// Nağıl və cizgi: sadə, sevimli (flat) obrazlar və nağıl fonları — SVG, deterministik (render = önizləmə).
// Obrazlar: tülkü (fox), dovşan (rabbit), ayı (bear), pişik (cat), uşaq (child). Hər obraz HƏR VİDEODA eyni görünür
// (ardıcıllıq — VIDEO_TYPES M12). Hərəkətlər: nəfəs, göz qırpma, danışma (ağız), əl yelləmə, tullanma, yan tərəfdən giriş.
// Vaxtlar səhnənin öz başlanğıcından saniyələrdir.
import React from "react";
import { AbsoluteFill, interpolate, spring, useVideoConfig } from "remotion";
import { FONT, T, clamp01, rgba } from "./theme";

type SceneProps = { f: number; p: Record<string, any>; startT: number };
type Act = { kind?: string; x?: number; y?: number; scale?: number; flip?: boolean; enterAt?: number; enterFrom?: "left" | "right" | "bottom" | "none";
  action?: "idle" | "wave" | "jump" | "talk"; actAt?: number; actFor?: number; talk?: [number, number][]; color?: string; shirt?: string };

const PAL: Record<string, { body: string; belly: string; dark: string; ear?: string }> = {
  fox: { body: "#E8792F", belly: "#FFF3E6", dark: "#3A2418", ear: "#2E1F17" },
  rabbit: { body: "#E9E4EE", belly: "#FFFFFF", dark: "#4A4458", ear: "#F6B8C8" },
  bear: { body: "#9B6B43", belly: "#E3C29B", dark: "#3B2618" },
  cat: { body: "#9AA3B0", belly: "#F2F2F2", dark: "#2C3038", ear: "#F3B5C0" },
  child: { body: "#F2C9A6", belly: "#F2C9A6", dark: "#3A2A22" },
};

// --- hərəkət köməkçiləri (hamısı f-dən — seek-safe)
const breathe = (f: number) => 1 + 0.018 * Math.sin(f / 9);
const blinkK = (f: number, seed: number) => { const t = (f + seed * 37) % 96; return t < 4 ? 0.12 : 1; };
const talking = (t: number, talk?: [number, number][]) => (talk ?? []).some(([a, b]) => t >= a && t <= b);

const Eyes: React.FC<{ y: number; dx: number; r: number; k: number; dark: string }> = ({ y, dx, r, k, dark }) => (
  <g>
    {[-dx, dx].map((x) => (
      <g key={x} transform={`translate(${x},${y}) scale(1,${k})`}>
        <ellipse rx={r} ry={r * 1.15} fill={dark} />
        <circle cx={r * 0.35} cy={-r * 0.4} r={r * 0.35} fill="#fff" />
      </g>
    ))}
  </g>
);

const Mouth: React.FC<{ y: number; open: number; dark: string }> = ({ y, open, dark }) => (
  open > 0.05 ? <ellipse cx={0} cy={y + 6} rx={11} ry={4 + 12 * open} fill={dark} /> :
    <path d={`M -14 ${y} Q 0 ${y + 12} 14 ${y}`} stroke={dark} strokeWidth={5} fill="none" strokeLinecap="round" />
);

// Qol çiyindən (gövdənin yuxarı hissəsi) başlayır: angle 0 — aşağı sallanır, ~150 — yuxarı qaldırılıb
const Arm: React.FC<{ side: number; angle: number; color: string; len?: number }> = ({ side, angle, color, len = 78 }) => (
  <g transform={`translate(${side * 64},${-172}) rotate(${-side * angle})`}>
    <rect x={-14} y={-6} width={28} height={len} rx={14} fill={color} />
  </g>
);

