import React from "react";
import { OffthreadVideo, interpolate, staticFile } from "remotion";
import { E, FONT, FONT_HAND, T, clamp01, rgba } from "./theme";

// Rəhimə Niyazlı's own insert shots: orange single-line drawings that draw themselves on warm cream
// paper (no boxes, no glow, no bouncy easing). Lines "boil" a little (redrawn every 2 frames with a
// small seeded jitter) so they read as hand drawn. Labels are handwritten (Caveat).
//   rh_fear   - a small child cowers while a big parent figure shouts (p.at = draw start, p.label)
//   rh_bounds - two rows: "with fear" (child alone, shouting parent, X) and "with understanding and
//               respect" (parent kneels at the child's height, hands held, heart). p.at = {a, b, c}
//   rh_word   - full-frame big word on cream; p.text, p.strikeAt draws a marker line through it
type SceneProps = { f: number; p: Record<string, any>; startT: number };
const FPSX = 30;
const PAPER = "#F7E6D0";
const LINE = () => T.accent;
const DEEP = "#B8460F";

const ease = (x: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
const prog = (t: number, at: number | undefined, d = 0.7) => (at === undefined ? 1 : ease((t - at) / d));

// a stroke that draws itself in (pathLength 1) and boils slightly every 2 frames
const Line: React.FC<{ d: string; p: number; f: number; w?: number; c?: string; seed?: number; fill?: string }> = ({ d, p, f, w = 9, c, seed = 0, fill }) => {
  const k = Math.floor(f / 2) + seed * 7;
  const jx = Math.sin(k * 12.9898) * 1.6;
  const jy = Math.cos(k * 78.233) * 1.6;
  if (p <= 0) return null;
  return (
    <path d={d} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} fill={fill && p >= 1 ? fill : "none"} stroke={c ?? LINE()} strokeWidth={w}
      strokeLinecap="round" strokeLinejoin="round" transform={`translate(${jx} ${jy})`} />
  );
};

const Paper: React.FC = () => (
  <div style={{ position: "absolute", inset: 0, background: `radial-gradient(ellipse at 50% 40%, #FBF1E3 0%, ${PAPER} 70%, #F0D9BE 100%)` }} />
);

const Label: React.FC<{ x: number; y: number; p: number; size?: number; color?: string; children: React.ReactNode }> = ({ x, y, p, size = 76, color, children }) => (
  <text x={x} y={y + (1 - p) * 14} opacity={p} textAnchor="middle" fontFamily={FONT_HAND} fontWeight={700} fontSize={size} fill={color ?? DEEP}>
    {children}
  </text>
);

// a person drawn as a few strokes around (x, y) = feet; s = scale; arms: "down" | "up" (cowering) | "shout" | "hold"
const Person: React.FC<{ x: number; y: number; s: number; p: number; f: number; arms?: string; kneel?: boolean; seed?: number; flip?: boolean }> = ({ x, y, s, p, f, arms = "down", kneel, seed = 0, flip }) => {
  const st = (i: number) => interpolate(p, [i * 0.18, i * 0.18 + 0.4], [0, 1], clamp01);
  const leg = kneel ? "M-18 0 L-22 -40 L-50 -40 M18 0 L22 -60" : "M-18 0 L-14 70 M18 0 L14 70";
  const armD =
    arms === "up" ? "M-30 -112 Q-70 -170 -18 -214 M30 -112 Q70 -170 18 -214" :
    arms === "shout" ? "M-30 -112 L-62 -40 M30 -112 L96 -150" :
    arms === "hold" ? "M-30 -112 L-62 -40 M30 -112 Q70 -70 104 -40" :
    "M-30 -112 L-58 -30 M30 -112 L58 -30";
  return (
    <g transform={`translate(${x} ${y - (kneel ? 0 : 70 * s)}) scale(${flip ? -s : s} ${s})`}>
      <Line f={f} seed={seed} p={st(0)} w={9 / s} d="M0 -172 m-38 0 a38 38 0 1 0 76 0 a38 38 0 1 0 -76 0" fill={rgba(T.accent, 0.12)} />
      <Line f={f} seed={seed + 1} p={st(1)} w={9 / s} d="M-30 -122 Q-44 -40 -36 0 L36 0 Q44 -40 30 -122 Q0 -136 -30 -122 Z" fill={rgba(T.accent, 0.22)} />
      <Line f={f} seed={seed + 2} p={st(2)} w={9 / s} d={armD} />
      <Line f={f} seed={seed + 3} p={st(3)} w={9 / s} d={leg} />
    </g>
  );
};

