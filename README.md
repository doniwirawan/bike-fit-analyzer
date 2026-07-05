# 🚴 Bike Fit Analyzer

### ▶️ Live demo (runs in your browser): **https://bikefit-analyzer.vercel.app**

No install, no upload — drop a side-on pedaling clip and it grades your fit
on-device. (The in-browser app lives in [`web/`](web/); the more accurate
desktop pipeline is below.)

---

Grade your own **road bike fit** from a side-on phone video, using AI pose
estimation. It tracks your body joints, finds the bottom of your pedal stroke,
measures the fit angles a professional fitter looks at, grades them against
published sport-science ranges, and draws a colored skeleton on your clip:

- 🟢 **green** = dialed &nbsp; 🟠 **orange** = borderline &nbsp; 🔴 **red** = fix it

Then it tells you the exact change, e.g. *"knee 45° at the bottom → saddle too
low, raise ~10 mm."*

> Built on [Ultralytics YOLO11](https://github.com/ultralytics/ultralytics)
> pose (`yolo11x-pose`), OpenCV, PyTorch and ffmpeg. **See the
> [License](#-license) note before using this in any product** — YOLO11 is
> AGPL-3.0.

---

## What you get

```
out_fit/
  overlay_h264.mp4     # your whole clip with the colored skeleton (plays anywhere)
  stills/bdc.jpg       # the bottom-of-stroke frame with angles graded
  report.md            # plain-English verdict + the exact fix
  report.json          # the same, structured
```

Example `report.md`:

```
# Bike fit report
- Overall: RED - fix needed

## Angles (deg) vs target
- knee_flexion_bdc (target 30-40): 45 -> RED
- torso_from_horiz (target 40-50): 44 -> GREEN
- elbow_flexion (target 15-30): 22 -> GREEN
- shoulder_angle (target 80-95): 88 -> GREEN

## Do this
- Knee 45deg at bottom (target 30-40) -> saddle TOO LOW. Raise saddle ~20mm.
```

---

## Film it right (this is 90% of the result)

- **Side-on.** Camera directly to the side, lens pointed straight at you, square
  to the bike. Not in front, behind, or at an angle.
- **Hip height.** Rest the phone at hip/crank height on something stable.
- **Nothing blocking your near leg and arm.** Move bottles, fans, the dog.
- **Pedal steadily for 20–30 s** at an easy, normal cadence (a trainer is ideal).
- **Good light**, less motion blur = a more accurate read.
- **Hands where you normally ride** (hoods for most people), the whole clip.
- **Road position.** These ranges are for road/trainer setups, not Tri/TT.
- Trim to just the pedaling part, or use `--start`/`--end` (see below).

---

## Requirements

- **Python 3.11+** (tested on 3.13)
- **ffmpeg** on your PATH — `winget install ffmpeg` (Windows) / `brew install ffmpeg` (Mac)
- ~1.5 GB free disk (PyTorch + the pose model)
- A GPU is optional. **CPU works fine** for a short clip, just slower.

## Setup

```bash
# 1. Create an isolated environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 2. Install PyTorch
#    NVIDIA GPU:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
#    CPU only:
pip install torch torchvision

# 3. Install the rest
pip install -r files/requirements.txt
```

The `yolo11x-pose.pt` model (~118 MB) auto-downloads on first run. If your
connection is slow, download it once by hand from the
[Ultralytics assets release](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x-pose.pt)
and drop it in the project folder.

---

## Usage

### Option A — command line

```bash
python files/analyze_bikefit.py --input my-ride.mp4 --out out_fit
```

Trim to just the pedaling window (seconds):

```bash
python files/analyze_bikefit.py --input my-ride.mp4 --out out_fit --start 5 --end 35
```

| Flag | Meaning | Default |
|---|---|---|
| `--input` | your side-on video (required) | — |
| `--out` | output folder | `out_fit` |
| `--start` / `--end` | trim window in seconds | whole clip |
| `--model` | pose model | `yolo11x-pose.pt` |

On a slow CPU, `--model yolo11n-pose.pt` trades accuracy for speed.

### Option B — drag-and-drop upload page

A tiny local, dependency-free upload page (no data leaves your computer):

```bash
python upload_server.py
```

Open **http://localhost:8000**, drop your clip in, and it's saved to `uploads/`.
Then run Option A on that file.

---

## What the colors mean

| Angle (side-on) | Green zone | Red means |
|---|---|---|
| Knee at the bottom | 30–40° | over 42 saddle too low (raise); under 28 too high (lower) |
| Torso from horizontal | 40–50° | over 56 too upright; under 34 very aggressive |
| Elbow bend | 15–30° | near 0 locked out (soften / shorten reach) |
| Shoulder (torso to arm) | ~80–95° | closed/scrunched cockpit, weight on the hands |
| Hip at the top | ~85–110° | flexibility / reach (report only) |

Full sources are in [`files/bikefit-research-ranges.md`](files/bikefit-research-ranges.md).

## How it works

1. Runs YOLO11x-pose on each frame → 17 COCO body keypoints per person.
2. Picks the highest-confidence person and your **near (camera-side)** joints.
3. Tracks the ankle's vertical position to find **bottom-dead-center (BDC)**
   across several real pedal strokes, taking the **median** so one blurry frame
   can't skew it.
4. Measures joint angles at BDC (pure geometry) and grades each with a ~2.5°
   edge tolerance.
5. Draws the skeleton (arm colored by the worse of shoulder/elbow), saves the
   BDC still, and re-encodes the overlay to H.264 so it plays anywhere.

---

## Troubleshooting

- **`ffmpeg not found`** → install it and reopen your terminal.
- **"very little leg movement detected"** → the clip isn't steady pedaling; use a
  trainer or a longer clip and trim with `--start/--end`.
- **"No clear pedal strokes found"** → trim to the pedaling window.
- **Slow first run** → the model downloads once (~118 MB); later runs are faster.

## Notes & limits

- A 2D side-view gives you **population ranges and a great starting point, not a
  3D pro fit**. For pain, numbness, or big changes, see a real fitter.
- **Not medical advice.** Change one thing at a time and stop if it hurts.
- Change one thing per session (saddle **or** reach), then re-film.

## 📄 License

The analysis code in this repo is provided as-is for personal use. **Ultralytics
YOLO11 is licensed AGPL-3.0** — free to run yourself, but its network-copyleft
terms apply if you ship it inside a product or a hosted service. For commercial
use, obtain an [Ultralytics Enterprise license](https://www.ultralytics.com/license)
or swap in a differently-licensed pose model.
