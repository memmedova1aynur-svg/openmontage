import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Pill, clamp01 } from "./theme";

// "kid": a small cartoon child bouncing non-stop beside the speaker (hyperactivity topics).
// Jumps with squash-and-stretch, arms up in the air, now and then a spin; motion lines under it.
// o.side "l" | "r", o.top = y of the ground line, o.size = height in px (default 260).
const PINK = "#F66CA1";
const TEAL = "#35C4CC";
const YEL = "#FFD21A";
const SKIN = "#F7C9A5";
const INK = "#2B2B3A";

export const Kid: React.FC<{ o: Pill }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const enter = spring({ frame, fps, config: { damping: 12, stiffness: 160, mass: 0.7 } });
  const exit = interpolate(frame, [dur - 10, dur], [1, 0], clamp01);
  const H = o.size ?? 260;
  const s = H / 260;
  // one jump every 0.55 s
  const ph = (frame / (fps * 0.55)) % 1;
  const air = Math.sin(ph * Math.PI); // 0 on the ground, 1 at the top
  const lift = air * 120;
  const squash = ph < 0.12 || ph > 0.9 ? 0.86 : 1 + 0.06 * air;
  const jumpNo = Math.floor(frame / (fps * 0.55));
  const spin = jumpNo % 5 === 4 ? ph * 360 : 0;
  const arm = -40 - 110 * air; // arms swing up when airborne
  const leg = 30 * air;
  const right = o.side !== "l";
  return (
    <div style={{ position: "absolute", [right ? "right" : "left"]: 40, top: (o.top ?? 1000) - H, width: H * 0.8, height: H, opacity: exit * Math.min(1, enter * 1.5), transform: `scale(${enter})`, transformOrigin: "50% 100%" }}>
      <svg width={H * 0.8} height={H} viewBox="0 0 208 260" style={{ overflow: "visible" }}>
        {/* shadow shrinks while airborne */}
        <ellipse cx={104} cy={252} rx={56 * (1 - 0.5 * air)} ry={9 * (1 - 0.5 * air)} fill="rgba(0,0,0,0.18)" />
        {/* motion lines */}
        {air > 0.4 && [0, 1, 2].map((i) => <path key={i} d={`M${74 + i * 30} ${230 - lift * 0.4} v${18 + i * 4}`} stroke={TEAL} strokeWidth={5} strokeLinecap="round" opacity={air - 0.3} />)}
        <g transform={`translate(0 ${-lift}) translate(104 240) scale(${2 - squash} ${squash}) rotate(${spin}) translate(-104 -240)`}>
          {/* legs */}
          <path d={`M92 182 L${82 - leg} ${228 - leg * 0.6}`} stroke={TEAL} strokeWidth={16} strokeLinecap="round" />
          <path d={`M116 182 L${126 + leg} ${228 - leg * 0.6}`} stroke={TEAL} strokeWidth={16} strokeLinecap="round" />
          <ellipse cx={80 - leg} cy={234 - leg * 0.6} rx={14} ry={8} fill={INK} />
          <ellipse cx={128 + leg} cy={234 - leg * 0.6} rx={14} ry={8} fill={INK} />
          {/* body */}
          <rect x={76} y={108} width={56} height={82} rx={22} fill={PINK} />
          <path d="M88 140 h32" stroke="#FFFFFF" strokeWidth={6} strokeLinecap="round" opacity={0.8} />
          {/* arms */}
          <g transform={`rotate(${arm} 82 118)`}><path d="M82 118 L44 140" stroke={SKIN} strokeWidth={13} strokeLinecap="round" /><circle cx={42} cy={141} r={9} fill={SKIN} /></g>
          <g transform={`rotate(${-arm} 126 118)`}><path d="M126 118 L164 140" stroke={SKIN} strokeWidth={13} strokeLinecap="round" /><circle cx={166} cy={141} r={9} fill={SKIN} /></g>
          {/* head */}
          <circle cx={104} cy={80} r={32} fill={SKIN} />
          <path d="M71 78 Q70 42 104 44 Q138 42 137 78 Q128 60 104 62 Q82 60 71 78 Z" fill="#6B4226" />
          
          <circle cx={93} cy={84} r={4} fill={INK} />
          <circle cx={115} cy={84} r={4} fill={INK} />
          <path d={air > 0.5 ? "M96 96 Q104 106 112 96 Z" : "M97 96 Q104 102 111 96"} fill={air > 0.5 ? INK : "none"} stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <circle cx={86} cy={94} r={5} fill={PINK} opacity={0.4} />
          <circle cx={122} cy={94} r={5} fill={PINK} opacity={0.4} />
        </g>
      </svg>
    </div>
  );
};

