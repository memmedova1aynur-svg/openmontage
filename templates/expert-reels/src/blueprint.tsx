import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, Pill, T, clamp01, rgba } from "./theme";

// Blueprint: thin brand-blue lines draw themselves on a navy drafting grid, every block is
// held by corner brackets (a "frame"). Full 9:16 frame; everything is drawn in code.
// Scene props carry absolute times in `at` so each element lands on its spoken word.

const FPSX = 30;
const ease = Easing.out(Easing.cubic);
const prog = (t: number, at: number | undefined, d = 0.45) => (at === undefined ? 1 : ease(interpolate(t, [at, at + d], [0, 1], clamp01)));
const LINE = () => T.accent;

// ---------------------------------------------------------------- primitives
const Grid: React.FC<{ t0: number; t: number }> = ({ t0, t }) => {
  const k = prog(t, t0, 0.6);
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <pattern id="bp-minor" width={60} height={60} patternUnits="userSpaceOnUse">
          <path d="M60 0 H0 V60" fill="none" stroke={rgba(T.accent, 0.08)} strokeWidth={1.5} />
        </pattern>
        <pattern id="bp-major" width={300} height={300} patternUnits="userSpaceOnUse">
          <path d="M300 0 H0 V300" fill="none" stroke={rgba(T.accent, 0.16)} strokeWidth={2} />
        </pattern>
        <radialGradient id="bp-vig" cx="50%" cy="42%" r="75%">
          <stop offset="0%" stopColor={T.primary} stopOpacity={0} />
          <stop offset="100%" stopColor={T.primaryDeep} stopOpacity={0.85} />
        </radialGradient>
      </defs>
      <rect width={1080} height={1920} fill={T.primary} />
      <rect width={1080} height={1920} fill="url(#bp-minor)" opacity={k} />
      <rect width={1080} height={1920} fill="url(#bp-major)" opacity={k} />
      <rect width={1080} height={1920} fill="url(#bp-vig)" />
    </svg>
  );
};

// four corner brackets around a box; p draws them in
export const Brackets: React.FC<{ x: number; y: number; w: number; h: number; p: number; len?: number; color?: string; sw?: number }> = ({
  x, y, w, h, p, len = 34, color, sw = 5,
}) => {
  const c = color ?? LINE();
  const l = len * p;
  const d = `M${x} ${y + l} V${y} H${x + l} M${x + w - l} ${y} H${x + w} V${y + l} M${x + w} ${y + h - l} V${y + h} H${x + w - l} M${x + l} ${y + h} H${x} V${y + h - l}`;
  return <path d={d} fill="none" stroke={c} strokeWidth={sw} strokeLinecap="square" opacity={Math.min(1, p * 3)} />;
};

const Draw: React.FC<{ d: string; p: number; sw?: number; color?: string; fill?: string; dash?: boolean }> = ({ d, p, sw = 5, color, fill, dash }) => (
  <>
    {fill && <path d={d} fill={fill} opacity={interpolate(p, [0.6, 1], [0, 1], clamp01)} />}
    <path
      d={d}
      pathLength={1}
      fill="none"
      stroke={color ?? LINE()}
      strokeWidth={sw}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray={dash ? undefined : 1}
      strokeDashoffset={dash ? undefined : 1 - p}
      opacity={dash ? p : 1}
      style={dash ? { strokeDasharray: "14 12" } : undefined}
    />
  </>
);

const Label: React.FC<{ x: number; y: number; p: number; size?: number; weight?: number; color?: string; anchor?: "start" | "middle" | "end"; spacing?: number; children: string }> = ({
  x, y, p, size = 34, weight = 600, color = "#FFFFFF", anchor = "start", spacing = 0, children,
}) => (
  <text
    x={x}
    y={y + (1 - p) * 18}
    fontFamily={FONT}
    fontSize={size}
    fontWeight={weight}
    fill={color}
    textAnchor={anchor}
    letterSpacing={spacing}
    opacity={p}
  >
    {children}
  </text>
);

