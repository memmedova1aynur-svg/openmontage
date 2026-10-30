import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, FONT_HAND, Pill, T, clamp01 } from "./theme";

// Paper-cut collage: torn paper strips, tape, sticker-like cut-outs, stop-motion timing.
// Everything is drawn in code.

// stop-motion: hold each pose for 2 frames (12 fps feel)
export const step = (f: number, n = 2) => Math.floor(f / n) * n;

// deterministic jagged edge for torn paper (clip-path polygon in %)
const torn = (seed: number, teeth = 26, depth = 2.4) => {
  const r = (i: number) => {
    const x = Math.sin(seed * 97.13 + i * 12.9898) * 43758.5453;
    return x - Math.floor(x);
  };
  const pts: string[] = [];
  for (let i = 0; i <= teeth; i++) pts.push(`${(i / teeth) * 100}% ${r(i) * depth}%`);
  for (let i = 0; i <= 6; i++) pts.push(`${100 - r(i + 50) * 1.2}% ${(i / 6) * 100}%`);
  for (let i = teeth; i >= 0; i--) pts.push(`${(i / teeth) * 100}% ${100 - r(i + 100) * depth}%`);
  for (let i = 6; i >= 0; i--) pts.push(`${r(i + 150) * 1.2}% ${(i / 6) * 100}%`);
  return `polygon(${pts.join(",")})`;
};

export const Paper: React.FC<{ color?: string; seed?: number; rot?: number; style?: React.CSSProperties; tape?: boolean; children?: React.ReactNode }> = ({
  color = "#FFFDF7",
  seed = 1,
  rot = 0,
  style,
  tape,
  children,
}) => (
  <div style={{ position: "relative", transform: `rotate(${rot}deg)`, filter: "drop-shadow(0 8px 10px rgba(0,0,0,0.22))", ...style }}>
    <div style={{ background: color, clipPath: torn(seed), padding: "26px 40px 30px", position: "relative" }}>
      <div style={{ position: "absolute", inset: 0, opacity: 0.18, backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.05) 0 1px, transparent 1px 4px)" }} />
      <div style={{ position: "relative" }}>{children}</div>
    </div>
    {tape && (
      <>
        <div style={{ position: "absolute", top: -14, left: -18, width: 110, height: 34, background: "rgba(245,230,180,0.75)", transform: "rotate(-28deg)" }} />
        <div style={{ position: "absolute", top: -14, right: -18, width: 110, height: 34, background: "rgba(245,230,180,0.75)", transform: "rotate(24deg)" }} />
      </>
    )}
  </div>
);

// ---------------------------------------------------------------- overlays
// "strip": a torn paper label that drops in (stop-motion), optional red marker cross / ring
export const Strip: React.FC<{ o: Pill & Record<string, any> }> = ({ o }) => {
  const f0 = useCurrentFrame();
  const f = step(f0);
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const k = spring({ frame: f, fps, config: { damping: 11, stiffness: 220, mass: 0.6 } });
  const exit = interpolate(f0, [dur - 6, dur], [1, 0], clamp01);
  const crossF = o.cross !== undefined ? Math.round((o.cross - o.in) * fps) : null;
  const cross = crossF === null ? 0 : interpolate(f0, [crossF, crossF + 8], [0, 1], clamp01);
  const text = o.parts.map(([t]: [string, number]) => t).join("");
  const big = o.big;
  const pos: React.CSSProperties =
    o.side === "l" ? { left: 50 } : o.side === "r" ? { right: 50 } : { left: 0, right: 0, display: "flex", justifyContent: "center" };
  return (
    <div style={{ position: "absolute", top: o.top ?? 200, ...pos, opacity: exit }}>
      <div style={{ transform: `translateY(${(1 - k) * -90}px) scale(${0.8 + 0.2 * k})` }}>
        <Paper color={o.paper ?? "#FFFDF7"} seed={o.seed ?? text.length} rot={o.rot ?? (text.length % 2 ? -2.5 : 2)} tape={o.tape}>
          {o.label && <div style={{ fontFamily: FONT_HAND, fontWeight: 700, fontSize: 44, color: "#6B5A4A", marginBottom: 2 }}>{o.label}</div>}
          <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: o.size ?? (big ? 96 : 62), letterSpacing: big ? 2 : 0, color: o.ink ?? "#1F1B18", lineHeight: 1.05, position: "relative", maxWidth: o.side ? 520 : 900, whiteSpace: o.side || o.wrap ? "normal" : "nowrap", textAlign: o.side ? "left" : "center" }}>
            {o.parts.map(([w, hl]: [string, number], i: number) => (
              <span key={i} style={{ color: hl ? T.primary : undefined, backgroundImage: hl ? "linear-gradient(transparent 62%, rgba(244,200,90,0.75) 62%)" : undefined }}>{w}</span>
            ))}
            {crossF !== null && (
              <svg viewBox="0 0 100 40" preserveAspectRatio="none" style={{ position: "absolute", left: -10, top: -6, width: "calc(100% + 20px)", height: "calc(100% + 12px)", overflow: "visible" }}>
                <path d="M2 30 L98 8" stroke="#E5484D" strokeWidth={4} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - cross} vectorEffect="non-scaling-stroke" style={{ strokeWidth: 10 }} />
              </svg>
            )}
          </div>
        </Paper>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- collage scenes (full frame)
