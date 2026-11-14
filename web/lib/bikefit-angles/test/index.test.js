import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  angleAt, torsoFromHorizontal, grade, worst, median, zonesFor, sideFrameAngles, analyzeSide,
  sidePoints, frontalFrameMetrics, analyzeFrontal, ZONES, BIKE_TYPES,
} from '../index.js';

const close = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`);
const rad = (d) => (d * Math.PI) / 180;

// A rider built with known angles: knee flexion 38, torso 48 from horizontal, elbow flexion 13.
function pose({ knee = 38, torso = 48, elbow = 13 } = {}) {
  const hip = { x: 0, y: 0 }, kneeP = { x: 0, y: 100 };
  const ankle = { x: kneeP.x + 100 * Math.sin(rad(knee)), y: kneeP.y + 100 * Math.cos(rad(knee)) };
  const shoulder = { x: 100 * Math.cos(rad(torso)), y: -100 * Math.sin(rad(torso)) };
  const upper = { x: 0.6, y: 0.8 };                       // upper-arm direction from the shoulder
  const elbowP = { x: shoulder.x + 60 * upper.x, y: shoulder.y + 60 * upper.y };
  const a = Math.atan2(upper.y, upper.x) - rad(elbow);     // forearm turned by the flexion angle
  const wrist = { x: elbowP.x + 50 * Math.cos(a), y: elbowP.y + 50 * Math.sin(a) };
  return { hip, knee: kneeP, ankle, shoulder, elbow: elbowP, wrist };
}

test('angleAt measures the interior angle', () => {
  close(angleAt({ x: 1, y: 0 }, { x: 0, y: 0 }, { x: 0, y: 1 }), 90);
  close(angleAt({ x: 1, y: 0 }, { x: 0, y: 0 }, { x: -1, y: 0 }), 180);
  assert.ok(Number.isNaN(angleAt({ x: 0, y: 0 }, { x: 0, y: 0 }, { x: 1, y: 1 })));
});

test('torso angle is the same whichever way the rider faces', () => {
  close(torsoFromHorizontal({ x: 0, y: 0 }, { x: 10, y: -10 }), 45);
  close(torsoFromHorizontal({ x: 0, y: 0 }, { x: -10, y: -10 }), 45);
});

test('sideFrameAngles recovers the angles a pose was built with', () => {
  const a = sideFrameAngles(pose());
  close(a.knee_flexion_bdc, 38);
  close(a.torso_from_horiz, 48);
  close(a.elbow_flexion, 13);
  assert.ok(a.shoulder_angle > 0 && a.hip_angle > 0);
});

test('a joint below the visibility gate gives NaN for every angle that uses it', () => {
  const p = pose();
  p.knee = { ...p.knee, visibility: 0.2 };
  const a = sideFrameAngles(p);
  assert.ok(Number.isNaN(a.knee_flexion_bdc));
  assert.ok(Number.isNaN(a.hip_angle));
  close(a.torso_from_horiz, 48);
});

test('grading follows the zone edges', () => {
  const z = ZONES.knee_flexion_bdc; // [30,40,28,42]
  assert.equal(grade(35, z), 'GREEN');
  assert.equal(grade(40, z), 'GREEN');
  assert.equal(grade(41, z), 'AMBER');
  assert.equal(grade(43, z), 'RED');
  assert.equal(grade(NaN, z), 'GRAY');
  assert.equal(worst('GREEN', 'AMBER', 'GRAY'), 'AMBER');
  assert.equal(worst(), 'GRAY');
});

test('only the torso target changes with the bike type', () => {
  for (const b of Object.keys(BIKE_TYPES)) {
    const z = zonesFor(b);
    assert.deepEqual(z.knee_flexion_bdc, ZONES.knee_flexion_bdc);
    assert.deepEqual(z.torso_from_horiz, BIKE_TYPES[b]);
  }
  assert.throws(() => zonesFor('unicycle'), RangeError);
});

test('median ignores non-numbers', () => {
  assert.equal(median([3, NaN, 1, 2]), 2);
  assert.equal(median([]), null);
});

// A 10 s clip at 30 fps, pedalling at 90 rpm: the ankle bobs 1.5 times a second.
function clip(angles, { seconds = 10, fps = 30, rpm = 90 } = {}) {
  const frames = [];
  for (let i = 0; i < seconds * fps; i++) {
    const t = i / fps;
    frames.push({ t, ankleY: 300 + 40 * Math.sin(2 * Math.PI * (rpm / 60) * t), angles });
  }
  return frames;
}

test('analyzeSide finds each pedal stroke and grades the bottom of it', () => {
  const r = analyzeSide(clip(sideFrameAngles(pose())), { bikeType: 'road_endurance' });
  assert.ok(r);
  assert.ok(r.strokes >= 14 && r.strokes <= 16, `strokes ${r.strokes}`);
  close(r.angles.knee_flexion_bdc, 38);
  assert.equal(r.grades.knee_flexion_bdc, 'GREEN');
  assert.equal(r.grades.elbow_flexion, 'AMBER');
  assert.equal(r.verdict, worst(...Object.values(r.grades)));
});

test('the same torso grades differently on different bikes', () => {
  const angles = sideFrameAngles(pose({ torso: 48 }));
  assert.equal(analyzeSide(clip(angles), { bikeType: 'mtb' }).grades.torso_from_horiz, 'GREEN');
  assert.equal(analyzeSide(clip(angles), { bikeType: 'tt_tri' }).grades.torso_from_horiz, 'RED');
});

test('analyzeSide returns null when nobody is pedalling', () => {
  const still = clip(sideFrameAngles(pose())).map((f) => ({ ...f, ankleY: 300 }));
  assert.equal(analyzeSide(still), null);
  assert.equal(analyzeSide([]), null);
});

test('sidePoints scales MediaPipe coordinates and keeps visibility', () => {
  const lm = Array.from({ length: 33 }, (_, i) => ({ x: i / 100, y: 0.5, visibility: 0.9 }));
  const p = sidePoints(lm, 'left', 1000, 500);
  close(p.knee.x, 250); close(p.knee.y, 250); assert.equal(p.knee.visibility, 0.9);
});

test('analyzeFrontal refuses a side-on clip', () => {
  const lm = Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5, visibility: 1 }));
  lm[23] = { x: 0.50, y: 0.40, visibility: 1 }; lm[24] = { x: 0.505, y: 0.40, visibility: 1 };
  lm[25] = { x: 0.50, y: 0.60, visibility: 1 }; lm[26] = { x: 0.505, y: 0.60, visibility: 1 };
  lm[27] = { x: 0.50, y: 0.80, visibility: 1 }; lm[28] = { x: 0.505, y: 0.80, visibility: 1 };
  const frames = Array.from({ length: 10 }, () => frontalFrameMetrics(lm, { width: 1000, height: 1000 }));
  assert.deepEqual(analyzeFrontal(frames, { width: 1000 }), { ok: false, reason: 'not-frontal' });
});

test('analyzeFrontal reports knee tracking and pelvic rock from a front view', () => {
  const frames = Array.from({ length: 20 }, (_, i) => {
    const tilt = (i % 2 ? 1 : -1) * 0.01;
    const lm = Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5, visibility: 1 }));
    lm[23] = { x: 0.40, y: 0.40 + tilt, visibility: 1 }; lm[24] = { x: 0.60, y: 0.40 - tilt, visibility: 1 };
    lm[25] = { x: 0.42, y: 0.60, visibility: 1 };        lm[26] = { x: 0.58, y: 0.60, visibility: 1 };
    lm[27] = { x: 0.40, y: 0.80, visibility: 1 };        lm[28] = { x: 0.60, y: 0.80, visibility: 1 };
    return frontalFrameMetrics(lm, { width: 1000, height: 1000 });
  });
  const r = analyzeFrontal(frames, { width: 1000 });
  assert.equal(r.ok, true);
  assert.ok(r.left.peak > 0 && r.right.peak > 0, 'both knees drift toward the midline');
  assert.ok(r.rock > 0);
});