// small uppercase heading with a ruled line, top of every scene
const Heading: React.FC<{ t: number; at: number; text: string; num?: string }> = ({ t, at, text, num }) => {
  const p = prog(t, at, 0.5);
  return (
    <g>
      {num && <Label x={90} y={330} p={p} size={28} weight={500} color={T.accentSoft} spacing={6}>{num}</Label>}
      <Label x={90} y={392} p={p} size={50} weight={800} spacing={2}>{text}</Label>
      <path d={`M90 425 H${90 + 900 * p}`} stroke={rgba(T.accent, 0.6)} strokeWidth={3} />
    </g>
  );
};

// ---------------------------------------------------------------- icons (drawn in a 120x120 box)
const ICON: Record<string, string> = {
  blocks: "M10 70 h30 v30 h-30 Z M45 70 h30 v30 h-30 Z M80 70 h30 v30 h-30 Z M27 35 h30 v30 h-30 Z M62 35 h30 v30 h-30 Z M45 0 h30 v30 h-30 Z",
  frame: "M10 40 V10 H40 M80 10 H110 V40 M110 80 V110 H80 M40 110 H10 V80 M60 45 a15 15 0 1 0 0.1 0",
  box: "M15 45 L60 25 L105 45 L105 95 L60 115 L15 95 Z M15 45 L60 65 L105 45 M60 65 V115 M78 20 L90 5 L110 12",
  compass: "M60 60 m-50 0 a50 50 0 1 0 100 0 a50 50 0 1 0 -100 0 M60 25 L72 60 L60 95 L48 60 Z M60 60 l0.1 0",
  hand: "M20 85 L45 85 L70 95 Q85 98 100 88 L110 80 Q114 74 106 72 L88 78 M45 85 V60 Q60 55 75 62 L90 70 Q96 75 90 79 L70 80 M20 65 h25 v35 h-25 Z",
  star: "M60 8 L72 44 L110 46 L80 70 L91 108 L60 86 L29 108 L40 70 L10 46 L48 44 Z",
  q: "M40 42 Q40 15 62 15 Q85 15 85 38 Q85 55 62 62 V78 M62 98 v0.1",
};

const Icon: React.FC<{ name: string; x: number; y: number; s?: number; p: number }> = ({ name, x, y, s = 1, p }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <Draw d={ICON[name]} p={p} sw={5 / s} />
  </g>
);

// ---------------------------------------------------------------- scenes
type SceneProps = { f: number; p: Record<string, any>; startT: number };

// potential battery: knowledge fills it, usage stays low -> passive
const Battery: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const bat = prog(t, a.bat, 0.6);
  const fill = prog(t, a.fill, 0.9);
  const use = prog(t, a.use, 0.8);
  const st = spring({ frame: Math.round((t - (a.passive ?? 0)) * FPSX), fps: FPSX, config: { damping: 9, stiffness: 220, mass: 0.6 } });
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Heading t={t} at={startT} num="01" text="BİLİK VƏ TƏCRÜBƏ" />
      {/* battery */}
      <Draw d="M180 560 H860 V860 H180 Z M860 640 H900 V780 H860" p={bat} sw={7} />
      <rect x={200} y={580} width={640 * fill} height={260} fill={rgba(T.accent, 0.85)} />
      {[1, 2, 3, 4].map((i) => (
        <path key={i} d={`M${180 + 136 * i} 580 V840`} stroke={T.primary} strokeWidth={8} opacity={fill > i / 5 ? 1 : 0} />
      ))}
      <Label x={520} y={735} p={fill} size={64} weight={900} color={T.primary} anchor="middle">100%</Label>
      <Label x={180} y={930} p={bat} size={30} weight={500} color={T.accentSoft} spacing={4}>POTENSİAL</Label>
      {/* usage bar */}
      <Label x={180} y={1060} p={use} size={30} weight={500} color={T.accentSoft} spacing={4}>İSTİFADƏ</Label>
      <Draw d="M180 1090 H900 V1170 H180 Z" p={use} sw={5} />
      <rect x={190} y={1100} width={700 * 0.15 * use} height={60} fill={T.accentSoft} />
      <Label x={920} y={1150} p={use} size={40} weight={800} anchor="end" color="#FFFFFF">15%</Label>
      {/* stamp */}
      {a.passive !== undefined && t >= a.passive && (
        <g transform={`translate(540 1330) rotate(-6) scale(${0.6 + 0.4 * st})`} opacity={Math.min(1, st * 2)}>
          <rect x={-230} y={-70} width={460} height={130} fill="none" stroke="#FFFFFF" strokeWidth={6} />
          <Brackets x={-250} y={-90} w={500} h={170} p={1} />
          <text x={0} y={22} fontFamily={FONT} fontWeight={900} fontSize={76} fill="#FFFFFF" textAnchor="middle" letterSpacing={6}>PASSİV</text>
        </g>
      )}
    </svg>
  );
};