const BG = "#F3EADB";
const KRAFT = "#D9B98C";

const Sticker: React.FC<{ children: React.ReactNode; x: number; y: number; k: number; rot?: number; s?: number }> = ({ children, x, y, k, rot = 0, s = 1 }) => (
  <g transform={`translate(${x} ${y + (1 - k) * -160}) rotate(${rot * k}) scale(${s * (0.7 + 0.3 * k)})`} opacity={Math.min(1, k * 2)} style={{ filter: "drop-shadow(0 10px 8px rgba(0,0,0,0.25))" }}>
    {children}
  </g>
);

// paper-cut child (flat shapes, white cut border)
const CutKid: React.FC<{ mood: "cry" | "calm" | "happy"; arms?: "up" | "down" | "head"; shirt?: string }> = ({ mood, arms = "down", shirt = "#7FB8A4" }) => {
  const W = { stroke: "#FFFFFF", strokeWidth: 10, strokeLinejoin: "round" as const };
  const arm = arms === "up" ? "M-40 -40 L-80 -120 M40 -40 L80 -120" : arms === "head" ? "M-40 -40 L-70 -110 L-40 -150 M40 -40 L70 -110 L40 -150" : "M-40 -40 L-60 30 M40 -40 L60 30";
  return (
    <g>
      <path d={arm} stroke="#F2C9A6" strokeWidth={26} strokeLinecap="round" />
      <path d="M-55 -60 Q0 -80 55 -60 L60 80 L-60 80 Z" fill={shirt} {...W} />
      <path d="M-40 80 L-40 170 M40 80 L40 170" stroke="#3E5C76" strokeWidth={30} strokeLinecap="round" />
      <circle cx={0} cy={-130} r={62} fill="#F2C9A6" {...W} />
      <path d="M-62 -140 Q-50 -200 0 -196 Q55 -200 62 -140 Q40 -170 0 -166 Q-38 -170 -62 -140 Z" fill="#4A3426" />
      {mood === "cry" ? (
        <>
          <path d="M-30 -132 q8 -8 16 0 M14 -132 q8 -8 16 0" stroke="#2B2B2B" strokeWidth={6} fill="none" strokeLinecap="round" />
          <path d="M-20 -95 q20 -18 40 0" stroke="#2B2B2B" strokeWidth={6} fill="none" strokeLinecap="round" />
          <path d="M-26 -120 q-6 22 0 34 q6 -12 0 -34 Z M26 -120 q-6 22 0 34 q6 -12 0 -34 Z" fill="#7FC4EA" />
        </>
      ) : (
        <>
          <circle cx={-22} cy={-135} r={6} fill="#2B2B2B" />
          <circle cx={22} cy={-135} r={6} fill="#2B2B2B" />
          <path d={mood === "happy" ? "M-22 -104 q22 20 44 0" : "M-18 -104 h36"} stroke="#2B2B2B" strokeWidth={6} fill="none" strokeLinecap="round" />
        </>
      )}
    </g>
  );
};

const Word: React.FC<{ text: string; x: number; y: number; k: number; rot?: number; color?: string; size?: number }> = ({ text, x, y, k, rot = 0, color = "#FFFDF7", size = 64 }) => (
  <foreignObject x={x - 300} y={y - 70} width={600} height={160} style={{ overflow: "visible" }}>
    <div style={{ display: "flex", justifyContent: "center", opacity: Math.min(1, k * 2), transform: `translateY(${(1 - k) * -80}px) rotate(${rot}deg)` }}>
      <Paper color={color} seed={text.length * 3} rot={0}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: size, color: "#1F1B18", whiteSpace: "nowrap" }}>{text}</div>
      </Paper>
    </div>
  </foreignObject>
);

