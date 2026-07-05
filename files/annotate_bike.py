"""
annotate_bike.py - mark up a side-on frame to judge if the bike is "too big / too long".
Draws the reach triangle (hip-shoulder-hand), the knee-over-pedal (KOPS) lines,
a saddle-height/leg-extension cue, and a plain verdict. Saves an annotated image.
"""
import argparse
import cv2
import numpy as np
from ultralytics import YOLO

SIDE = {
    "left":  dict(shoulder=5, elbow=7, wrist=9,  hip=11, knee=13, ankle=15),
    "right": dict(shoulder=6, elbow=8, wrist=10, hip=12, knee=14, ankle=16),
}
GREEN, AMBER, RED, WHITE, CYAN = (0,200,0), (0,165,255), (0,0,255), (255,255,255), (255,230,0)


def angle_at(a, b, c):
    a, b, c = map(lambda p: np.asarray(p, float), (a, b, c))
    v1, v2 = a - b, c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return np.nan
    return float(np.degrees(np.arccos(np.clip(np.dot(v1, v2)/(n1*n2), -1, 1))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="bike_marked.jpg")
    ap.add_argument("--model", default="yolo11x-pose.pt")
    args = ap.parse_args()

    model = YOLO(args.model)
    cap = cv2.VideoCapture(args.input)

    # pick the highest-confidence frame in the clip for clean marks
    best_frame, best_kp, best_score = None, None, -1
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % 3 == 0:  # sample every 3rd frame for speed
            r = model.predict(frame, device="cpu", verbose=False)[0]
            if r.boxes is not None and len(r.boxes) > 0:
                b = int(np.argmax(r.boxes.conf.cpu().numpy()))
                kp = r.keypoints.data.cpu().numpy()[b]
                score = float(kp[:, 2].sum())
                if score > best_score:
                    best_score, best_frame, best_kp = score, frame.copy(), kp
        idx += 1
    cap.release()

    if best_frame is None:
        raise SystemExit("No person detected.")

    # near side = higher total confidence
    conf = {s: sum(best_kp[j][2] for j in ids.values()) for s, ids in SIDE.items()}
    ids = SIDE["left" if conf["left"] >= conf["right"] else "right"]
    P = {name: best_kp[j][:2].astype(int) for name, j in ids.items()}

    sh, el, wr, hp, kn, an = (P["shoulder"], P["elbow"], P["wrist"],
                              P["hip"], P["knee"], P["ankle"])
    img = best_frame
    H, W = img.shape[:2]

    shoulder_ang = angle_at(hp, sh, el)      # reach indicator
    knee_flex = 180 - angle_at(hp, kn, an)   # saddle height indicator
    torso = float(np.degrees(np.arctan2(abs(sh[1]-hp[1]), abs(sh[0]-hp[0]))))

    def line(a, b, c, t=3): cv2.line(img, tuple(a), tuple(b), c, t)
    def dot(a, c=WHITE, r=6): cv2.circle(img, tuple(a), r, c, -1)

    # --- Reach triangle: hip -> shoulder -> hand (bars) ---
    line(hp, sh, CYAN); line(sh, wr, CYAN)
    line(hp, wr, CYAN, 1)
    for p in (hp, sh, wr): dot(p, CYAN)
    reach_grade = GREEN if shoulder_ang >= 80 else (AMBER if shoulder_ang >= 70 else RED)
    cv2.putText(img, f"shoulder {shoulder_ang:.0f}deg", (sh[0]+8, sh[1]-8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, reach_grade, 2)

    # --- KOPS: vertical lines at knee and at pedal(ankle) ---
    line((kn[0], kn[1]-40), (kn[0], an[1]+30), AMBER, 2)
    line((an[0], kn[1]-40), (an[0], an[1]+30), WHITE, 1)
    dx = kn[0] - an[0]
    cv2.putText(img, f"knee vs pedal: {dx:+d}px", (kn[0]+8, (kn[1]+an[1])//2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, AMBER, 2)

    # --- Leg / saddle-height cue: hip-knee-ankle ---
    kg = GREEN if 30 <= knee_flex <= 40 else (AMBER if 26 <= knee_flex <= 44 else RED)
    line(hp, kn, kg); line(kn, an, kg)
    for p in (kn, an): dot(p, kg)
    cv2.putText(img, f"knee bend {knee_flex:.0f}deg", (kn[0]+8, kn[1]+22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, kg, 2)

    # --- Verdict box ---
    if shoulder_ang < 70:
        reach_txt = "REACH: long/stretched - bike may be too long"
    elif shoulder_ang > 100:
        reach_txt = "REACH: very open - possibly too long"
    else:
        reach_txt = "REACH: OK - you are NOT overstretched"
    sad_txt = ("SADDLE: a bit HIGH (lower a little)" if knee_flex < 30
               else "SADDLE: a bit LOW (raise a little)" if knee_flex > 40
               else "SADDLE: good height")
    lines = ["BIKE FIT MARKS (side-on)", reach_txt, sad_txt,
             "Note: sandals + not a locked trainer = rough read"]
    y0 = 30
    cv2.rectangle(img, (10, 10), (min(W-10, 640), 20 + 26*len(lines)), (0,0,0), -1)
    for i, t in enumerate(lines):
        cv2.putText(img, t, (20, y0 + 26*i), cv2.FONT_HERSHEY_SIMPLEX,
                    0.62, WHITE if i else CYAN, 2)

    cv2.imwrite(args.out, img)
    print(f"saved {args.out}  | shoulder={shoulder_ang:.0f} knee_flex={knee_flex:.0f} torso={torso:.0f}")


if __name__ == "__main__":
    main()