// little experience climbs, a lot of experience stays flat
const Compare: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const L = prog(t, a.left, 0.5);
  const R = prog(t, a.right, 0.5);
  const steps: [string, number, number][] = [
    ["öyrədir", 1180, a.s1],
    ["məhsul", 960, a.s2],
    ["qazanc", 740, a.s3],
  ];
  const cross = prog(t, a.no, 0.35);
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Heading t={t} at={startT} num="02" text="KİM NƏ EDİR?" />
      <path d="M540 480 V1420" stroke={rgba(T.accent, 0.35)} strokeWidth={3} style={{ strokeDasharray: "10 12" }} opacity={L} />
      {/* left column */}
      <Label x={290} y={540} p={L} size={30} weight={500} color={T.accentSoft} anchor="middle" spacing={3}>AZ TƏCRÜBƏ</Label>
      <Draw d="M110 1380 H480" p={L} sw={4} color={rgba(T.accent, 0.5)} />
      {steps.map(([txt, y, at], i) => {
        const k = prog(t, at, 0.45);
        const x = 150 + i * 110;
        const prev = i === 0 ? null : [150 + (i - 1) * 110, steps[i - 1][1]];
        return (
          <g key={i}>
            {prev && <Draw d={`M${prev[0] + 40} ${prev[1] - 10} L${x + 40} ${y - 10}`} p={k} sw={6} />}
            <rect x={x} y={y} width={80} height={1380 - y} fill={rgba(T.accent, 0.22 + 0.2 * i)} opacity={k} transform={`translate(0 ${(1 - k) * 40})`} />
            <Brackets x={x - 8} y={y - 8} w={96} h={1380 - y + 16} p={k} len={20} sw={4} />
            <Label x={x + 40} y={y - 40} p={k} size={36} weight={800} anchor="middle">{txt}</Label>
          </g>
        );
      })}
      {a.s3 !== undefined && <Draw d="M470 650 l26 -26 l26 26 M496 624 V720" p={prog(t, a.s3 + 0.3, 0.4)} sw={7} />}
      {/* right column */}
      <Label x={810} y={540} p={R} size={30} weight={500} color={T.accentSoft} anchor="middle" spacing={3}>ÇOX TƏCRÜBƏ</Label>
      <Draw d="M630 1380 H1000" p={R} sw={4} color={rgba(T.accent, 0.5)} />
      <rect x={660} y={760} width={300} height={620} fill={rgba(T.accent, 0.5)} opacity={R} transform={`translate(0 ${(1 - R) * 40})`} />
      <Label x={810} y={1080} p={R} size={34} weight={800} anchor="middle" color={T.primary}>bilik</Label>
      <Draw d="M660 700 H960" p={prog(t, a.flat, 0.6)} sw={6} dash />
      <Label x={810} y={670} p={prog(t, a.flat, 0.6)} size={34} weight={800} anchor="middle">passiv</Label>
      {a.no !== undefined && (
        <g opacity={cross}>
          <Draw d="M740 1180 l140 140 M880 1180 l-140 140" p={cross} sw={12} color="#FFFFFF" />
        </g>
      )}
    </svg>
  );
};

// the three missing skills, numbered rows
const Build: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const rows: [string, string, string, number][] = [
    ["01", "blocks", "Strukturlaşdırmaq", a.r1],
    ["02", "frame", "Çərçivələndirmək", a.r2],
    ["03", "box", "Məhsula çevirmək", a.r3],
  ];
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Heading t={t} at={startT} num="03" text="BİLİK VAR. ÇATIŞMAYAN:" />
      {rows.map(([n, icon, txt, at], i) => {
        const k = prog(t, at, 0.5);
        const y = 520 + i * 290;
        return (
          <g key={i} transform={`translate(${(1 - k) * 60} 0)`} opacity={Math.min(1, k * 2)}>
            <rect x={90} y={y} width={900} height={230} fill={rgba(T.primaryDeep, 0.55)} />
            <Brackets x={90} y={y} w={900} h={230} p={k} />
            <Icon name={icon} x={130} y={y + 55} p={prog(t, at === undefined ? undefined : at + 0.1, 0.7)} />
            <Label x={300} y={y + 95} p={k} size={30} weight={500} color={T.accentSoft} spacing={4}>{n}</Label>
            <Label x={300} y={y + 160} p={k} size={56} weight={800}>{txt}</Label>
          </g>
        );
      })}
    </svg>
  );
};

// direction + frame + support = successful trainer
const Formula: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const rows: [string, string, number][] = [
    ["compass", "Doğru istiqamət", a.r1],
    ["frame", "Düzgün çərçivə", a.r2],
    ["hand", "Bir az dəstək", a.r3],
  ];
  const fast = prog(t, a.fast, 0.4);
  const res = spring({ frame: Math.round((t - (a.res ?? 0)) * FPSX), fps: FPSX, config: { damping: 12, stiffness: 160, mass: 0.7 } });
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Heading t={t} at={startT} num="04" text="FORMUL" />
      {rows.map(([icon, txt, at], i) => {
        const k = prog(t, at, 0.45);
        const y = 500 + i * 200;
        return (
          <g key={i} opacity={Math.min(1, k * 2)}>
            {i > 0 && <Label x={150} y={y - 22} p={k} size={60} weight={300} color={T.accent} anchor="middle">+</Label>}
            <Icon name={icon} x={110} y={y} s={0.68} p={prog(t, at, 0.7)} />
            <Brackets x={96} y={y - 14} w={110} h={110} p={k} len={18} sw={4} />
            <Label x={250} y={y + 62} p={k} size={56} weight={700}>{txt}</Label>
          </g>
        );
      })}
      <Draw d="M90 1130 H990" p={fast} sw={4} />
      <Draw d="M90 1150 H990" p={fast} sw={4} />
      <Label x={990} y={1110} p={fast} size={30} weight={500} color={T.accentSoft} anchor="end" spacing={3}>ÇOX QISA MÜDDƏTDƏ</Label>
      {a.res !== undefined && t >= a.res && (
        <g transform={`translate(540 1300) scale(${0.7 + 0.3 * res})`} opacity={Math.min(1, res * 2)}>
          <rect x={-430} y={-95} width={860} height={170} fill={T.accent} />
          <Brackets x={-455} y={-120} w={910} h={220} p={1} color="#FFFFFF" />
          <Icon name="star" x={-400} y={-70} s={1} p={prog(t, a.res + 0.1, 0.5)} />
          <text x={50} y={20} fontFamily={FONT} fontWeight={900} fontSize={66} fill={T.primary} textAnchor="middle" letterSpacing={1}>UĞURLU TƏLİMÇİ</text>
        </g>
      )}
    </svg>
  );
};

// three questions the consultation answers; the last is the main one
const Questions: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const qs: [string, string, number][] = [
    ["Təlimçilik üçün", "uyğunsunuzmu?", a.q1],
    ["Təcrübəni təlimə çevirmək", "mümkündürmü?", a.q2],
    ["Gəlir gətirən fəaliyyətə", "çevirmək olarmı?", a.q3],
  ];
  const main = prog(t, a.main, 0.4);
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Heading t={t} at={startT} num="05" text="KONSULTASİYADA" />
      {qs.map(([l1, l2, at], i) => {
        const k = prog(t, at, 0.5);
        const y = 510 + i * 300;
        const hot = i === 2 ? main : 0;
        return (
          <g key={i} transform={`translate(0 ${(1 - k) * 50})`} opacity={Math.min(1, k * 2)}>
            <rect x={90} y={y} width={900} height={240} fill={hot > 0 ? rgba(T.accent, 0.18 * hot) : rgba(T.primaryDeep, 0.55)} />
            <Brackets x={90} y={y} w={900} h={240} p={k} />
            <Icon name="q" x={115} y={y + 60} s={1} p={prog(t, at === undefined ? undefined : at + 0.1, 0.6)} />
            <Label x={260} y={y + 105} p={k} size={44} weight={600}>{l1}</Label>
            <Label x={260} y={y + 170} p={k} size={52} weight={800} color={T.accent}>{l2}</Label>
            {i === 2 && a.main !== undefined && (
              <g opacity={main}>
                <rect x={700} y={y - 26} width={250} height={52} fill={T.accent} />
                <text x={825} y={y + 12} fontFamily={FONT} fontWeight={800} fontSize={28} fill={T.primary} textAnchor="middle" letterSpacing={3}>ƏN ƏSASI</text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
};

const wrap = (S: React.FC<SceneProps>): React.FC<SceneProps> => (props) => (
  <div style={{ position: "absolute", inset: 0 }}>
    <Grid t0={props.startT} t={props.startT + props.f / FPSX} />
    <S {...props} />
  </div>
);

export const BLUEPRINT: Record<string, React.FC<SceneProps>> = {
  bp_battery: wrap(Battery),
  bp_compare: wrap(Compare),
  bp_build: wrap(Build),
  bp_formula: wrap(Formula),
  bp_questions: wrap(Questions),
};

// ---------------------------------------------------------------- overlays on the speaker
// "note": a framed label. Without `point` it is a centred title row at `top`; with `point`
// ([x, y] on the speaker) it sits on the left / right with a thin leader line and a dot.
export const BpNote: React.FC<{ o: Pill & { point?: [number, number]; big?: boolean } }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const k = ease(interpolate(frame, [0, 12], [0, 1], clamp01));
  const exit = interpolate(frame, [dur - 8, dur], [1, 0], clamp01);
  const text = o.parts.map(([s]) => s).join("");
  const size = o.size ?? (o.big ? 92 : o.point ? 40 : text.length > 22 ? 52 : 60);
  const strikeF = o.strike !== undefined ? Math.round((o.strike - o.in) * fps) : null;
  const strike = strikeF === null ? 0 : interpolate(frame, [strikeF, strikeF + 8], [0, 1], clamp01);
  const side = o.side ?? "l";
  const box: React.CSSProperties = o.point
    ? { position: "absolute", top: o.top ?? 900, [side === "l" ? "left" : "right"]: 40 }
    : { position: "absolute", top: o.top ?? 280, left: 0, right: 0, display: "flex", justifyContent: "center" };
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit }}>
      {o.point && (
        <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
          <NoteLeader o={o} k={k} />
        </svg>
      )}
      <div style={box}>
        <div
          style={{
            position: "relative",
            padding: o.big ? "18px 48px 24px" : o.point ? "12px 24px 15px" : "16px 34px 20px",
            background: rgba(T.primary, 0.9),
            border: `2px solid ${rgba(T.accent, 0.55)}`,
            fontFamily: FONT,
            fontWeight: o.big ? 900 : 800,
            fontSize: size,
            lineHeight: 1.1,
            letterSpacing: o.big ? 4 : 0,
            color: "#FFFFFF",
            maxWidth: o.point ? 420 : 960,
            textAlign: "center",
            transform: `translateY(${(1 - k) * 24}px)`,
            opacity: Math.min(1, k * 1.5) * (1 - 0.4 * strike),
            boxShadow: "0 14px 36px rgba(0,0,0,0.35)",
          }}
        >
          {o.label && <div style={{ fontSize: 24, fontWeight: 500, letterSpacing: 5, color: T.accent, marginBottom: 6 }}>{o.label}</div>}
          {o.parts.map(([s, hl], i) => (
            <span key={i} style={{ color: hl ? T.accent : "#FFFFFF" }}>{s}</span>
          ))}
          <CornerTicks k={k} />
          {strikeF !== null && (
            <div style={{ position: "absolute", left: 14, top: "50%", height: 8, width: `calc(${strike} * (100% - 28px))`, background: T.accent }} />
          )}
        </div>
      </div>
    </div>
  );
};

const NoteLeader: React.FC<{ o: Pill & { point?: [number, number] }; k: number }> = ({ o, k }) => {
  const [px, py] = o.point!;
  const sx = o.side === "r" ? 1040 - 200 : 40 + 200;
  const sy = (o.top ?? 900) + 70;
  const mx = sx + (px - sx) * k;
  const my = sy + (py - sy) * k;
  return (
    <g>
      <path d={`M${sx} ${sy} L${mx} ${my}`} stroke={T.accent} strokeWidth={3} />
      <circle cx={px} cy={py} r={10 * k} fill={T.accent} />
      <circle cx={px} cy={py} r={22 * k} fill="none" stroke={T.accent} strokeWidth={2} opacity={0.6} />
    </g>
  );
};

const CornerTicks: React.FC<{ k: number }> = ({ k }) => {
  const l = 22 * k;
  const c = T.accent;
  const s = (pos: React.CSSProperties, b: React.CSSProperties) => (
    <div style={{ position: "absolute", width: l, height: l, ...pos, ...b }} />
  );
  const w = `5px solid ${c}`;
  return (
    <>
      {s({ left: -10, top: -10 }, { borderLeft: w, borderTop: w })}
      {s({ right: -10, top: -10 }, { borderRight: w, borderTop: w })}
      {s({ right: -10, bottom: -10 }, { borderRight: w, borderBottom: w })}
      {s({ left: -10, bottom: -10 }, { borderLeft: w, borderBottom: w })}
    </>
  );
};

// "spark": a small burst of light-blue rays with a framed word under it
export const BpSpark: React.FC<{ o: Pill & { point?: [number, number] } }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const [cx, cy] = o.point ?? [540, 420];
  const k = ease(interpolate(frame, [0, 10], [0, 1], clamp01));
  const fade = interpolate(frame, [dur - 8, dur], [1, 0], clamp01);
  const rays = 12;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: fade }}>
      {Array.from({ length: rays }).map((_, i) => {
        const ang = (i / rays) * Math.PI * 2;
        const r0 = 30 + 40 * k;
        const r1 = r0 + (i % 2 ? 50 : 90) * k;
        return (
          <line key={i} x1={cx + Math.cos(ang) * r0} y1={cy + Math.sin(ang) * r0} x2={cx + Math.cos(ang) * r1} y2={cy + Math.sin(ang) * r1}
            stroke={i % 2 ? "#FFFFFF" : T.accent} strokeWidth={7} strokeLinecap="round" />
        );
      })}
      <path d={`M${cx} ${cy - 34} L${cx + 10} ${cy - 10} L${cx + 34} ${cy} L${cx + 10} ${cy + 10} L${cx} ${cy + 34} L${cx - 10} ${cy + 10} L${cx - 34} ${cy} L${cx - 10} ${cy - 10} Z`}
        fill="#FFFFFF" transform={`rotate(${frame * 2} ${cx} ${cy}) scale(1)`} style={{ transformOrigin: `${cx}px ${cy}px` }} opacity={k} />
    </svg>
  );
};