export const CollageScene: React.FC<{ f: number; p: Record<string, any>; startT: number }> = ({ f: f0, p, startT }) => {
  const { fps } = useVideoConfig();
  const f = step(f0);
  const t = startT + f / fps;
  const at = (x: number) => spring({ frame: Math.round((t - x) * fps), fps, config: { damping: 11, stiffness: 200, mass: 0.6 } }) * (t >= x ? 1 : 0);
  const wob = (i: number) => Math.sin(step(f0, 6) / 6 + i) * 2;
  let body: React.ReactNode = null;
  const a = p.at ?? {};
  if (p.scene === "bath") {
    body = (
      <>
        <Sticker x={580} y={1300} k={at(a.tub)} rot={-2} s={1.2}>
          <path d="M-380 -60 h760 q0 260 -220 260 h-320 q-220 0 -220 -260 Z" fill="#FFFFFF" stroke="#9BC7E3" strokeWidth={12} />
          <path d="M-300 200 l-20 70 M300 200 l20 70" stroke="#8C97A3" strokeWidth={18} strokeLinecap="round" />
          {[0, 1, 2, 3, 4].map((i) => (
            <circle key={i} cx={-250 + i * 120} cy={-80 - (i % 2) * 30} r={44 + (i % 3) * 10} fill="#EAF4FB" stroke="#FFFFFF" strokeWidth={6} />
          ))}
        </Sticker>
        <Sticker x={650} y={1010} k={at(a.kid)} rot={3} s={1.6}>
          <CutKid mood="cry" arms={t >= (a.run ?? 99) ? "up" : "head"} />
        </Sticker>
        <Sticker x={800} y={520} k={at(a.shower)} rot={-6} s={1.4}>
          <path d="M0 -300 v180 q0 40 -40 60 h-120 q-40 0 -40 40 v20 h200 z" fill="#B7C3CE" stroke="#FFFFFF" strokeWidth={10} />
          {[0, 1, 2, 3, 4].map((i) => (
            <path key={i} d={`M${-150 + i * 30} 20 q -6 ${40 + ((step(f0, 4) + i * 7) % 40)} 0 ${60 + ((step(f0, 4) + i * 11) % 50)}`} stroke="#7FC4EA" strokeWidth={8} fill="none" strokeLinecap="round" />
          ))}
        </Sticker>
        <Word text="Ağlayır" x={240} y={420} k={at(a.w1)} rot={-5 + wob(1)} color="#FFE3D6" />
        <Word text="Qaçır" x={250} y={600} k={at(a.w2)} rot={4 + wob(2)} color="#FFF4C9" />
        <Word text="Etiraz edir" x={270} y={780} k={at(a.w3)} rot={-3 + wob(3)} color="#E3F1EA" />
      </>
    );
  } else if (p.scene === "water") {
    body = (
      <>
        <Sticker x={540} y={1060} k={at(a.head)} s={1.5}>
          <circle cx={0} cy={0} r={190} fill="#F2C9A6" stroke="#FFFFFF" strokeWidth={14} />
          <path d="M-190 -20 Q-170 -240 0 -230 Q170 -240 190 -20 Q140 -140 0 -136 Q-140 -140 -190 -20 Z" fill="#4A3426" />
          <path d="M-70 10 q16 -14 32 0 M38 10 q16 -14 32 0 M-40 90 q40 -26 80 0" stroke="#2B2B2B" strokeWidth={9} fill="none" strokeLinecap="round" />
        </Sticker>
        {t >= a.stream &&
          [0, 1, 2].map((i) => (
            <Sticker key={i} x={400 + i * 140} y={560} k={at(a.stream + i * 0.12)} rot={i * 4 - 4} s={1.3}>
              <path d={`M0 -220 q-24 ${120 + ((step(f0, 4) + i * 9) % 30)} 0 ${200}`} stroke="#5EB3E6" strokeWidth={26} fill="none" strokeLinecap="round" opacity={0.9} />
            </Sticker>
          ))}
        {t >= a.drops &&
          [[-120, 60], [130, 40], [-60, 150], [90, 170], [10, 230]].map(([dx, dy], i) => (
            <Sticker key={i} x={540 + dx * 1.5} y={1060 + dy * 1.5} k={at(a.drops + i * 0.1)} s={1.4}>
              <path d="M0 -40 q-28 40 0 60 q28 -20 0 -60 Z" fill="#7FC4EA" stroke="#FFFFFF" strokeWidth={5} />
            </Sticker>
          ))}
        <Sticker x={540} y={400} k={at(a.sound)} s={1.3}>
          <path d="M-60 -80 h120 l-20 60 h-80 Z" fill="#B7C3CE" stroke="#FFFFFF" strokeWidth={8} />
          {[0, 1, 2].map((i) => {
            const r = 90 + i * 60 + ((step(f0, 3) * 2) % 60);
            return <path key={i} d={`M${-r} ${40} a${r} ${r} 0 0 0 ${2 * r} 0`} stroke="#E5484D" strokeWidth={10} fill="none" strokeLinecap="round" opacity={0.75 - i * 0.2} />;
          })}
        </Sticker>
        <Word text="Axan su" x={250} y={300} k={at(a.stream)} rot={-4} color="#E3F1EA" />
        <Word text="Damcılar" x={820} y={1420} k={at(a.drops)} rot={3} color="#FFF4C9" />
        <Word text="Duşun səsi" x={800} y={260} k={at(a.sound)} rot={4} color="#FFE3D6" />
      </>
    );
  } else if (p.scene === "steps") {
    const n = 4;
    const climb = t >= a.gradual ? Math.min(n - 1, Math.floor((t - a.gradual) / 0.55)) : t >= a.safe ? 0 : -1;
    body = (
      <>
        {Array.from({ length: n }, (_, i) => (
          <Sticker key={i} x={220 + i * 210} y={1400 - i * 170} k={at(a.steps + i * 0.15)}>
            <rect x={-110} y={-40} width={220} height={420} fill={["#CDEBDD", "#F8DCC8", "#E3DAF3", "#FFF1B8"][i]} stroke="#FFFFFF" strokeWidth={10} />
            <text x={0} y={60} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={70} fill="#1F1B18" opacity={0.75}>
              {i + 1}
            </text>
          </Sticker>
        ))}
        {climb >= 0 && (
          <g transform={`translate(${220 + climb * 210} ${1400 - climb * 170 - 250 - Math.abs(Math.sin(step(f0, 3) / 3)) * 10}) scale(1.1)`} style={{ filter: "drop-shadow(0 10px 8px rgba(0,0,0,0.25))" }}>
            <CutKid mood={climb >= n - 1 ? "happy" : "calm"} arms={climb >= n - 1 ? "up" : "down"} />
          </g>
        )}
        <Word text="Təhlükəsiz temp" x={330} y={360} k={at(a.safe)} rot={-4} color="#E3F1EA" size={58} />
        <Word text="Tədricən" x={720} y={560} k={at(a.gradual)} rot={5} color="#FFF4C9" size={84} />
      </>
    );
  }
  return (
    <div style={{ position: "absolute", inset: 0, width: 1080, height: 1920, background: BG, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(rgba(120,90,50,0.10) 1px, transparent 1px)", backgroundSize: "7px 7px" }} />
      <div style={{ position: "absolute", left: -60, top: 120, width: 700, height: 300, background: KRAFT, clipPath: torn(9, 30, 6), transform: "rotate(-8deg)", opacity: 0.55 }} />
      <div style={{ position: "absolute", right: -80, bottom: 260, width: 760, height: 340, background: "#BFD9EC", clipPath: torn(4, 30, 6), transform: "rotate(6deg)", opacity: 0.6 }} />
      <svg viewBox="0 0 1080 1920" width={1080} height={1920} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        {body}
      </svg>
    </div>
  );
};

// retro film look for a quoted line: grain + vignette + flicker (the footage is greyed in index.tsx)
export const RetroOverlay: React.FC<{ p: number }> = ({ p }) => {
  const f = useCurrentFrame();
  return (
    <div style={{ position: "absolute", inset: 0, opacity: p, pointerEvents: "none" }}>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: 0.32, mixBlendMode: "overlay" }}>
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={f % 30} />
        </filter>
        <rect width={1080} height={1920} filter="url(#grain)" />
      </svg>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(90% 70% at 50% 45%, transparent 45%, rgba(0,0,0,0.65) 100%)" }} />
      <div style={{ position: "absolute", inset: 0, background: "#000", opacity: 0.06 + 0.06 * Math.abs(Math.sin(f * 1.7)) }} />
      {[0, 1].map((i) => (
        <div key={i} style={{ position: "absolute", top: 0, bottom: 0, left: ((f * (37 + i * 23)) % 1080), width: 2, background: "rgba(255,255,255,0.25)" }} />
      ))}
    </div>
  );
};

export const PAPER: Record<string, React.FC<{ f: number; p: Record<string, any>; startT: number }>> = {
  collage: CollageScene,
};
