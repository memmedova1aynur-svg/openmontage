import React from "react";
import { interpolate, spring, useVideoConfig } from "remotion";
import { FONT, FONT_HAND, T, clamp01 } from "./theme";

// Watercolour sketchbook: ink lines draw themselves on warm paper, then soft washes bloom in.
// Full 9:16 frame; everything is drawn in code (no stock, no generated images).

const INK = "#2F2B28";
const PAPER = "#FBF5E8";

const Defs: React.FC<{ id: string }> = ({ id }) => (
  <defs>
    <filter id={`wob-${id}`}>
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves={2} seed={3} />
      <feDisplacementMap in="SourceGraphic" scale={4} />
    </filter>
    <filter id={`wash-${id}`} x="-20%" y="-20%" width="140%" height="140%">
      <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves={3} seed={7} result="n" />
      <feDisplacementMap in="SourceGraphic" in2="n" scale={26} result="d" />
      <feGaussianBlur in="d" stdDeviation={3} />
    </filter>
  </defs>
);

// one drawing = ordered strokes: ink lines draw on, then washes bloom
type Stroke = { d: string; wash?: string; w?: number };

const ART: Record<string, Stroke[]> = {
  // a t-shirt held up, the child's head stuck in the collar, cross scribbles
  dress: [
    { d: "M150 230 L230 170 Q300 210 370 170 L450 230 L410 300 L380 280 L380 470 L220 470 L220 280 L190 300 Z", wash: "#9ED8C0" },
    { d: "M150 230 L230 170 Q300 210 370 170 L450 230 L410 300 L380 280 L380 470 L220 470 L220 280 L190 300 Z" },
    { d: "M300 165 m-52 0 a52 52 0 1 0 104 0 a52 52 0 1 0 -104 0", wash: "#F6D2B8" },
    { d: "M300 165 m-52 0 a52 52 0 1 0 104 0 a52 52 0 1 0 -104 0" },
    { d: "M270 150 l14 6 M330 150 l-14 6 M282 190 q18 -14 36 0" },
    { d: "M470 120 q20 -20 40 0 t40 0 M480 150 q20 -20 40 0 t40 0" },
    { d: "M110 110 l30 30 M140 110 l-30 30" },
  ],
  // messy hair, a comb, tears and run-away lines
  hair: [
    { d: "M300 300 m-110 0 a110 110 0 1 0 220 0 a110 110 0 1 0 -220 0", wash: "#F6D2B8" },
    { d: "M300 300 m-110 0 a110 110 0 1 0 220 0 a110 110 0 1 0 -220 0" },
    { d: "M190 260 q-30 -90 40 -120 q30 -60 90 -30 q70 -30 100 40 q40 40 0 110", wash: "#7A5A48" },
    { d: "M190 260 q-30 -90 40 -120 q30 -60 90 -30 q70 -30 100 40 q40 40 0 110 M220 170 q20 -30 50 -10 M300 140 q30 -20 50 10" },
    { d: "M255 300 l20 -8 M345 300 l-20 -8 M270 360 q30 -24 60 0" },
    { d: "M250 320 q-6 22 0 36 q6 -14 0 -36 Z M352 320 q-6 22 0 36 q6 -14 0 -36 Z", wash: "#8FC9EE" },
    { d: "M420 120 l120 -60 l20 30 l-120 60 Z M440 140 l-8 22 M460 130 l-8 22 M480 120 l-8 22 M500 110 l-8 22 M520 100 l-8 22", wash: "#F2A65A" },
    { d: "M80 260 h70 M60 300 h90 M80 340 h70" },
  ],
  // a plate with broccoli and peas, a small hand saying "stop"
  food: [
    { d: "M300 330 m-200 0 a200 90 0 1 0 400 0 a200 90 0 1 0 -400 0", wash: "#FFFFFF" },
    { d: "M300 330 m-200 0 a200 90 0 1 0 400 0 a200 90 0 1 0 -400 0 M300 330 m-150 0 a150 62 0 1 0 300 0 a150 62 0 1 0 -300 0" },
    { d: "M240 330 v-40 M220 290 q-30 -10 -20 -40 q10 -30 40 -20 q20 -30 50 -10 q30 0 20 40 q10 30 -30 30 Z", wash: "#7CC37A" },
    { d: "M240 330 v-40 M220 290 q-30 -10 -20 -40 q10 -30 40 -20 q20 -30 50 -10 q30 0 20 40 q10 30 -30 30 Z" },
    { d: "M340 320 m-14 0 a14 14 0 1 0 28 0 a14 14 0 1 0 -28 0 M372 336 m-14 0 a14 14 0 1 0 28 0 a14 14 0 1 0 -28 0 M350 350 m-14 0 a14 14 0 1 0 28 0 a14 14 0 1 0 -28 0", wash: "#A6D96A" },
    { d: "M460 130 v-70 q0 -16 14 -16 q14 0 14 16 v60 M488 120 v-80 q0 -16 14 -16 q14 0 14 16 v80 M516 120 v-70 q0 -16 14 -16 q14 0 14 16 v90 q0 70 -60 80 q-50 0 -70 -50 l-24 -60 q-6 -18 10 -22 q14 -4 22 12 l14 30", wash: "#F6D2B8" },
  ],
  touch: [
    { d: "M220 420 v-200 q0 -24 22 -24 q22 0 22 24 v150 M264 360 v-200 q0 -24 22 -24 q22 0 22 24 v190 M308 370 v-170 q0 -24 22 -24 q22 0 22 24 v190 M352 400 v-120 q0 -24 22 -24 q22 0 22 24 v170 q0 110 -100 120 q-90 6 -120 -70 l-40 -90 q-10 -26 14 -32 q22 -6 34 18 l24 50", wash: "#F6D2B8" },
    { d: "M120 220 q-30 -40 0 -80 M90 240 q-50 -60 0 -120 M480 220 q30 -40 0 -80 M510 240 q50 -60 0 -120" },
  ],
  smell: [
    { d: "M300 140 q-40 140 -70 200 q-10 30 20 40 q30 10 50 -10 q20 20 50 10 q30 -10 20 -40", wash: "#F6D2B8" },
    { d: "M260 420 q20 20 40 0 q20 20 40 0" },
    { d: "M380 300 q60 -20 40 -70 q-20 -50 40 -70 M400 340 q90 -10 80 -80 q-10 -60 60 -80", wash: "#C9B6EC" },
  ],
  move: [
    { d: "M300 120 m-150 0 a150 150 0 1 0 300 0", w: 0 },
    { d: "M140 200 a170 170 0 0 1 320 0 M460 200 l-10 -40 M460 200 l-40 6" },
    { d: "M300 300 m-50 0 a50 50 0 1 0 100 0 a50 50 0 1 0 -100 0", wash: "#F6D2B8" },
    { d: "M300 300 m-50 0 a50 50 0 1 0 100 0 a50 50 0 1 0 -100 0 M300 350 v120 M300 390 l-70 -30 M300 390 l70 -30 M300 470 l-50 80 M300 470 l50 80", wash: "#9ED8C0" },
    { d: "M120 460 q60 40 120 0 M360 460 q60 40 120 0" },
  ],
  // collar close-up: tag and zig-zag stitches, itchy marks
  seam: [
    { d: "M80 160 Q300 300 520 160 L560 480 L40 480 Z", wash: "#9ED8C0" },
    { d: "M80 160 Q300 300 520 160 L560 480 L40 480 Z" },
    { d: "M240 230 h120 v110 h-120 Z", wash: "#FFFFFF" },
    { d: "M240 230 h120 v110 h-120 Z M260 270 h80 M260 300 h60" },
    { d: "M110 200 l20 20 l20 -20 l20 20 l20 -20 l20 20 l20 -20 M380 220 l20 -20 l20 20 l20 -20 l20 20 l20 -20 l20 20" },
    { d: "M200 90 l20 30 M240 70 l10 34 M380 70 l-10 34 M420 90 l-20 30", wash: "#F07B6B" },
  ],
  // a lumpy, bumpy food texture under a spoon
  texture: [
    { d: "M120 360 q20 -120 120 -110 q40 -70 110 -20 q100 -20 120 90 q40 90 -60 120 q-80 40 -170 10 q-130 -10 -120 -90 Z", wash: "#F2C46D" },
    { d: "M120 360 q20 -120 120 -110 q40 -70 110 -20 q100 -20 120 90 q40 90 -60 120 q-80 40 -170 10 q-130 -10 -120 -90 Z" },
    { d: "M200 320 m-10 0 a10 10 0 1 0 20 0 a10 10 0 1 0 -20 0 M280 290 m-12 0 a12 12 0 1 0 24 0 a12 12 0 1 0 -24 0 M360 330 m-9 0 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 M300 380 m-11 0 a11 11 0 1 0 22 0 a11 11 0 1 0 -22 0 M410 280 m-8 0 a8 8 0 1 0 16 0 a8 8 0 1 0 -16 0", wash: "#C9893A" },
    { d: "M440 80 q60 -10 70 40 q6 50 -50 56 q-50 0 -50 -50 Z M470 176 l-30 120", wash: "#D7DCE2" },
  ],
};

// Draw one art: each stroke takes ~0.45 s, staggered; washes bloom after their outline.
const Drawing: React.FC<{ art: string; f: number; fps: number; id: string; size: number }> = ({ art, f, fps, id, size }) => {
  const strokes = ART[art] ?? [];
  const per = 0.32 * fps;
  return (
    <svg viewBox="0 0 600 600" width={size} height={size}>
      <Defs id={id} />
      {strokes.map((s, i) => {
        const start = i * per;
        const draw = interpolate(f, [start, start + per * 1.6], [0, 1], clamp01);
        const bloom = interpolate(f, [start + per * 0.8, start + per * 3], [0, 1], clamp01);
        return (
          <g key={i}>
            {s.wash && <path d={s.d} fill={s.wash} opacity={0.62 * bloom} filter={`url(#wash-${id})`} transform={`translate(300 300) scale(${0.92 + 0.08 * bloom}) translate(-300 -300)`} />}
            {(s.w ?? 1) > 0 && (
              <path d={s.d} fill="none" stroke={INK} strokeWidth={7.5} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} filter={`url(#wob-${id})`} />
            )}
          </g>
        );
      })}
    </svg>
  );
};

const Paper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ position: "absolute", inset: 0, width: 1080, height: 1920, background: PAPER, overflow: "hidden" }}>
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: 0.35 }}>
      <filter id="paper-grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={11} />
        <feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.38  0 0 0 0 0.28  0 0 0 0.35 0" />
      </filter>
      <rect width={1080} height={1920} filter="url(#paper-grain)" />
    </svg>
    <div style={{ position: "absolute", inset: 0, background: "radial-gradient(120% 80% at 50% 40%, transparent 55%, rgba(120,95,60,0.18) 100%)" }} />
    {children}
  </div>
);