/** Bir obraz (mərkəz: ayaqların ortası). */
export const Character: React.FC<{ a: Act; f: number; fps: number }> = ({ a, f, fps }) => {
  const kind = a.kind ?? "fox";
  const pal = { ...PAL[kind] ?? PAL.fox, ...(a.color ? { body: a.color } : {}) };
  const t = f / fps;
  const seed = kind.length;
  // giriş
  const enterAt = a.enterAt ?? 0;
  const ent = a.enterFrom === "none" ? 1 : spring({ frame: f - Math.round(enterAt * fps), fps, config: { damping: 14, stiffness: 120 } });
  const from = a.enterFrom ?? "bottom";
  const ex = from === "left" ? -700 * (1 - ent) : from === "right" ? 700 * (1 - ent) : 0;
  const ey = from === "bottom" ? 500 * (1 - ent) : 0;
  // hərəkət
  const act = a.action ?? "idle";
  const actAt = a.actAt ?? enterAt + 0.6;
  const actOn = t >= actAt && t <= actAt + (a.actFor ?? 1.6);
  const lt = Math.max(0, t - actAt);
  const jump = act === "jump" && actOn ? -Math.abs(Math.sin(lt * Math.PI * 1.6)) * 90 : 0;
  const wave = act === "wave" && actOn ? 140 + 25 * Math.sin(lt * 14) : 18;
  const talk = (act === "talk" && actOn) || talking(t, a.talk) ? 0.5 + 0.5 * Math.abs(Math.sin(t * 13)) : 0;
  const b = breathe(f + seed * 11);
  const k = blinkK(f, seed);
  const sc = (a.scale ?? 1) * (a.flip ? -1 : 1);
  const head = (body: React.ReactNode, ears: React.ReactNode, face: React.ReactNode) => (
    <g transform={`translate(${(a.x ?? 540) + ex},${(a.y ?? 1300) + ey + jump}) scale(${sc},${a.scale ?? 1})`} opacity={Math.min(1, ent * 2)}>
      <ellipse cx={0} cy={6} rx={95} ry={16} fill="rgba(0,0,0,0.18)" />
      <g transform={`scale(1,${b})`}>{body}</g>
      <g transform={`translate(0,${-250 * b})`}>{ears}{face}</g>
    </g>
  );
  const bodyCommon = (shirt?: string) => (
    <g>
      <rect x={-50} y={-70} width={34} height={70} rx={17} fill={pal.dark} opacity={0.85} />
      <rect x={16} y={-70} width={34} height={70} rx={17} fill={pal.dark} opacity={0.85} />
      <ellipse cx={0} cy={-120} rx={78} ry={92} fill={shirt ?? pal.body} />
      {!shirt && <ellipse cx={0} cy={-105} rx={48} ry={62} fill={pal.belly} />}
      <Arm side={-1} angle={18} color={shirt ?? pal.body} />
      <Arm side={1} angle={wave} color={shirt ?? pal.body} />
    </g>
  );
  if (kind === "child") {
    const shirt = a.shirt ?? T.accent;
    return head(bodyCommon(shirt), (
      <g><ellipse cx={0} cy={-40} rx={88} ry={70} fill={pal.dark} /></g>
    ), (
      <g>
        <circle cx={0} cy={0} r={78} fill={pal.body} />
        <path d="M -80 -10 Q -60 -95 0 -88 Q 60 -95 80 -10 Q 40 -55 0 -50 Q -40 -55 -80 -10 Z" fill={pal.dark} />
        <Eyes y={4} dx={28} r={9} k={k} dark={pal.dark} />
        <circle cx={-46} cy={26} r={11} fill="#F4A0A0" opacity={0.6} />
        <circle cx={46} cy={26} r={11} fill="#F4A0A0" opacity={0.6} />
        <Mouth y={36} open={talk} dark={pal.dark} />
      </g>
    ));
  }
  const ears = kind === "rabbit" ? (
    <g>{[-1, 1].map((s) => <g key={s} transform={`translate(${s * 34},-70) rotate(${s * 8})`}><ellipse cx={0} cy={-70} rx={22} ry={80} fill={pal.body} /><ellipse cx={0} cy={-66} rx={11} ry={60} fill={pal.ear} /></g>)}</g>
  ) : kind === "bear" ? (
    <g>{[-1, 1].map((s) => <g key={s}><circle cx={s * 62} cy={-58} r={30} fill={pal.body} /><circle cx={s * 62} cy={-58} r={15} fill={pal.belly} /></g>)}</g>
  ) : (
    <g>{[-1, 1].map((s) => <g key={s}><path d={`M ${s * 30} -50 L ${s * 74} -128 L ${s * 82} -36 Z`} fill={pal.body} /><path d={`M ${s * 42} -56 L ${s * 70} -106 L ${s * 74} -48 Z`} fill={pal.ear ?? pal.dark} /></g>)}</g>
  );
  const face = (
    <g>
      <ellipse cx={0} cy={0} rx={kind === "fox" ? 86 : 80} ry={72} fill={pal.body} />
      {kind === "fox" && <path d="M -86 6 Q -40 70 0 52 Q 40 70 86 6 Q 50 40 0 34 Q -50 40 -86 6 Z" fill={pal.belly} />}
      {kind !== "fox" && <ellipse cx={0} cy={26} rx={44} ry={32} fill={pal.belly} />}
      <Eyes y={-8} dx={30} r={10} k={k} dark={pal.dark} />
      <ellipse cx={0} cy={16} rx={kind === "bear" ? 14 : 10} ry={8} fill={pal.dark} />
      {kind === "cat" && [-1, 1].map((s) => <g key={s}>{[0, 1].map((i) => <line key={i} x1={s * 22} y1={22 + i * 8} x2={s * 70} y2={14 + i * 16} stroke={pal.dark} strokeWidth={3} />)}</g>)}
      <circle cx={-48} cy={18} r={10} fill="#F4A0A0" opacity={0.5} />
      <circle cx={48} cy={18} r={10} fill="#F4A0A0" opacity={0.5} />
      <Mouth y={30} open={talk} dark={pal.dark} />
    </g>
  );
  const tail = kind === "fox" ? <path d="M 60 -90 Q 170 -150 150 -20 Q 120 -60 70 -60 Z" fill={pal.body} />
    : kind === "cat" ? <path d="M 60 -60 Q 150 -80 130 -190" stroke={pal.body} strokeWidth={20} fill="none" strokeLinecap="round" />
      : kind === "rabbit" ? <circle cx={72} cy={-70} r={20} fill={pal.belly} /> : null;
  return head(<g>{tail}{bodyCommon()}</g>, ears, face);
};

