/**
 * bikefit-angles: the measurement and grading core of Bike Fit Analyzer.
 *
 * Pose model agnostic. Feed it 2D points (pixels or normalised, any consistent unit) from any
 * pose estimator; helpers are included for the 33-point MediaPipe / BlazePose layout.
 *
 * This file is the one copy of the maths: the analyzer at bikefit.doniwirawan.xyz imports it
 * directly, and it is published from this folder as `bikefit-angles` on npm and
 * `@doniwirawan/bikefit-angles` on GitHub Packages.
 *
 * Source-available under PolyForm Shield 1.0.0 (see LICENSE): free to use, but not to build
 * a product that competes with Bike Fit Analyzer.
 */

/* ------------------------------------------------------------------ targets */

/**
 * Side-view targets: [greenLow, greenHigh, redBelow, redAbove]. Inside green = GREEN, outside
 * red = RED, between = AMBER. Knee and elbow are the Holmes-method averages, raised ~8 deg for
 * dynamic (pedalling) video; shoulder is a fitter's rule of thumb.
 */
export const ZONES = Object.freeze({
  knee_flexion_bdc: [30, 40, 28, 42],
  torso_from_horiz: [40, 50, 34, 56],
  elbow_flexion: [15, 30, 8, 45],
  shoulder_angle: [80, 95, 70, 105],
});

/** Torso target per bike type. Only the torso changes with the bike; knee, elbow and shoulder do not. */
export const BIKE_TYPES = Object.freeze({
  road_endurance: [40, 50, 34, 56],
  road_race: [32, 42, 28, 48],
  tt_tri: [12, 28, 8, 34],
  gravel: [42, 52, 36, 58],
  mtb: [46, 58, 40, 64],
  city: [55, 70, 48, 78],
});

/** Hip at the top of the stroke is reported, never graded. Road reference ~55-65 deg (Burt 2014). */
export const HIP_TOP_REFERENCE = Object.freeze([55, 65]);

/**
 * Front/rear (beta) flag thresholds, in degrees. Set at the top of the healthy range, not the
 * mean: FPPA (knee tracking) 10, pelvic rock 12, left/right difference 9.
 */
export const FRONTAL = Object.freeze({ fppa: 10, rock: 12, sym: 9 });

/** A landmark below this visibility is treated as not seen. */
export const MIN_VISIBILITY = 0.5;

/** Zones for a bike type: the side-view zones with that bike's torso target. */
export function zonesFor(bikeType = 'road_endurance') {
  const torso = BIKE_TYPES[bikeType];
  if (!torso) throw new RangeError(`Unknown bike type "${bikeType}". Known: ${Object.keys(BIKE_TYPES).join(', ')}`);
  return { ...ZONES, torso_from_horiz: torso };
}

/* ------------------------------------------------------------------ basics */

const deg = (r) => (r * 180) / Math.PI;

/** Interior angle at b, in degrees, of the path a-b-c. NaN if a segment has no length. */
export function angleAt(a, b, c) {
  const v1x = a.x - b.x, v1y = a.y - b.y, v2x = c.x - b.x, v2y = c.y - b.y;
  const n1 = Math.hypot(v1x, v1y), n2 = Math.hypot(v2x, v2y);
  if (!n1 || !n2) return NaN;
  return deg(Math.acos(Math.max(-1, Math.min(1, (v1x * v2x + v1y * v2y) / (n1 * n2)))));
}

/** Torso angle from horizontal, hip to shoulder, 0-90 deg whichever way the rider faces. */
export function torsoFromHorizontal(hip, shoulder) {
  return deg(Math.atan2(Math.abs(shoulder.y - hip.y), Math.abs(shoulder.x - hip.x)));
}

