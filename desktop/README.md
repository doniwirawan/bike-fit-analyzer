# Bike Fit Analyzer — desktop

The website's interface, measured by a much larger pose model.

The browser version runs MediaPipe Pose, which has to be small enough to download to a
web page. This one runs **YOLO11x-pose** on your own machine, so the joint positions are
steadier — particularly the far-side leg and the wrist, which are where the browser build
gets noisy on a busy background.

It is not a second app. `desktop/bikefit.py` opens **`web/app.html` itself** in a native
window; the page notices `window.pywebview` and routes its file picker and its analysis
through Python instead of MediaPipe. Every report card, the saved-results list, the export
buttons and both languages are whatever is currently live on the site. Change the web UI
and the desktop app changes with it.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements-desktop.txt
```

`yolo11x-pose.pt` must be in the repo root — it already is.

For an NVIDIA GPU, install the CUDA build of torch first (see pytorch.org). A 30-second
clip is seconds on a GPU and a few minutes on a CPU.

## Run

```bash
python desktop/bikefit.py                 # open the window, then choose a clip
python desktop/bikefit.py path\to\clip.mp4  # analyze that clip on startup
```

## What differs from the browser build

| | Browser | Desktop |
|---|---|---|
| Pose model | MediaPipe Pose (full) | YOLO11x-pose |
| Runs on | anyone's phone or laptop | this machine, GPU if there is one |
| Views | side, front, rear (front/rear beta) | side only |
| Webcam recording | yes | no — choose a file |
| Drag and drop | yes | no; a webview can't see a dropped file's path |

Front and rear are hidden in the desktop window rather than quietly falling back to the
browser engine, because there is no Python implementation of the frontal metrics yet.

## How the two stay honest

The angle maths, the grading zones and the stroke detection are imported from
`files/analyze_bikefit.py` — the same module the MCP server and the CLI use — rather than
copied. `desktop/engine.py` only changes the *output*: no report files, no overlay video
render, just the numbers and the measured frame handed back to the page. Grading happens
in the UI, using the UI's own per-bike-type zones, so there is exactly one set of
thresholds on screen.

Sampling: YOLO11x is slow enough that measuring all 900 frames of a 30s clip is a waste,
so frames are sampled to ~15 fps. Pedal strokes are a few Hz, and `find_peaks` is given
the sampled rate, so stroke detection is unaffected.
