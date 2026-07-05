"""
analyze_bikefit.py - Grade a road bike fit from a side-on pedaling video.

Runs YOLO11x-pose on each frame, finds bottom-dead-center (BDC) of the pedal
stroke during real pedaling, measures joint angles there, grades them against
research-backed dynamic road ranges, draws a colored skeleton on the whole clip,
and writes a plain-English report.

Ranges come from files/bikefit-research-ranges.md (Holmes method + a
dynamic-vs-static validity study). See README.md for sources.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from ultralytics import YOLO

# COCO-17 keypoint indices, split by body side.
SIDE = {
    "left":  dict(shoulder=5, elbow=7, wrist=9,  hip=11, knee=13, ankle=15),
    "right": dict(shoulder=6, elbow=8, wrist=10, hip=12, knee=14, ankle=16),
}

# Grading zones: (green_lo, green_hi, red_lo, red_hi).
# green inside [green_lo, green_hi]; red below red_lo or above red_hi; amber between.
# Grounded in the dynamic road-fit ranges in bikefit-research-ranges.md.
ZONES = {
    "knee_flexion_bdc":  (30, 40, 28, 42),   # Holmes; over 42 saddle low, under 28 saddle high
    "torso_from_horiz":  (40, 50, 34, 56),
    "elbow_flexion":     (15, 30,  8, 45),   # near 0 = locked out
    "shoulder_angle":    (80, 95, 70, 105),  # much lower = closed/scrunched cockpit
}

# BGR colors for OpenCV drawing.
COLOR = {"GREEN": (0, 200, 0), "AMBER": (0, 165, 255), "RED": (0, 0, 255), "GRAY": (150, 150, 150)}
MIN_CONF = 0.3  # ignore keypoints below this confidence


def grade(metric, value):
    """Return GREEN / AMBER / RED for a measured angle."""
    if value is None or np.isnan(value):
        return "GRAY"
    g_lo, g_hi, r_lo, r_hi = ZONES[metric]
    if g_lo <= value <= g_hi:
        return "GREEN"
    if value < r_lo or value > r_hi:
        return "RED"
    return "AMBER"


def worse(*grades):
    """Worst (most severe) grade among the given grades."""
    order = {"GRAY": 0, "GREEN": 1, "AMBER": 2, "RED": 3}
    return max(grades, key=lambda g: order[g])


def angle_at(a, b, c):
    """Interior angle in degrees at vertex b, between points a and c."""
    a, b, c = np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)
    v1, v2 = a - b, c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return np.nan
    cosang = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))


def torso_from_horizontal(hip, shoulder):
    """Angle of the torso (hip->shoulder) from horizontal, 0=flat .. 90=upright."""
    dx = shoulder[0] - hip[0]
    dy = shoulder[1] - hip[1]
    if dx == 0 and dy == 0:
        return np.nan
    return float(np.degrees(np.arctan2(abs(dy), abs(dx))))


def find_peaks(y, min_dist, prominence):
    """Simple 1-D local-maxima finder. y is a float array (may contain nan).
    Returns indices of peaks separated by >= min_dist with the given prominence."""
    n = len(y)
    cand = []
    for i in range(n):
        if np.isnan(y[i]):
            continue
        lo, hi = max(0, i - min_dist), min(n, i + min_dist + 1)
        window = y[lo:hi]
        if np.isnan(window).all():
            continue
        if y[i] < np.nanmax(window):
            continue
        # prominence: rise above the lower of the two neighboring valleys
        left = y[lo:i]
        right = y[i + 1:hi]
        base_l = np.nanmin(left) if left.size and not np.isnan(left).all() else y[i]
        base_r = np.nanmin(right) if right.size and not np.isnan(right).all() else y[i]
        if y[i] - max(base_l, base_r) >= prominence:
            cand.append(i)
    # enforce min separation, keeping the higher peak
    peaks = []
    for i in cand:
        if peaks and i - peaks[-1] < min_dist:
            if y[i] > y[peaks[-1]]:
                peaks[-1] = i
        else:
            peaks.append(i)
    return peaks


def analyze(args):
    if not os.path.exists(args.input):
        sys.exit(f"Input video not found: {args.input}")
    os.makedirs(args.out, exist_ok=True)
    stills_dir = os.path.join(args.out, "stills")
    os.makedirs(stills_dir, exist_ok=True)

    device = 0 if _cuda_available() else "cpu"
    print(f"Loading {args.model} on device={device} ...")
    model = YOLO(args.model)

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        sys.exit(f"Could not open video: {args.input}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    start_f = int(args.start * fps) if args.start else 0
    end_f = int(args.end * fps) if args.end else total

    # ---- Pass 1: run pose on every frame, cache keypoints ----
    print(f"Running pose on frames {start_f}..{end_f} ({fps:.1f} fps) ...")
    frames_kp = []   # per frame: (17,3) array of x,y,conf for best person, or None
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx < start_f:
            idx += 1
            continue
        if idx >= end_f:
            break
        res = model.predict(frame, device=device, verbose=False)[0]
        kp = None
        if res.keypoints is not None and res.boxes is not None and len(res.boxes) > 0:
            confs = res.boxes.conf.cpu().numpy()
            best = int(np.argmax(confs))
            data = res.keypoints.data.cpu().numpy()  # (N,17,3)
            if best < len(data):
                kp = data[best]
        frames_kp.append(kp)
        idx += 1
        if len(frames_kp) % 25 == 0:
            print(f"  {len(frames_kp)} frames processed")
    cap.release()

    if not frames_kp:
        sys.exit("No frames read. Check --start/--end.")

    # ---- Decide near (camera) side by total keypoint confidence ----
    side_conf = {"left": 0.0, "right": 0.0}
    for kp in frames_kp:
        if kp is None:
            continue
        for side, ids in SIDE.items():
            side_conf[side] += sum(kp[j][2] for j in ids.values())
    near = "left" if side_conf["left"] >= side_conf["right"] else "right"
    ids = SIDE[near]
    print(f"Near (camera) side: {near}")

    # ---- Per-frame angles + ankle vertical position ----
    N = len(frames_kp)
    ankle_y = np.full(N, np.nan)
    angles = {k: np.full(N, np.nan) for k in
              ["knee_flexion_bdc", "torso_from_horiz", "elbow_flexion",
               "shoulder_angle", "hip_angle"]}
    pts_cache = [None] * N

    for i, kp in enumerate(frames_kp):
        if kp is None:
            continue
        p = {name: kp[j] for name, j in ids.items()}  # each is (x,y,conf)
        pts_cache[i] = p

        def ok(*names):
            return all(p[nm][2] >= MIN_CONF for nm in names)

        def xy(nm):
            return p[nm][:2]

        if ok("ankle"):
            ankle_y[i] = p["ankle"][1]
        if ok("hip", "knee", "ankle"):
            interior = angle_at(xy("hip"), xy("knee"), xy("ankle"))
            angles["knee_flexion_bdc"][i] = 180 - interior
        if ok("hip", "shoulder"):
            angles["torso_from_horiz"][i] = torso_from_horizontal(xy("hip"), xy("shoulder"))
        if ok("shoulder", "elbow", "wrist"):
            interior = angle_at(xy("shoulder"), xy("elbow"), xy("wrist"))
            angles["elbow_flexion"][i] = 180 - interior
        if ok("hip", "shoulder", "elbow"):
            angles["shoulder_angle"][i] = angle_at(xy("hip"), xy("shoulder"), xy("elbow"))
        if ok("shoulder", "hip", "knee"):
            angles["hip_angle"][i] = angle_at(xy("shoulder"), xy("hip"), xy("knee"))

    # ---- Find BDC (lowest ankle = max y) during real pedaling ----
    valid = ~np.isnan(ankle_y)
    if valid.sum() < 5:
        sys.exit("Could not track the ankle in enough frames. Check the clip framing/lighting.")
    amp = np.nanpercentile(ankle_y, 95) - np.nanpercentile(ankle_y, 5)
    if amp < 0.03 * h:
        print("WARNING: very little leg movement detected - is this really a pedaling clip?")
    min_dist = max(3, int(fps * 0.35))          # up to ~170 rpm
    prominence = max(2.0, 0.25 * amp)
    bdc_frames = find_peaks(ankle_y, min_dist, prominence)          # bottom of stroke
    tdc_frames = find_peaks(-ankle_y, min_dist, prominence)          # top of stroke
    print(f"Detected {len(bdc_frames)} pedal strokes (BDC frames).")

    if not bdc_frames:
        sys.exit("No clear pedal strokes found. Try trimming to the pedaling window with --start/--end.")

    # ---- Median angles across strokes ----
    def median_at(metric, frames):
        vals = [angles[metric][f] for f in frames if not np.isnan(angles[metric][f])]
        return float(np.median(vals)) if vals else None

    results = {
        "knee_flexion_bdc": median_at("knee_flexion_bdc", bdc_frames),
        "torso_from_horiz": median_at("torso_from_horiz", bdc_frames),
        "elbow_flexion":    median_at("elbow_flexion", bdc_frames),
        "shoulder_angle":   median_at("shoulder_angle", bdc_frames),
        "hip_angle_top":    median_at("hip_angle", tdc_frames) if tdc_frames else None,
    }
    grades = {m: grade(m, results[m]) for m in ZONES}

    # ---- Save the BDC still (deepest stroke) ----
    deepest = max(bdc_frames, key=lambda f: ankle_y[f])
    _save_still(args.input, start_f + deepest, os.path.join(stills_dir, "bdc.jpg"),
                pts_cache[deepest], ids, grades)

    # ---- Draw skeleton on whole clip ----
    overlay_raw = os.path.join(args.out, "overlay_raw.mp4")
    _draw_overlay(args.input, start_f, end_f, overlay_raw, pts_cache, ids, grades, w, h, fps)

    # ---- Re-encode to H.264 so it plays anywhere ----
    overlay_h264 = os.path.join(args.out, "overlay_h264.mp4")
    _reencode_h264(overlay_raw, overlay_h264)

    # ---- Reports ----
    _write_reports(args.out, results, grades)
    print(f"\nDone. See {args.out}/report.md and {overlay_h264}")


def _cuda_available():
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def _color_for(grades, part):
    if part == "leg":
        return COLOR[grades["knee_flexion_bdc"]]
    if part == "torso":
        return COLOR[grades["torso_from_horiz"]]
    if part == "arm":
        return COLOR[worse(grades["shoulder_angle"], grades["elbow_flexion"])]
    return COLOR["GRAY"]


def _draw_skeleton(frame, p, ids, grades):
    """Draw the near-side skeleton on a frame using cached points p (name->x,y,conf)."""
    def pt(nm):
        return (int(p[nm][0]), int(p[nm][1]))

    def good(nm):
        return p[nm][2] >= MIN_CONF

    segs = [
        ("hip", "knee", "leg"), ("knee", "ankle", "leg"),
        ("shoulder", "hip", "torso"),
        ("shoulder", "elbow", "arm"), ("elbow", "wrist", "arm"),
    ]
    for a, b, part in segs:
        if good(a) and good(b):
            cv2.line(frame, pt(a), pt(b), _color_for(grades, part), 3)
    for nm in ids:
        if good(nm):
            cv2.circle(frame, pt(nm), 5, (255, 255, 255), -1)


def _save_still(input_path, frame_no, out_path, p, ids, grades):
    cap = cv2.VideoCapture(input_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    cap.release()
    if ret and p is not None:
        _draw_skeleton(frame, p, ids, grades)
        cv2.imwrite(out_path, frame)


def _draw_overlay(input_path, start_f, end_f, out_path, pts_cache, ids, grades, w, h, fps):
    cap = cv2.VideoCapture(input_path)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    idx = 0
    ci = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx < start_f:
            idx += 1
            continue
        if idx >= end_f:
            break
        p = pts_cache[ci] if ci < len(pts_cache) else None
        if p is not None:
            _draw_skeleton(frame, p, ids, grades)
        writer.write(frame)
        idx += 1
        ci += 1
    cap.release()
    writer.release()


def _reencode_h264(src, dst):
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found - leaving raw overlay, may not play on all devices.")
        shutil.copy(src, dst)
        return
    subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", dst],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.remove(src)


def _fix_text(metric, value, g):
    if g == "GREEN" or value is None:
        return None
    if metric == "knee_flexion_bdc":
        if value > 40:
            return f"Knee {value:.0f}deg at bottom (target 30-40) -> saddle TOO LOW. Raise saddle ~{(value-35)*2:.0f}mm."
        return f"Knee {value:.0f}deg at bottom (target 30-40) -> saddle TOO HIGH. Lower saddle ~{(35-value)*2:.0f}mm."
    if metric == "torso_from_horiz":
        return f"Torso {value:.0f}deg (target 40-50) -> {'too upright' if value > 50 else 'very aggressive'}; adjust reach/stem."
    if metric == "elbow_flexion":
        return f"Elbow {value:.0f}deg (target 15-30) -> {'locked out, soften/shorten reach' if value < 15 else 'very bent, reach may be short'}."
    if metric == "shoulder_angle":
        return f"Shoulder {value:.0f}deg (target 80-95) -> {'closed/scrunched cockpit, weight on hands' if value < 80 else 'very open reach'}."
    return None


def _write_reports(out_dir, results, grades):
    overall = worse(*grades.values())
    verdict = {"GREEN": "GREEN - dialed", "AMBER": "AMBER - minor tweaks",
               "RED": "RED - fix needed", "GRAY": "INCOMPLETE"}[overall]

    lines = ["# Bike fit report", f"- Overall: {verdict}", "", "## Angles (deg) vs target"]
    labels = {
        "knee_flexion_bdc": "knee_flexion_bdc (target 30-40)",
        "torso_from_horiz": "torso_from_horiz (target 40-50)",
        "elbow_flexion":    "elbow_flexion (target 15-30)",
        "shoulder_angle":   "shoulder_angle (target 80-95)",
    }
    for m in ZONES:
        v = results[m]
        vs = f"{v:.0f}" if v is not None else "n/a"
        lines.append(f"- {labels[m]}: {vs} -> {grades[m]}")
    if results.get("hip_angle_top") is not None:
        lines.append(f"- hip_angle_top: {results['hip_angle_top']:.0f} (report only, ~85-110)")

    fixes = [t for m in ZONES for t in [_fix_text(m, results[m], grades[m])] if t]
    lines += ["", "## Do this"]
    lines += [f"- {t}" for t in fixes] if fixes else ["- Everything in range. Nice fit."]

    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump({"overall": overall, "angles": results, "grades": grades, "fixes": fixes},
                  f, indent=2)
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description="Grade a road bike fit from a side-on pedaling video.")
    ap.add_argument("--input", required=True, help="path to your side-on video")
    ap.add_argument("--out", default="out_fit", help="output folder")
    ap.add_argument("--start", type=float, default=None, help="start second (trim)")
    ap.add_argument("--end", type=float, default=None, help="end second (trim)")
    ap.add_argument("--model", default="yolo11x-pose.pt", help="pose model")
    analyze(ap.parse_args())


if __name__ == "__main__":
    main()