// ---------------------------------------------------------------- big number / word, full frame
// "bg_number": the speaker is replaced for a beat by one huge word or number on the brand colour
// (p.text, optional p.sub). It slams in, breathes, and confetti in the page colours bursts out.
export const BigNumber: React.FC<{ f: number; p: any; startT: number }> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const k = spring({ frame: f, fps, config: { damping: 9, stiffness: 220, mass: 0.6 } });
  const breathe = 1 + Math.sin(f / 6) * 0.015;
  const burst = interpolate(f, [2, 22], [0, 1], clamp01);
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: `radial-gradient(ellipse at 50% 45%, ${p.bg ?? "#1A9AA0"} 0%, ${p.bgDeep ?? "#0A4F53"} 100%)` }}>
      {Array.from({ length: 22 }).map((_, i) => {
        const a = (i / 22) * Math.PI * 2;
        const r = 120 + burst * (380 + (i % 4) * 70);
        const c = [PINK, YEL, "#FFFFFF", TEAL][i % 4];
        return <div key={i} style={{ position: "absolute", left: 540 + Math.cos(a) * r - 10, top: 880 + Math.sin(a) * r - 10, width: 20, height: i % 2 ? 20 : 12, borderRadius: i % 3 ? 4 : 10, background: c, opacity: 1 - burst * 0.6, transform: `rotate(${a * 57 + f * 8}deg)` }} />;
      })}
      <div style={{ position: "absolute", left: 0, right: 0, top: 880, transform: `translateY(-50%) scale(${(0.3 + 0.7 * k) * breathe})`, textAlign: "center", fontFamily: "Montserrat", fontWeight: 900, fontSize: p.size ?? 520, lineHeight: 1, whiteSpace: "pre-line", color: "#FFFFFF", textShadow: `0 18px 0 ${PINK}, 0 30px 60px rgba(0,0,0,0.35)` }}>
        {p.text}
      </div>
      {p.sub && <div style={{ position: "absolute", left: 0, right: 0, top: 1250, textAlign: "center", fontFamily: "Montserrat", fontWeight: 800, fontSize: 64, color: YEL, opacity: interpolate(f, [6, 14], [0, 1], clamp01) }}>{p.sub}</div>}
    </div>
  );
};

// ---------------------------------------------------------------- devices row
// "devices": real-looking screens (tv / tablet / phone) appear one by one in a centred row above
// the speaker's head as each is named (o.items: [{ type, at }], absolute times), each with a soft
// screen glow; o.top = row top, o.label under each device (optional).
const Screen: React.FC<{ type: string; k: number; t: number }> = ({ type, k, t }) => {
  const glow = 0.75 + 0.25 * Math.sin(t * 3 + type.length);
  const scr = (x: number, y: number, w: number, h: number, r: number) => (
    <>
      <defs>
        <linearGradient id={`g-${type}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#7FE3E8" />
          <stop offset="0.55" stopColor="#35C4CC" />
          <stop offset="1" stopColor="#F66CA1" />
        </linearGradient>
      </defs>
      <rect x={x} y={y} width={w} height={h} rx={r} fill={`url(#g-${type})`} opacity={glow} />
      <path d={`M${x + w * 0.1} ${y + h * 0.15} L${x + w * 0.45} ${y + h * 0.15}`} stroke="#FFFFFF" strokeWidth={6} strokeLinecap="round" opacity={0.5} />
    </>
  );
  const body = { fill: "#1E1F24", stroke: "#3A3C44", strokeWidth: 3 };
  return (
    <g transform={`scale(${k})`} opacity={Math.min(1, k * 1.4)}>
      {type === "tv" && (
        <g>
          <rect x={-120} y={-80} width={240} height={150} rx={12} {...body} />
          {scr(-110, -70, 220, 130, 6)}
          <path d="M-30 70 L-45 98 M30 70 L45 98" stroke="#3A3C44" strokeWidth={8} strokeLinecap="round" />
          <rect x={-70} y={96} width={140} height={8} rx={4} fill="#3A3C44" />
        </g>
      )}
      {type === "tablet" && (
        <g>
          <rect x={-78} y={-100} width={156} height={200} rx={18} {...body} />
          {scr(-68, -88, 136, 176, 8)}
          <circle cx={0} cy={-94} r={2.5} fill="#55575F" />
        </g>
      )}
      {type === "phone" && (
        <g>
          <rect x={-50} y={-100} width={100} height={200} rx={20} {...body} />
          {scr(-43, -90, 86, 180, 12)}
          <rect x={-14} y={-96} width={28} height={6} rx={3} fill="#1E1F24" />
        </g>
      )}
    </g>
  );
};

export const Devices: React.FC<{ o: Pill & { items?: { type: string; at: number; label?: string }[] } }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const exit = interpolate(frame, [dur - 8, dur], [1, 0], clamp01);
  const items = o.items ?? [];
  const W = 1080;
  const gap = W / (items.length + 1);
  const t = o.in + frame / fps;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: exit }}>
      {items.map((it, i) => {
        const k = spring({ frame: frame - Math.round((it.at - o.in) * fps), fps, config: { damping: 13, stiffness: 170, mass: 0.7 } });
        if (t < it.at) return null;
        const float = Math.sin(t * 1.6 + i) * 5;
        return (
          <g key={i} transform={`translate(${gap * (i + 1)} ${(o.top ?? 330) + float}) scale(${o.size ?? 1})`}>
            <Screen type={it.type} k={k} t={t} />
            {it.label && (
              <text x={0} y={140} textAnchor="middle" fontFamily="Montserrat" fontWeight={800} fontSize={38} fill="#FFFFFF" opacity={Math.min(1, k)} style={{ paintOrder: "stroke", stroke: "rgba(0,0,0,0.55)", strokeWidth: 6 }}>{it.label}</text>
            )}
          </g>
        );
      })}
    </svg>
  );
};
