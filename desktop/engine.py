"""
Side-view bike-fit analysis for the desktop app.

This is the same measurement pipeline as files/analyze_bikefit.py — the angle maths,
the grading zones and the stroke detection are imported from it rather than copied, so
the desktop app cannot drift away from the CLI. What differs is the output: nothing is
written to disk, no overlay video is rendered, and the result comes back as plain data
for the web UI to draw. That makes a run seconds rather than minutes.

The pose model is YOLO11x-pose, which is why the desktop numbers are steadier than the
browser's MediaPipe ones: it is a far larger model than anything sensible to ship to a
web page, and it runs here on your own CPU or GPU.
"""

import base64
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "files"))
import analyze_bikefit as core  # noqa: E402  (path must be set first)

MODEL_PATH = ROOT / "yolo11x-pose.pt"

# YOLO11x is accurate and slow. Every frame of a 30s clip is 900 inferences, which on a
# CPU is a coffee break; the stroke rate we need to resolve is a few Hz, so sampling to
# ~15 effective fps loses nothing and halves the wait. find_peaks is given the sampled
# rate, not the file's, so stroke separation stays correct.
TARGET_FPS = 15.0

# The frame handed back to the UI. Big enough to read the angle badges on a laptop
# screen, small enough that the base64 data URL stays a sane size.
MAX_FRAME_W = 1280

_model = None


def _load_model(progress):
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Pose model not found at {MODEL_PATH}")
        progress("model", 0)
        _model = YOLO(str(MODEL_PATH))
    return _model


