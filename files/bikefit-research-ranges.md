# Bike-fit research ranges (dynamic, road position, side-on 2D)

These are the target zones the analyzer grades against. They are **dynamic**
ranges (measured while pedaling on video), which run a few degrees higher than
static goniometer numbers.

| Angle (side-on) | Green zone | Red means |
|---|---|---|
| Knee flexion at bottom (BDC) | 30-40 deg | over ~42 saddle too low (raise); under ~28 too high (lower) |
| Torso from horizontal | 40-50 deg | over ~56 too upright; under ~34 very aggressive |
| Elbow bend | 15-30 deg | near 0 locked out (soften / shorten reach) |
| Shoulder (torso to upper arm) | 80-95 deg | much lower = closed/scrunched cockpit, weight on hands |
| Hip at top (TDC) | ~85-110 deg | flexibility / reach dependent (report only) |

Angles use ~2.5 deg edge tolerance because a phone video only resolves to a few
degrees. BDC is measured as the median across several strokes so one blurry
frame can't skew the result.

## Frontal plane (front / rear view) - BETA

These flags are softer than the side-on ones and are reported as hints, not
grades. The thresholds sit at the **top** of the healthy range rather than near
the mean: healthy riders on a correctly-set saddle already show real
frontal-plane movement, so a threshold near the mean flags most normal people.

| Reading (front/rear) | Flag at | Healthy reference |
|---|---|---|
| Knee tracking (FPPA) | +/- 10 deg | knee coronal ROM 6.6 +/- 2.7 deg; valgus component 5.0 +/- 2.2 deg (mean+2SD ~9.4) |
| Pelvic rock (peak-to-peak hip-line tilt) | 12 deg | pelvis coronal ROM 7.1 +/- 2.5 deg, observed range 2.0-11.7 deg |
| Left/right symmetry (difference in knee FPPA) | 9 deg | below the smallest detectable difference of 2D FPPA (~7.5-8.9 deg) a L/R gap is measurement noise |

Two things to keep in mind before tightening these:

- **A correctly-fitted rider rocks.** Healthy adults at 85.5% inseam saddle
  height show 7.1 deg of pelvic coronal ROM. The original 6 deg rock threshold
  was *below the healthy mean*, so it would have flagged the majority of
  correctly-fitted riders as "saddle possibly too high".
- **2D FPPA has a floor.** Reported SEM is 2.7-3.0 deg and the smallest
  detectable difference is 7.5-8.9 deg. Any frontal threshold under ~9 deg is
  inside the measurement noise of the method, so it cannot be trusted no matter
  how good the pose model is.

Still unvalidated: these come from the literature, not from clips through this
tool. They need checking against real front/rear footage before the beta label
comes off.

## Sources

- **Cycling kinematics in healthy adults** (31 adults, saddle at 85.5% inseam) -
  source of the healthy frontal-plane ROM: pelvis coronal 7.1 +/- 2.5 deg, knee
  coronal 6.6 +/- 2.7 deg: https://pmc.ncbi.nlm.nih.gov/articles/PMC8675512/
- **Knee alignment and frontal-plane knee biomechanics in cycling** - peak knee
  adduction by alignment group (varus 10.3 +/- 4.8, neutral 5.2, valgus -2.2);
  valgus-aligned riders sit around 10 deg of abduction:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5950749/
- **Reliability of 2D video assessment of frontal-plane knee valgus** - SEM
  2.72-3.01 deg, smallest detectable difference 7.54-8.93 deg; this is the floor
  under any frontal threshold: https://pubmed.ncbi.nlm.nih.gov/22104115/
- **Holmes method** - clinical standard for knee angle at the bottom of the
  stroke; joint-angle averages (knee 36 +/- 7 deg, elbow 19 +/- 8 deg):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/
- **Dynamic-vs-static validity study** - angles measured while pedaling on video
  run ~8 deg higher than static goniometer numbers (why the knee zone is a
  dynamic 30-40, not the static 25-35): https://pubmed.ncbi.nlm.nih.gov/24499342/
- **Practitioner cross-check** for the full joint set (torso, shoulder, hip):
  https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles
