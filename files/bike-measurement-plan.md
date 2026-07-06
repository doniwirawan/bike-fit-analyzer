# Bike Geometry Measurement — Future Feature Plan

> Deferred on 2026-07-06. This doc captures the plan so it can be picked up later.
> Nothing here is built yet.

## Goal
Output **real-world bike numbers** from a side-on clip/photo:
- **Saddle height** (bottom bracket → top of saddle, mm)
- **Reach & stack** (BB → head-tube top: horizontal reach, vertical stack, mm)
- **Seat & head tube angles** (degrees)
- **Wheelbase** (axle-to-axle, mm) + **rider leg/torso length** (mm)

## Current status (what exists today)
The app measures the **rider** only (MediaPipe Pose in `web/index.html`; YOLO11-pose in `files/analyze_bikefit.py`) and *infers* fit from body joint angles. **Nothing detects the bicycle itself** — even the "reach/saddle" marks are drawn from hip/shoulder/knee, not from the frame.

## Chosen approach
**Full-auto trained bike-keypoint model** (user decision). Needs two pieces:
1. **Bike keypoints** — a custom-trained keypoint model (no strong off-the-shelf one exists).
2. **Scale reference** — to convert pixels → mm.

---

## 1. Keypoint skeleton to label (8–9 points)
| # | Keypoint | Used for |
|---|----------|----------|
| 1 | rear axle | wheelbase, scale |
| 2 | front axle | wheelbase, scale |
| 3 | bottom bracket (crank centre) | saddle height, reach, stack, seat angle |
| 4 | seat-tube top (saddle clamp) | seat tube angle |
| 5 | head-tube top | reach, stack, head angle |
| 6 | head-tube bottom / fork crown | head tube angle |
| 7 | saddle tip/top | saddle height |
| 8 | handlebar / hoods | (cockpit, optional) |
| 9 | wheel rim point (top of one wheel) *(optional)* | wheel diameter → scale without Hough |

Each point also needs a **visibility flag** (visible / occluded).

## 2. Dataset requirements
- **Images:** side-on (drive-side), **riders on the bikes** (so the model handles legs occluding the frame). Vary bike type, colour, lighting, background, distance, phone lens.
- **Quantity:** ~300–500 to start (YOLO11-pose is COCO-pretrained, so transfer learning needs far less than scratch); 1–2k for robust. Expand where it fails (active learning).
- **Format:** COCO-keypoints JSON or YOLO-pose `.txt` (Roboflow exports both).

## 3. Where to get / build the data
- **Label your own (best match):** extract frames from real fit clips → label in **Roboflow Annotate**, **CVAT**, or **Label Studio**. Most reliable because BB/head-tube aren't in any generic dataset.
- **PASCAL3D+** (https://cvgl.stanford.edu/projects/pascal3d.html): "bicycle" category, real images + pose/keypoints. Keypoints are generic object-pose landmarks (remap needed) but images + CAD models are useful.
- **ObjectNet3D:** bicycle among 100 categories, 3D meshes + keypoints. Good for bulk + rendering.
- **Roboflow Universe** (https://universe.roboflow.com/search?q=keypoint+detection): community bike *detection* datasets (boxes) for cropping; keypoint ones rare.
- **Synthetic (Blender / BlenderProc):** bikes are rigid with exact geometry → render 3D models with programmatically-known keypoints. Cheap way to reach thousands of perfectly-labelled images; mix with real to close the domain gap.
- **Validation only (not training images):** 99spokes.com, geometrygeeks.bike — real reach/stack/angle numbers to sanity-check mm outputs.

## 4. Training & deployment pipeline
1. **Label** the skeleton in Roboflow.
2. **Train** YOLO11-pose (COCO-pretrained) via `ultralytics`; evaluate; iterate.
3. **Export** to ONNX → run in-browser via **ONNX Runtime Web** (or TF.js), or server-side.
4. **Integrate** with the existing app (see below).

## 5. Measurement math (once keypoints + scale exist)
`scale_mm_per_px = wheel_diameter_mm / wheel_diameter_px`
(wheel diameter: user picks size — 700c ≈ 668 mm outer w/ 25 mm tyre, 622 mm bead; 650b; 26"; etc. Get `wheel_diameter_px` from a Hough circle on a wheel, or from a labelled rim point.)

- **Wheelbase** = dist(rear_axle, front_axle) × scale
- **Saddle height** = dist(BB, saddle_top) × scale
- **Reach** = |head_tube_top.x − BB.x| × scale
- **Stack** = |head_tube_top.y − BB.y| × scale
- **Seat tube angle** = angle of (BB → seat_tube_top) from horizontal
- **Head tube angle** = angle of (head_tube_top → head_tube_bottom) from horizontal
- **Rider leg length** = dist(hip, ankle at full extension) × scale (from MediaPipe + scale)
- **Rider torso** = dist(hip, shoulder) × scale

## 6. Mobile / performance notes
- Running a 2nd model on top of MediaPipe adds download + compute. **Run bike detection on ONE good frame** (highest-confidence pose frame), not every frame — cheap.
- Keep the model small (nano/small YOLO-pose) for ONNX Runtime Web on phones.
- Let the user confirm/nudge keypoints if auto-detection is off (assisted fallback).

## 7. Related future item — bike-type support (separate, shippable without the model)
Grading today is **road-only** (`ZONES` in `web/index.html` from `files/bikefit-research-ranges.md`, which specifies road position). Other disciplines want different targets:
- **TT/Tri:** much lower torso, forward hip
- **Gravel/MTB:** slightly more upright, varies
- **Commuter/City:** very upright (60°+ torso), high bars
- Saddle height (knee ~30–40° at BDC) is roughly universal → carries over.

Plan: add a **bike-type selector** (like the Side/Front/Rear view selector) that swaps `ZONES` + advice per type. Main work is sourcing sensible per-discipline ranges. Frontal metrics (knee tracking, pelvic rock) are largely type-independent.

## Sources
- PASCAL3D+ — https://cvgl.stanford.edu/projects/pascal3d.html
- Roboflow, Annotate Keypoints — https://docs.roboflow.com/annotate/annotate-keypoints
- Roboflow, Train a custom YOLO pose model — https://blog.roboflow.com/train-a-custom-yolov8-pose-estimation-model/
- Roboflow Universe keypoint search — https://universe.roboflow.com/search?q=keypoint+detection
- Bike geometry reference DBs — https://99spokes.com , https://geometrygeeks.bike