// --- fonlar
const Background: React.FC<{ kind: string; f: number }> = ({ kind, f }) => {
  const sky = kind === "night" ? ["#1B2142", "#3A3F78"] : kind === "house" ? ["#F6E7D3", "#EBD3B5"] : kind === "plain" ? [T.primary, T.primaryDeep] : ["#BDE4F7", "#EAF7FF"];
  return (
    <g>
      <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={sky[0]} /><stop offset="1" stopColor={sky[1]} /></linearGradient></defs>
      <rect x={0} y={0} width={1080} height={1920} fill="url(#sky)" />
      {kind === "night" && <g><circle cx={820} cy={300} r={90} fill="#FFF4C2" />{[...Array(24)].map((_, i) => <circle key={i} cx={(i * 137) % 1080} cy={80 + ((i * 89) % 600)} r={3 + (i % 3)} fill="#fff" opacity={0.5 + 0.5 * Math.sin(f / 10 + i)} />)}</g>}
      {(kind === "forest" || kind === "meadow") && <circle cx={860} cy={260} r={95} fill="#FFD866" opacity={0.95} />}
      {kind === "house" ? (
        <g><rect x={0} y={1180} width={1080} height={740} fill="#C99A6B" /><rect x={120} y={420} width={300} height={260} rx={20} fill="#9CD3EE" stroke="#fff" strokeWidth={14} /><rect x={700} y={560} width={220} height={620} rx={18} fill="#8A5A3B" /></g>
      ) : kind !== "plain" ? (
        <g>
          <ellipse cx={300} cy={1300} rx={700} ry={220} fill={kind === "night" ? "#22305A" : "#8FD18A"} />
          <ellipse cx={900} cy={1340} rx={600} ry={200} fill={kind === "night" ? "#1D2A4F" : "#7CC47A"} />
          <rect x={0} y={1300} width={1080} height={620} fill={kind === "night" ? "#1A2546" : "#6DB86C"} />
          {kind === "forest" && [80, 260, 860, 1010].map((x, i) => <g key={x} transform={`translate(${x},${1150 + (i % 2) * 40}) rotate(${Math.sin(f / 30 + i) * 1.2})`}>
            <rect x={-18} y={-40} width={36} height={190} fill="#7A5235" /><circle cx={0} cy={-120} r={120} fill={i % 2 ? "#4FA35A" : "#5BB466"} /></g>)}
          {kind === "meadow" && [...Array(14)].map((_, i) => <circle key={i} cx={40 + i * 75} cy={1420 + (i % 3) * 60} r={12} fill={["#FF8FB1", "#FFE066", "#FFFFFF"][i % 3]} />)}
        </g>
      ) : null}
    </g>
  );
};

// props: bg (forest|meadow|night|house|plain), title (nağıl mətni — danışıqdan), titleAt, chars [Act]
const TaleScene: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const chars: Act[] = p.chars ?? [];
  const tk = spring({ frame: f - Math.round((p.titleAt ?? 0.3) * fps), fps, config: { damping: 15, stiffness: 140 } });
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <Background kind={p.bg ?? "forest"} f={f} />
        {chars.map((a, i) => <Character key={i} a={a} f={f} fps={fps} />)}
      </svg>
      {p.title && (
        <div style={{ position: "absolute", top: 230, left: 80, right: 80, padding: "26px 36px", borderRadius: 30, background: "rgba(255,255,255,0.88)",
          fontFamily: FONT, fontWeight: 800, fontSize: 50, color: "#2B2B2B", textAlign: "center", opacity: tk, transform: `translateY(${(1 - tk) * -30}px)` }}>
          {p.title}
        </div>
      )}
    </AbsoluteFill>
  );
};

// props: char (Act), transparent: true — real videonun üstünə qoyulan obraz (fon yoxdur)
const TaleChar: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  // standart: sol tərəfdə, ayaqlar altyazının üstündə (y≈1330), sağda Reels düymələri olduğu üçün sol
  const a: Act = { x: 215, y: 1330, scale: 1.15, enterFrom: "left", ...(p.char ?? {}) };
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <Character a={a} f={f} fps={fps} />
      </svg>
    </AbsoluteFill>
  );
};

export const TALE: Record<string, React.FC<SceneProps>> = { tale_scene: TaleScene, tale_char: TaleChar };
export const TALE_CHARACTERS = Object.keys(PAL);
export const _unused = { rgba, interpolate, clamp01 };
