# @doniwirawan/bikefit-angles

Bike fit joint angles from 2D pose landmarks. This is the measuring core of [Bike Fit Analyzer](https://bikefit.doniwirawan.xyz), the same code the site runs, published as a package.

Give it points from any pose model (MediaPipe, BlazePose, MoveNet, YOLO-pose, your own) and it returns:

- **Five angles per frame:**
  - knee flexion
  - torso from horizontal
  - elbow flexion
  - shoulder angle
  - hip angle
- **Pedal-stroke detection:** finds the bottom and top of each stroke from the ankle's path.
- **A graded result:** the median angle at the bottom of the stroke, graded green / amber / red against targets for six bike types.
- **Front and rear view readings (beta):** knee tracking (frontal-plane projection angle), pelvic rock, and left/right symmetry.

There are no dependencies. It runs in the browser or in Node 18+.

```sh
npm i @doniwirawan/bikefit-angles
```

## Quick start

```js
import { sideFrameAngles, analyzeSide } from '@doniwirawan/bikefit-angles';

// One side's joints, in any consistent unit. visibility (0-1) is optional.
const angles = sideFrameAngles({
  shoulder: { x: 512, y: 210 }, elbow: { x: 590, y: 300 }, wrist: { x: 660, y: 330 },
  hip: { x: 400, y: 330 }, knee: { x: 470, y: 470 }, ankle: { x: 455, y: 600 },
});
// -> { knee_flexion_bdc, torso_from_horiz, elbow_flexion, shoulder_angle, hip_angle }

// A whole clip: one entry per frame.
const result = analyzeSide(frames, { bikeType: 'road_endurance' });
// frames: [{ t: seconds, ankleY: ankle y in image coordinates, angles: sideFrameAngles(...) }, ...]
// -> { angles, grades, verdict, strokes, hipTop, bdcFrames, tdcFrames }, or null if no pedal strokes
```

## With MediaPipe Pose

```js
import { PoseLandmarker } from '@mediapipe/tasks-vision';
import { sidePoints, sideConfidence, sideFrameAngles, analyzeSide } from '@doniwirawan/bikefit-angles';

const frames = [];
const confidence = { left: 0, right: 0 };

for (const { t, result } of everyFrame) {          // your loop over the video
  const lm = result.landmarks[0];
  if (!lm) continue;
  // Lock onto the side facing the camera by confidence over the whole clip, so one noisy
  // frame can't flip the measurement to the far leg.
  confidence.left += sideConfidence(lm, 'left');
  confidence.right += sideConfidence(lm, 'right');
  const side = confidence.left >= confidence.right ? 'left' : 'right';

  const p = sidePoints(lm, side, video.videoWidth, video.videoHeight);
  frames.push({ t, ankleY: p.ankle.y, angles: sideFrameAngles(p) });
}

const report = analyzeSide(frames, { bikeType: 'gravel' });
console.log(report.verdict, report.angles.knee_flexion_bdc, report.grades.knee_flexion_bdc);
```

Film the rider square to the side, at hip height, pedalling steadily for 20 to 30 seconds. A joint below `MIN_VISIBILITY` (0.5) is left out of every angle that uses it, so an occluded far-side limb never reaches the median.

## Targets

Zones are `[greenLow, greenHigh, redBelow, redAbove]` in degrees. Between green and red is amber.

| Measurement | Green | Source |
|---|---|---|
| Knee flexion at the bottom of the stroke | 30–40° | Holmes method, raised ~8° for pedalling video |
| Elbow flexion | 15–30° | Holmes method |
| Shoulder (torso to upper arm) | 80–95° | fitter's rule of thumb |
| Torso from horizontal | depends on bike type (below) | fitter's rule of thumb |
| Hip at the top of the stroke | ~55–65° on a road bike, **reported only, never graded** | Burt (2014) |

| `bikeType` | Torso green |
|---|---|
| `road_endurance` | 40–50° |
| `road_race` | 32–42° |
| `tt_tri` | 12–28° |
| `gravel` | 42–52° |
| `mtb` | 46–58° |
| `city` | 55–70° |

`zonesFor(bikeType)` returns the full set, and `analyzeSide(frames, { zones })` accepts your own.

Sources and how each number was chosen: [bikefit-research-ranges.md](https://github.com/doniwirawan/bike-fit-analyzer/blob/main/files/bikefit-research-ranges.md).

## Front and rear views (beta)

```js
import { frontalFrameMetrics, analyzeFrontal, FRONTAL } from '@doniwirawan/bikefit-angles';

const metrics = everyLandmarkSet.map((lm) => frontalFrameMetrics(lm, { width, height }));
const r = analyzeFrontal(metrics, { width });
if (!r.ok) console.log(r.reason);   // 'too-few-frames' or 'not-frontal' (a side-on clip)
else console.log(r.left?.peak, r.right?.peak, r.rock);   // flag at FRONTAL.fppa / .rock / .sym
```

These readings have been checked against the literature and against synthetic poses, but not yet against real front or rear footage. Treat them as hints, not verdicts.

## API

| Export | What it does |
|---|---|
| `sideFrameAngles(points, { minVisibility })` | The five angles for one frame |
| `analyzeSide(frames, { bikeType, zones })` | Finds strokes, takes medians at the bottom of each stroke, grades them |
| `sidePoints(landmarks, side, width, height)` | Picks one side out of a 33-point MediaPipe array, scaled to pixels |
| `sideConfidence(landmarks, side)` | Visibility sum for one side, used for near-side locking |
| `frontalFrameMetrics(landmarks, opts)` / `analyzeFrontal(frames, opts)` | Front/rear knee tracking, pelvic rock and symmetry |
| `grade(value, zone)` / `worst(...grades)` | `GREEN` / `AMBER` / `RED` / `GRAY` |
| `angleAt(a, b, c)` / `torsoFromHorizontal(hip, shoulder)` | The geometry |
| `findPeaks(y, minDist, prominence)` / `median(values)` | The signal helpers |
| `ZONES`, `BIKE_TYPES`, `zonesFor()`, `FRONTAL`, `HIP_TOP_REFERENCE`, `SIDE_LANDMARKS`, `MIN_VISIBILITY` | Targets and constants |

TypeScript types are included.

## Limits

These are 2D angles from a single camera. A clip filmed off-axis stretches or squashes them, reach most of all. Knee flexion is the most reliable reading and shoulder/reach the least. This is a starting point before adjusting a bike or booking a fitter, not a replacement for a professional fit, and not medical advice.

## Licence

Source-available under [PolyForm Shield 1.0.0](./LICENSE). You may use it, including commercially, but not to build or provide a product that competes with Bike Fit Analyzer. It is not open source.