/** Median of the finite numbers in a list, or null if there are none. */
export function median(values) {
  const a = values.filter((v) => Number.isFinite(v)).sort((x, y) => x - y);
  if (!a.length) return null;
  const m = a.length >> 1;
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

/** Grade a value against a zone: GREEN, AMBER, RED, or GRAY when there is no reading. */
export function grade(value, zone) {
  if (value == null || Number.isNaN(value)) return 'GRAY';
  const [glo, ghi, rlo, rhi] = zone;
  if (value >= glo && value <= ghi) return 'GREEN';
  if (value < rlo || value > rhi) return 'RED';
  return 'AMBER';
}

/** The worst of several grades (RED > AMBER > GREEN > GRAY). */
export function worst(...grades) {
  const order = { GRAY: 0, GREEN: 1, AMBER: 2, RED: 3 };
  return grades.filter((g) => g in order).reduce((a, b) => (order[b] > order[a] ? b : a), 'GRAY');
}

/**
 * Indices of local maxima at least minDist apart that stand at least `prominence` above the
 * lower of their two neighbouring minima. NaN entries are skipped.
 */
export function findPeaks(y, minDist, prominence) {
  const peaks = [];
  for (let i = 0; i < y.length; i++) {
    if (Number.isNaN(y[i])) continue;
    const lo = Math.max(0, i - minDist), hi = Math.min(y.length, i + minDist + 1);
    let isMax = true, bL = y[i], bR = y[i];
    for (let j = lo; j < hi; j++) if (!Number.isNaN(y[j]) && y[j] > y[i]) { isMax = false; break; }
    if (!isMax) continue;
    for (let j = lo; j < i; j++) if (!Number.isNaN(y[j])) bL = Math.min(bL, y[j]);
    for (let j = i + 1; j < hi; j++) if (!Number.isNaN(y[j])) bR = Math.min(bR, y[j]);
    if (y[i] - Math.max(bL, bR) >= prominence) {
      if (peaks.length && i - peaks[peaks.length - 1] < minDist) {
        if (y[i] > y[peaks[peaks.length - 1]]) peaks[peaks.length - 1] = i;
      } else peaks.push(i);
    }
  }
  return peaks;
}

/* --------------------------------------------------------------- MediaPipe */

/** MediaPipe / BlazePose landmark indices for each side of the body. */
export const SIDE_LANDMARKS = Object.freeze({
  left: Object.freeze({ shoulder: 11, elbow: 13, wrist: 15, hip: 23, knee: 25, ankle: 27 }),
  right: Object.freeze({ shoulder: 12, elbow: 14, wrist: 16, hip: 24, knee: 26, ankle: 28 }),
});

/**
 * Pick one side's six joints out of a 33-point landmark array, scaled to pixels when width and
 * height are given (MediaPipe returns 0-1 coordinates). Keeps `visibility`.
 */
export function sidePoints(landmarks, side, width = 1, height = 1) {
  const ids = SIDE_LANDMARKS[side];
  if (!ids) throw new RangeError('side must be "left" or "right"');
  const out = {};
  for (const k in ids) {
    const p = landmarks[ids[k]];
    out[k] = { x: p.x * width, y: p.y * height, visibility: p.visibility ?? 1 };
  }
  return out;
}

/** Sum of the six joints' visibility for one side, used to lock onto the side facing the camera. */
export function sideConfidence(landmarks, side) {
  return Object.values(SIDE_LANDMARKS[side]).reduce((a, i) => a + (landmarks[i].visibility ?? 0), 0);
}

/* ------------------------------------------------------------------ side view */

/**
 * The five angles for one frame, from one side's joints. A joint below `minVisibility` gives
 * NaN for every angle that uses it, so an occluded limb never reaches a median.
 * @returns {{knee_flexion_bdc:number, torso_from_horiz:number, elbow_flexion:number, shoulder_angle:number, hip_angle:number}}
 */
export function sideFrameAngles(p, { minVisibility = MIN_VISIBILITY } = {}) {
  const ok = (...ks) => ks.every((k) => p[k] && (p[k].visibility ?? 1) >= minVisibility);
  return {
    knee_flexion_bdc: ok('hip', 'knee', 'ankle') ? 180 - angleAt(p.hip, p.knee, p.ankle) : NaN,
    torso_from_horiz: ok('hip', 'shoulder') ? torsoFromHorizontal(p.hip, p.shoulder) : NaN,
    elbow_flexion: ok('shoulder', 'elbow', 'wrist') ? 180 - angleAt(p.shoulder, p.elbow, p.wrist) : NaN,
    shoulder_angle: ok('hip', 'shoulder', 'elbow') ? angleAt(p.hip, p.shoulder, p.elbow) : NaN,
    hip_angle: ok('shoulder', 'hip', 'knee') ? angleAt(p.shoulder, p.hip, p.knee) : NaN,
  };
}

/**
 * Turn a side-view clip into a graded result.
 *
 * Each frame is `{ t, ankleY, angles }`: the time in seconds, the ankle's vertical position
 * (image y grows downward, so the lowest ankle is the largest value; NaN if unseen) and the
 * output of sideFrameAngles(). The bottom of each stroke is found from the ankle's peaks, the
 * angles there are taken by median, and each is graded against the bike type's zones.
 *
 * @returns {null | {angles:object, grades:object, verdict:string, strokes:number, hipTop:number|null, bdcFrames:number[], tdcFrames:number[]}}
 *   null when there are too few frames or no clear pedal strokes.
 */
export function analyzeSide(frames, { bikeType = 'road_endurance', zones } = {}) {
  if (!frames || frames.length < 5) return null;
  const ankle = frames.map((f) => (Number.isFinite(f.ankleY) ? f.ankleY : NaN));
  const sorted = ankle.filter((v) => !Number.isNaN(v)).sort((a, b) => a - b);
  if (sorted.length < 5) return null;
  const amp = sorted[Math.floor(sorted.length * 0.95)] - sorted[Math.floor(sorted.length * 0.05)];
  const span = frames[frames.length - 1].t - frames[0].t;
  const fps = span > 0 ? frames.length / span : 30;
  const minDist = Math.max(3, Math.round(fps * 0.35)), prom = Math.max(2, 0.25 * amp);
  const bdc = findPeaks(ankle, minDist, prom);
  const tdc = findPeaks(ankle.map((v) => -v), minDist, prom);
  if (!bdc.length) return null;
  const at = (idx, m) => median(idx.map((i) => frames[i].angles[m]));
  const angles = {
    knee_flexion_bdc: at(bdc, 'knee_flexion_bdc'),
    torso_from_horiz: at(bdc, 'torso_from_horiz'),
    elbow_flexion: at(bdc, 'elbow_flexion'),
    shoulder_angle: at(bdc, 'shoulder_angle'),
  };
  const z = zones || zonesFor(bikeType);
  const grades = {};
  for (const m in angles) grades[m] = grade(angles[m], z[m]);
  return {
    angles, grades, verdict: worst(...Object.values(grades)), strokes: bdc.length,
    hipTop: tdc.length ? at(tdc, 'hip_angle') : null, bdcFrames: bdc, tdcFrames: tdc,
  };
}

/* ------------------------------------------------------------- front / rear */

/**
 * Frontal-plane readings for one frame from a 33-point landmark array (beta). Knee tracking is
 * the frontal-plane projection angle (FPPA), signed toward the body's midline.
 */
export function frontalFrameMetrics(landmarks, { width = 1, height = 1, minVisibility = MIN_VISIBILITY } = {}) {
  const P = (i) => ({ x: landmarks[i].x * width, y: landmarks[i].y * height, v: landmarks[i].visibility ?? 0 });
  const hL = P(23), hR = P(24), kL = P(25), kR = P(26), aL = P(27), aR = P(28);
  const center = (hL.x + hR.x) / 2;
  const leg = (h, k, a) => {
    if (Math.abs(a.y - h.y) < 1e-9) return null;
    const lineX = h.x + (a.x - h.x) * ((k.y - h.y) / (a.y - h.y));
    const dev = k.x - lineX;
    const medial = h.x < center ? dev : -dev;
    return { fppa: 180 - angleAt(h, k, a), medialSign: Math.sign(medial) };
  };
  const ok = (...p) => p.every((q) => q.v >= minVisibility);
  return {
    L: ok(hL, kL, aL) ? leg(hL, kL, aL) : null,
    R: ok(hR, kR, aR) ? leg(hR, kR, aR) : null,
    hipTilt: ok(hL, hR) ? deg(Math.atan2(hR.y - hL.y, hR.x - hL.x)) : NaN,
    hipSpan: ok(hL, hR) ? Math.abs(hR.x - hL.x) : NaN,
  };
}

/**
 * Summarise a front or rear clip (beta, report only). Returns null with `reason` when the clip
 * cannot be read: too few frames, or hips so close together that it is really a side view
 * (median hip span under 4% of `width`).
 * @returns {{ok:boolean, reason?:string, left?:object|null, right?:object|null, rock?:number|null, frames?:number}}
 */
export function analyzeFrontal(frameMetrics, { width = 1 } = {}) {
  const F = frameMetrics.filter(Boolean);
  if (F.length < 5) return { ok: false, reason: 'too-few-frames' };
  const spans = F.map((f) => f.hipSpan).filter((x) => !Number.isNaN(x));
  if (spans.length >= 5 && median(spans) < 0.04 * width) return { ok: false, reason: 'not-frontal' };
  const legStat = (s) => {
    const v = F.map((f) => f[s]).filter(Boolean).map((x) => x.medialSign * x.fppa);
    if (v.length < 3) return null;
    const q = [...v].sort((a, b) => a - b);
    return { peak: q[Math.floor(q.length * 0.9)], median: median(v) };
  };
  const tilts = F.map((f) => f.hipTilt).filter((x) => !Number.isNaN(x));
  let rock = null;
  if (tilts.length >= 5) {
    const q = [...tilts].sort((a, b) => a - b);
    rock = q[Math.floor(q.length * 0.95)] - q[Math.floor(q.length * 0.05)];
  }
  return { ok: true, left: legStat('L'), right: legStat('R'), rock, frames: F.length };
}
