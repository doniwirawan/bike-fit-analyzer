/** A 2D point in any consistent unit (pixels or 0-1). `visibility` is 0-1; missing means fully visible. */
export interface Point { x: number; y: number; visibility?: number }

/** [greenLow, greenHigh, redBelow, redAbove] in degrees. */
export type Zone = readonly [number, number, number, number];
export type Grade = 'GREEN' | 'AMBER' | 'RED' | 'GRAY';
export type BikeType = 'road_endurance' | 'road_race' | 'tt_tri' | 'gravel' | 'mtb' | 'city';
export type SideMetric = 'knee_flexion_bdc' | 'torso_from_horiz' | 'elbow_flexion' | 'shoulder_angle';
export type Zones = Record<SideMetric, Zone>;

export interface SidePoints { shoulder: Point; elbow: Point; wrist: Point; hip: Point; knee: Point; ankle: Point }
export interface FrameAngles extends Record<SideMetric, number> { hip_angle: number }
export interface SideFrame { t: number; ankleY: number; angles: FrameAngles }
export interface SideResult {
  angles: Record<SideMetric, number | null>;
  grades: Record<SideMetric, Grade>;
  verdict: Grade;
  strokes: number;
  hipTop: number | null;
  bdcFrames: number[];
  tdcFrames: number[];
}
export interface FrontalFrame {
  L: { fppa: number; medialSign: number } | null;
  R: { fppa: number; medialSign: number } | null;
  hipTilt: number;
  hipSpan: number;
}
export type FrontalResult =
  | { ok: false; reason: 'too-few-frames' | 'not-frontal' }
  | { ok: true; left: { peak: number; median: number | null } | null; right: { peak: number; median: number | null } | null; rock: number | null; frames: number };

export const ZONES: Readonly<Zones>;
export const BIKE_TYPES: Readonly<Record<BikeType, Zone>>;
export const HIP_TOP_REFERENCE: readonly [number, number];
export const FRONTAL: Readonly<{ fppa: number; rock: number; sym: number }>;
export const MIN_VISIBILITY: number;
export const SIDE_LANDMARKS: Readonly<Record<'left' | 'right', Readonly<Record<keyof SidePoints, number>>>>;

export function zonesFor(bikeType?: BikeType): Zones;
export function angleAt(a: Point, b: Point, c: Point): number;
export function torsoFromHorizontal(hip: Point, shoulder: Point): number;
export function median(values: number[]): number | null;
export function grade(value: number | null | undefined, zone: Zone): Grade;
export function worst(...grades: Grade[]): Grade;
export function findPeaks(y: number[], minDist: number, prominence: number): number[];
export function sidePoints(landmarks: Point[], side: 'left' | 'right', width?: number, height?: number): SidePoints;
export function sideConfidence(landmarks: Point[], side: 'left' | 'right'): number;
export function sideFrameAngles(points: Partial<SidePoints>, options?: { minVisibility?: number }): FrameAngles;
export function analyzeSide(frames: SideFrame[], options?: { bikeType?: BikeType; zones?: Zones }): SideResult | null;
export function frontalFrameMetrics(landmarks: Point[], options?: { width?: number; height?: number; minVisibility?: number }): FrontalFrame;
export function analyzeFrontal(frames: (FrontalFrame | null)[], options?: { width?: number }): FrontalResult;