def _device():
    try:
        import torch
        return 0 if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _frame_to_data_url(frame):
    h, w = frame.shape[:2]
    if w > MAX_FRAME_W:
        scale = MAX_FRAME_W / w
        frame = cv2.resize(frame, (MAX_FRAME_W, int(round(h * scale))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise RuntimeError("Could not encode the analyzed frame")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii"), frame.shape[1], frame.shape[0]


def analyze(video_path, progress=lambda stage, pct: None):
    """Measure a side-on pedaling clip.

    Returns the same shape the web UI already knows how to render: raw angles in R,
    the deepest-stroke pose in P (in the pixels of the returned frame), and that frame
    as a data URL. Grading is deliberately left to the UI, which owns the per-bike-type
    zones — this way there is one set of thresholds on screen, not two.
    """
    src = Path(video_path)
    if not src.exists():
        raise RuntimeError(f"Video not found: {src}")

    model = _load_model(progress)
    device = _device()

    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise RuntimeError("Could not open that video. Try MP4, MOV or WebM.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    stride = max(1, int(round(fps / TARGET_FPS)))
    eff_fps = fps / stride

    # ---- pass 1: pose, tracked ----
    # Picking the highest-confidence detection independently per frame is what the CLI does,
    # and on a clip with anyone else in shot it silently flips subject halfway through. The
    # ankle then teleports, the measured stroke amplitude inflates to most of the frame, and
    # the prominence threshold derived from it rejects every real stroke — the clip comes
    # back as "no pedal strokes" rather than as a wrong answer. Tracking gives each person a
    # stable id, and we commit to the one seen most across the whole clip.
    per_frame, source_frames = [], []      # {track_id: keypoints} for each sampled frame
    seen_conf = {}                         # track id -> summed detection confidence
    idx = 0
    expected = (total // stride) if total else 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % stride == 0:
            res = model.track(frame, persist=True, device=device, verbose=False)[0]
            found = {}
            if res.keypoints is not None and res.boxes is not None and len(res.boxes) > 0:
                data = res.keypoints.data.cpu().numpy()
                confs = res.boxes.conf.cpu().numpy()
                raw_ids = res.boxes.id
                ids_arr = (raw_ids.cpu().numpy().astype(int) if raw_ids is not None
                           else np.arange(len(confs)))     # tracker not running: fall back
                for slot, tid in enumerate(ids_arr):
                    if slot >= len(data):
                        continue
                    found[int(tid)] = data[slot]
                    seen_conf[int(tid)] = seen_conf.get(int(tid), 0.0) + float(confs[slot])
            per_frame.append(found)
            source_frames.append(idx)
            if expected and len(per_frame) % 5 == 0:
                progress("pose", min(99, int(100 * len(per_frame) / expected)))
        idx += 1
    cap.release()

    if len(per_frame) < 5:
        raise RuntimeError("Couldn't read enough of that video to measure anything.")
    if not seen_conf:
        raise RuntimeError("Couldn't find anyone in that video. Re-film with your whole body in frame.")

    subject = max(seen_conf, key=seen_conf.get)
    kps = [f.get(subject) for f in per_frame]

    # ---- near side: whichever half of the body the model is more confident about ----
    side_conf = {"left": 0.0, "right": 0.0}
    for kp in kps:
        if kp is None:
            continue
        for side, ids in core.SIDE.items():
            side_conf[side] += float(sum(kp[j][2] for j in ids.values()))
    near = "left" if side_conf["left"] >= side_conf["right"] else "right"
    far = "right" if near == "left" else "left"
    ids = core.SIDE[near]

    # A square-on clip hides the far leg; when both sides read almost equally well the
    # camera is off to one side, which stretches the reach angles. Same 0.55 threshold
    # the browser build uses, from the ratio of far-side to near-side confidence.
    off_axis = False
    if side_conf[near] > 0:
        off_axis = (side_conf[far] / side_conf[near]) > 0.55

    # ---- per-frame angles ----
    n = len(kps)
    ankle_y = np.full(n, np.nan)
    angles = {k: np.full(n, np.nan) for k in
              ["knee_flexion_bdc", "torso_from_horiz", "elbow_flexion", "shoulder_angle", "hip_angle"]}
    poses = [None] * n

    for i, kp in enumerate(kps):
        if kp is None:
            continue
        p = {name: kp[j] for name, j in ids.items()}
        poses[i] = p
        seen = lambda *names: all(p[nm][2] >= core.MIN_CONF for nm in names)  # noqa: E731
        xy = lambda nm: p[nm][:2]                                            # noqa: E731

        if seen("ankle"):
            ankle_y[i] = p["ankle"][1]
        if seen("hip", "knee", "ankle"):
            angles["knee_flexion_bdc"][i] = 180 - core.angle_at(xy("hip"), xy("knee"), xy("ankle"))
        if seen("hip", "shoulder"):
            angles["torso_from_horiz"][i] = core.torso_from_horizontal(xy("hip"), xy("shoulder"))
        if seen("shoulder", "elbow", "wrist"):
            angles["elbow_flexion"][i] = 180 - core.angle_at(xy("shoulder"), xy("elbow"), xy("wrist"))
        if seen("hip", "shoulder", "elbow"):
            angles["shoulder_angle"][i] = core.angle_at(xy("hip"), xy("shoulder"), xy("elbow"))
        if seen("shoulder", "hip", "knee"):
            angles["hip_angle"][i] = core.angle_at(xy("shoulder"), xy("hip"), xy("knee"))

    if (~np.isnan(ankle_y)).sum() < 5:
        raise RuntimeError("Couldn't track your ankle clearly. Re-film side-on, well lit, whole body in frame.")

    # ---- bottom and top of each pedal stroke ----
    amp = float(np.nanpercentile(ankle_y, 95) - np.nanpercentile(ankle_y, 5))
    min_dist = max(3, int(eff_fps * 0.35))
    prominence = max(2.0, 0.25 * amp)
    bdc = core.find_peaks(ankle_y, min_dist, prominence)
    tdc = core.find_peaks(-ankle_y, min_dist, prominence)
    if not bdc:
        raise RuntimeError("No clear pedal strokes found. Make sure you're actually pedaling, filmed side-on.")

    def median_at(metric, frames):
        vals = [angles[metric][f] for f in frames if not np.isnan(angles[metric][f])]
        return float(np.median(vals)) if vals else None

    results = {
        "knee_flexion_bdc": median_at("knee_flexion_bdc", bdc),
        "torso_from_horiz": median_at("torso_from_horiz", bdc),
        "elbow_flexion": median_at("elbow_flexion", bdc),
        "shoulder_angle": median_at("shoulder_angle", bdc),
    }
    hip_top = median_at("hip_angle", tdc) if tdc else None

    # ---- the frame the numbers came from: the deepest bottom-dead-centre ----
    deepest = max(bdc, key=lambda f: ankle_y[f])
    cap = cv2.VideoCapture(str(src))
    cap.set(cv2.CAP_PROP_POS_FRAMES, source_frames[deepest])
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Couldn't re-read the measured frame from the video.")

    data_url, out_w, out_h = _frame_to_data_url(frame)
    scale = out_w / frame.shape[1] if frame.shape[1] else 1.0
    pose = poses[deepest]
    P = {name: {"x": float(pose[name][0]) * scale,
                "y": float(pose[name][1]) * scale,
                "v": float(pose[name][2])}
         for name in ids}

    progress("pose", 100)
    return {
        "R": results,
        "hipTop": hip_top,
        "strokes": len(bdc),
        "offAxis": bool(off_axis),
        "P": P,
        "pw": out_w,
        "ph": out_h,
        "frame": data_url,
        "engine": f"YOLO11x-pose ({'GPU' if device == 0 else 'CPU'})",
    }
