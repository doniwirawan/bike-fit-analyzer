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

## Installable build (Windows)

```powershell
pwsh -File desktop\build.ps1
```

Leaves `dist\BikeFitAnalyzer\BikeFitAnalyzer.exe` — double-click it, no Python needed — and
`dist\BikeFitAnalyzer-windows.zip` to hand to someone else. Ship the whole folder; the exe
alone will not run.

**It is ~955MB installed, ~415MB zipped.** Torch is 490MB of that, OpenCV 110MB and the
YOLO11x pose model 113MB, and the accuracy this build exists for is exactly what those
three provide. Too large for git and for Vercel, so `dist/` is gitignored — attach the zip
to a GitHub Release.

To check a build without clicking through the window:

```powershell
.\dist\BikeFitAnalyzer\BikeFitAnalyzer.exe --selftest CLIP.mp4 > result.txt
```

It runs the whole pipeline and prints the angles. Redirect stdout — the app is built
windowed, so it has no console of its own. The numbers should match the browser build on
the same clip.

### If the size matters more than the last degree

The way out is dropping torch, not shaving the bundle. Exporting the model to ONNX and
running it under `onnxruntime` (~15MB) removes torch and ultralytics entirely and lands
around 200MB, at the cost of hand-writing the letterbox, NMS and keypoint decoding that
ultralytics currently does. Worth doing if this is ever distributed widely.

Two excludes that look free and are not: `torch.distributed` (imported unconditionally by
`torch.utils.data.dataloader`) and `matplotlib` (imported at module level by
`ultralytics.models.yolo.semantic.train`). Both produce a build that launches happily and
dies with `ModuleNotFoundError` the moment you analyse a clip.

## Run from source

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
| Views | side, front, rear (front/rear beta) | all three, same beta caveat |
| Webcam recording | yes | no — choose a file |
| Drag and drop | yes | no; a webview can't see a dropped file's path |

The frontal (front/rear) maths in `analyze_frontal` is a port of the browser's
`frontalMetrics()` / `finishFrontal()`, down to using the same `sorted[floor(n*q)]`
percentile so short clips can't disagree by an off-by-one. It carries the same beta
warning in the UI, for the same reason: 2D frontal readings have a precision floor of
several degrees.

**The frontal path is verified to run, not verified to be right.** There is no front or
rear footage in this repo to test against — running it on a side-on clip exercises every
line and returns a well-formed result, but the numbers from that are meaningless. First
real front-on clip you have, compare it against the browser build on the same file; they
should agree closely.

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