const Fear: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? startT;
  const shake = Math.sin(f * 1.7) * 3 * prog(t, a + 0.8, 0.3);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Paper />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <Person x={690} y={1380} s={2.5} p={prog(t, a, 1.0)} f={f} arms="shout" seed={3} />
        {/* the shout: a jagged bubble with "!" */}
        <Line f={f} seed={9} p={prog(t, a + 0.55, 0.5)} w={8} d="M700 330 L770 300 L820 260 L870 305 L950 280 L950 350 L1010 390 L940 420 L940 490 L860 460 L800 510 L780 450 L700 460 L740 400 Z" />
        <text x={848} y={435} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={110} fill={T.accent} opacity={prog(t, a + 0.85, 0.3)}>!</text>
        <g transform={`translate(${shake} 0)`}>
          <Person x={290} y={1380} s={1.45} p={prog(t, a + 0.3, 0.9)} f={f} arms="up" seed={6} />
          {[0, 1, 2].map((i) => (
            <Line key={i} f={f} seed={12 + i} p={prog(t, a + 0.9 + i * 0.08, 0.3)} w={6} d={`M${150 - i * 6} ${930 + i * 50} q-30 -12 -48 0`} />
          ))}
        </g>
        <Label x={540} y={1520} p={prog(t, a + 0.6, 0.5)} size={92}>{p.label ?? ""}</Label>
      </svg>
    </div>
  );
};

const Bounds: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const A = prog(t, a.a, 0.9);
  const B = prog(t, a.b, 0.9);
  const C = prog(t, a.c, 0.6);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Paper />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <Label x={540} y={290} p={prog(t, startT, 0.5)} size={96}>{p.title ?? ""}</Label>
        {/* row 1: with fear */}
        <g opacity={1 - 0.45 * B}>
          <Label x={230} y={470} p={A} size={84}>{p.left ?? ""}</Label>
          <Person x={250} y={960} s={1.1} p={A} f={f} arms="up" seed={2} />
          <Person x={540} y={960} s={1.7} p={A} f={f} arms="shout" seed={5} />
          <Line f={f} seed={8} p={prog(t, (a.a ?? 0) + 0.5, 0.4)} w={7} d="M720 500 L780 465 L830 500 L890 475 L880 545 L820 570 L760 545 Z" />
          <Line f={f} seed={11} p={prog(t, (a.a ?? 0) + 0.7, 0.4)} w={14} c={DEEP} d="M840 690 L970 820 M970 690 L840 820" />
        </g>
        <Line f={f} seed={14} p={B} w={5} c={rgba(T.accent, 0.5)} d="M120 1010 H960" />
        {/* row 2: understanding and respect */}
        <Label x={540} y={1100} p={B} size={84}>{p.right ?? ""}</Label>
        <Person x={400} y={1560} s={1.6} p={B} f={f} arms="hold" kneel seed={17} />
        <Person x={610} y={1560} s={1.1} p={B} f={f} arms="down" seed={21} flip />
        <g transform="translate(20 -50)"><Line f={f} seed={23} p={C} w={10} c={DEEP} d="M490 1250 C470 1215 420 1225 430 1265 C440 1295 490 1320 490 1320 C490 1320 540 1295 550 1265 C560 1225 510 1215 490 1250 Z" fill={rgba(T.accent, 0.55)} /></g>
        <Line f={f} seed={26} p={prog(t, (a.b ?? 0) + 0.6, 0.4)} w={14} c={DEEP} d="M820 1330 L880 1395 L1000 1250" />
        <Label x={880} y={1490} p={C} size={66}>{p.sub ?? ""}</Label>
      </svg>
    </div>
  );
};

// rh_word: the speaker stays behind the type, blurred and warmed to the brand orange; the words
// come in one by one in cream, then at p.strikeAt a marker line crosses them out and a handwritten
// p.sub (e.g. "deyil") lands under them.
const Word: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const words: string[] = String(p.text ?? "").split(/\s+/);
  const st = prog(t, p.strikeAt, 0.3);
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: -60, filter: "blur(26px) saturate(1.1)", transform: "scale(1.1)" }}>
        <OffthreadVideo src={staticFile(E.video ?? "base.mp4")} muted style={{ width: 1200, height: 2040 }} />
      </div>
      <div style={{ position: "absolute", inset: 0, background: `linear-gradient(180deg, ${rgba(T.accent, 0.72)} 0%, ${rgba(DEEP, 0.82)} 100%)` }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 640, textAlign: "center" }}>
        {words.map((w, i) => {
          const k = ease((t - startT - i * 0.22) / 0.3);
          return (
            <div key={i} style={{ fontFamily: FONT, fontWeight: 900, fontSize: p.size ?? 190, lineHeight: 1.0, letterSpacing: -3, color: PAPER,
              opacity: k * (1 - 0.35 * st), transform: `translateY(${(1 - k) * 40}px)` }}>{w}</div>
          );
        })}
      </div>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <Line f={f} p={st} w={22} c={PAPER} d="M150 870 C380 820 700 850 930 790" />
        <Label x={540} y={1180} p={st} size={130} color={PAPER}>{p.sub ?? ""}</Label>
      </svg>
    </div>
  );
};

export const RAHIME: Record<string, React.FC<SceneProps>> = { rh_fear: Fear, rh_bounds: Bounds, rh_word: Word };
