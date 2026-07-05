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

## Sources

- **Holmes method** - clinical standard for knee angle at the bottom of the
  stroke; joint-angle averages (knee 36 +/- 7 deg, elbow 19 +/- 8 deg):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/
- **Dynamic-vs-static validity study** - angles measured while pedaling on video
  run ~8 deg higher than static goniometer numbers (why the knee zone is a
  dynamic 30-40, not the static 25-35): https://pubmed.ncbi.nlm.nih.gov/24499342/
- **Practitioner cross-check** for the full joint set (torso, shoulder, hip):
  https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles
