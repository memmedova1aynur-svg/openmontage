import { Easing, interpolate } from "remotion";
import { FPS } from "./brand";

/** Music is locked to 120 BPM: one beat = 0.5 s = 15 frames. */
export const BPM = 120;
export const BEAT = 60 / BPM;
export const beat = (n: number) => n * BEAT;
export const sec = (s: number) => Math.round(s * FPS);

export const easeOut = Easing.bezier(0.16, 1, 0.3, 1); // expo-like out
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);
export const easeBack = Easing.bezier(0.34, 1.4, 0.64, 1);
const clampOpts = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0→1 progress between two times (seconds) with easing. */
export const prog = (frame: number, t0: number, t1: number, easing: (x: number) => number = easeOut) =>
  interpolate(frame / FPS, [t0, t1], [0, 1], { ...clampOpts, easing });

export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
export { clampOpts };