const Label: React.FC<{ text: string; k: number; size?: number }> = ({ text, k, size = 132 }) => (
  <div style={{ fontFamily: FONT_HAND, fontWeight: 700, fontSize: size, color: T.primary, lineHeight: 1, opacity: k, transform: `translateY(${(1 - k) * 24}px) rotate(-2deg)` }}>
    {text}
    <svg width="100%" height={18} viewBox="0 0 300 18" preserveAspectRatio="none" style={{ display: "block", marginTop: 4 }}>
      <path d="M4 12 Q80 2 150 10 T296 8" stroke="#E9A23B" strokeWidth={5} fill="none" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - k} />
    </svg>
  </div>
);

// items: [{art, at, label}] - "one": one drawing at a time (page flips), "stack": they gather in a column
export const SketchScene: React.FC<{ f: number; p: Record<string, any>; startT: number }> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const t = startT + f / fps;
  const items: { art: string; at: number; label: string; sub?: string }[] = p.items ?? [];
  if (p.mode === "stack") {
    return (
      <Paper>
        {p.title && (
          <div style={{ position: "absolute", top: 200, left: 0, right: 0, textAlign: "center", fontFamily: FONT_HAND, fontWeight: 700, fontSize: 84, color: T.primary, opacity: interpolate(f, [0, 10], [0, 1], clamp01) }}>{p.title}</div>
        )}
        {items.map((it, i) => {
          const fi = Math.round((t - it.at) * fps);
          if (fi < 0) return null;
          const k = spring({ frame: fi, fps, config: { damping: 15, stiffness: 150 } });
          return (
            <div key={i} style={{ position: "absolute", top: 300 + i * 410, left: 30, right: 30, display: "flex", alignItems: "center", justifyContent: "space-between", flexDirection: i % 2 ? "row-reverse" : "row" }}>
              <div style={{ position: "relative", width: 500, height: 500 }}>
                <svg width={500} height={500} viewBox="0 0 600 600" style={{ position: "absolute", inset: 0 }}>
                  <Defs id={`sb${i}`} />
                  <circle cx={300} cy={300} r={240 * k} fill={["#F8DCC8", "#E3DAF3", "#CDEBDD"][i % 3]} opacity={0.75} filter={`url(#wash-sb${i})`} />
                </svg>
                <div style={{ position: "absolute", inset: 0 }}>
                  <Drawing art={it.art} f={fi} fps={fps} id={`s${i}`} size={500} />
                </div>
              </div>
              <div style={{ flex: 1, display: "flex", justifyContent: "center" }}>
                <Label text={it.label} k={k} size={120} />
              </div>
            </div>
          );
        })}
      </Paper>
    );
  }
  const cur = [...items].reverse().find((x) => t >= x.at) ?? items[0];
  const ci = items.indexOf(cur);
  const fi = Math.round((t - cur.at) * fps);
  const k = spring({ frame: fi - 6, fps, config: { damping: 15, stiffness: 150 } });
  const turn = interpolate(fi, [0, 8], [1, 0], clamp01);
  return (
    <Paper>
      <div style={{ position: "absolute", inset: 0, transform: `translateX(${turn * 120}px) rotate(${turn * 2}deg)`, opacity: 1 - turn * 0.6 }}>
        <div style={{ position: "absolute", top: 200, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
          <Label text={cur.label} k={k} />
        </div>
        <div style={{ position: "absolute", top: 280, left: -20, width: 1120, height: 1120 }}>
          <svg width={1120} height={1120} viewBox="0 0 600 600" style={{ position: "absolute", inset: 0 }}>
            <Defs id={`bg${ci}`} />
            <circle cx={300} cy={320} r={250 * interpolate(fi, [0, 18], [0.6, 1], clamp01)} fill={["#CDEBDD", "#F8DCC8", "#E3DAF3", "#D6ECF6"][ci % 4]} opacity={0.7} filter={`url(#wash-bg${ci})`} />
          </svg>
          <div style={{ position: "absolute", inset: 0, display: "flex", justifyContent: "center", alignItems: "center" }}>
            <Drawing art={cur.art} f={fi} fps={fps} id={`o${ci}`} size={1040} />
          </div>
        </div>
        {cur.sub && (
          <div style={{ position: "absolute", top: 1390, left: 0, right: 0, textAlign: "center", fontFamily: FONT_HAND, fontWeight: 700, fontSize: 70, color: INK, opacity: interpolate(fi, [20, 34], [0, 1], clamp01) }}>{cur.sub}</div>
        )}
      </div>
    </Paper>
  );
};

// A counter that rolls smoothly up to its target (odometer digits), e.g. "100" for "Yüz dəfə deyirəm".
export const RollingCounter: React.FC<{ value: number; prog: number; size: number; color: string }> = ({ value, prog, size, color }) => {
  const shown = value * prog;
  const digits = String(value).length;
  return (
    <div style={{ display: "flex", height: size * 1.1, overflow: "hidden", fontFamily: FONT, fontWeight: 900, fontSize: size, color, lineHeight: 1.1 }}>
      {Array.from({ length: digits }, (_, i) => {
        const place = 10 ** (digits - 1 - i);
        const v = shown / place;
        const hidden = i < digits - 1 && shown < place * 0.95;
        return (
          <div key={i} style={{ width: size * 0.66, textAlign: "center", opacity: hidden ? 0 : 1 }}>
            <div style={{ transform: `translateY(${-((v % 10) * size * 1.1)}px)` }}>
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map((d, j) => (
                <div key={j} style={{ height: size * 1.1 }}>{d}</div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const SKETCH: Record<string, React.FC<{ f: number; p: Record<string, any>; startT: number }>> = {
  sketch: SketchScene,
};

// "100" moment: the number rolls up smoothly, then a hand-drawn ring loops around it.
export const CounterPop: React.FC<{ o: any; f: number }> = ({ o, f }) => {
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const roll = interpolate(f, [2, (o.rollSec ?? 1.1) * fps], [0, 1], { ...clamp01, easing: (x: number) => 1 - Math.pow(1 - x, 3) });
  const ring = interpolate(f, [(o.rollSec ?? 1.1) * fps, (o.rollSec ?? 1.1) * fps + 12], [0, 1], clamp01);
  const enter = spring({ frame: f, fps, config: { damping: 14, stiffness: 170 } });
  const exit = interpolate(f, [dur - 8, dur], [1, 0], clamp01);
  return (
    <div style={{ position: "absolute", top: o.top ?? 260, left: o.left ?? 60, opacity: Math.min(1, enter * 1.5) * exit, transform: `scale(${0.8 + 0.2 * enter})`, transformOrigin: "0 50%" }}>
      <div style={{ position: "relative", display: "flex", alignItems: "center", gap: 18 }}>
        <div style={{ position: "relative" }}>
          <RollingCounter value={o.value ?? 100} prog={roll} size={150} color={T.primary} />
          <svg viewBox="0 0 300 200" width={330} height={220} style={{ position: "absolute", left: -40, top: -30, overflow: "visible" }}>
            <path d="M40 110 C40 30 250 10 270 90 C290 170 80 200 50 140 C35 110 60 70 120 60" fill="none" stroke="#E9A23B" strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - ring} />
          </svg>
        </div>
        <div style={{ fontFamily: FONT_HAND, fontWeight: 700, fontSize: 70, color: T.primary, lineHeight: 0.95, textShadow: "0 0 14px rgba(255,255,255,0.95)", opacity: interpolate(f, [8, 18], [0, 1], clamp01) }}>{o.label ?? "dəfə"}</div>
      </div>
    </div>
  );
};
