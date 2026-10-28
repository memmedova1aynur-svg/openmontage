import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, Pill, T, clamp01, isPale, rgba } from "./theme";
import { KidsStage } from "./studio";

// Light paper scenes (white sheet, navy ink, brand-blue accents) in two families:
//  - "route": a road map whose stops pin in one by one (consultation / process ads)
//  - "exam":  an answer sheet whose bubbles fill on the spoken word (study / exam topics)
// Plus overlays for the speaker: "ticket" (white card), "marker" (highlighter type,
// optional chat-bubble form) and "callcard" (closing contact card).

const FPSX = 30;
const ease = Easing.out(Easing.cubic);
const prog = (t: number, at: number | undefined, d = 0.45) => (at === undefined ? 1 : ease(interpolate(t, [at, at + d], [0, 1], clamp01)));
const INK = () => T.primary;
const PAPER = "#FAFAF7";

type SceneProps = { f: number; p: Record<string, any>; startT: number };

const Sheet: React.FC<{ kind: "route" | "exam" }> = ({ kind }) => (
  <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
    <defs>
      <pattern id={`sh-${kind}`} width={kind === "exam" ? 54 : 1080} height={54} patternUnits="userSpaceOnUse">
        {kind === "exam" ? (
          <path d="M54 0 H0 V54" fill="none" stroke={rgba(T.accentSoft, 0.22)} strokeWidth={1.5} />
        ) : (
          <circle cx={27} cy={27} r={2} fill={rgba(T.accentSoft, 0.35)} />
        )}
      </pattern>
      <pattern id="sh-dots" width={54} height={54} patternUnits="userSpaceOnUse">
        <circle cx={27} cy={27} r={2.2} fill={rgba(T.accentSoft, 0.3)} />
      </pattern>
    </defs>
    <rect width={1080} height={1920} fill={PAPER} />
    <rect width={1080} height={1920} fill={kind === "exam" ? `url(#sh-${kind})` : "url(#sh-dots)"} />
    {kind === "exam" && <path d="M150 0 V1920" stroke={rgba(T.accentSoft, 0.55)} strokeWidth={3} />}
  </svg>
);

const Txt: React.FC<{ x: number; y: number; p: number; size?: number; weight?: number; color?: string; anchor?: "start" | "middle" | "end"; spacing?: number; children: React.ReactNode }> = ({
  x, y, p, size = 40, weight = 700, color, anchor = "start", spacing = 0, children,
}) => (
  <text x={x} y={y + (1 - p) * 16} fontFamily={FONT} fontSize={size} fontWeight={weight} fill={color ?? INK()} textAnchor={anchor} letterSpacing={spacing} opacity={p}>
    {children}
  </text>
);

const Line: React.FC<{ d: string; p: number; sw?: number; color?: string; dash?: string }> = ({ d, p, sw = 6, color, dash }) =>
  dash ? (
    <g>
      <defs>
        <mask id={`m-${d.length}-${Math.round(sw)}`}>
          <path d={d} pathLength={1} fill="none" stroke="#fff" strokeWidth={sw + 4} strokeDasharray={1} strokeDashoffset={1 - p} />
        </mask>
      </defs>
      <path d={d} fill="none" stroke={color ?? INK()} strokeWidth={sw} strokeLinecap="round" style={{ strokeDasharray: dash }} mask={`url(#m-${d.length}-${Math.round(sw)})`} />
    </g>
  ) : (
    <path d={d} pathLength={1} fill="none" stroke={color ?? INK()} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={1} strokeDashoffset={1 - p} />
  );

const Title: React.FC<{ t: number; at: number; small?: string; text: string }> = ({ t, at, small, text }) => {
  const p = prog(t, at, 0.5);
  return (
    <g>
      {small && (
        <g opacity={p}>
          <rect x={90} y={268} width={small.length * 19 + 44} height={50} rx={25} fill={T.accent} />
          <Txt x={112} y={303} p={1} size={26} weight={800} spacing={3}>{small}</Txt>
        </g>
      )}
      <Txt x={90} y={400} p={p} size={62} weight={900}>{text}</Txt>
    </g>
  );
};

// ---------------------------------------------------------------- route (road map)
const PIN = (x: number, y: number, k: number, n: string) => (
  <g transform={`translate(${x} ${y}) scale(${k})`}>
    <circle r={44} fill={INK()} />
    <circle r={44} fill="none" stroke={T.accent} strokeWidth={8} opacity={0.9} />
    <text y={15} fontFamily={FONT} fontWeight={900} fontSize={42} fill="#FFFFFF" textAnchor="middle">{n}</text>
  </g>
);

// a little bunny that hops along the road as it is drawn (p.bunny)
const bezier = (p0: number[], p1: number[], p2: number[], p3: number[], u: number) => {
  const v = 1 - u;
  return [0, 1].map((k) => v * v * v * p0[k] + 3 * v * v * u * p1[k] + 3 * v * u * u * p2[k] + u * u * u * p3[k]);
};
const Bunny: React.FC<{ x: number; y: number; flip: boolean; hop: number }> = ({ x, y, flip, hop }) => (
  <g transform={`translate(${x} ${y - 70 - hop}) scale(${flip ? -1.5 : 1.5} 1.5)`}>
    <ellipse cx={0} cy={58 + hop} rx={34 - hop * 0.4} ry={8} fill="rgba(0,0,0,0.12)" />
    <ellipse cx={-6} cy={14} rx={34} ry={28} fill="#FFFFFF" stroke={INK()} strokeWidth={5} />
    <circle cx={-40} cy={10} r={9} fill="#FFFFFF" stroke={INK()} strokeWidth={4} />
    <ellipse cx={14} cy={-34} rx={8} ry={26} transform="rotate(-12 14 -34)" fill="#FFFFFF" stroke={INK()} strokeWidth={5} />
    <ellipse cx={14} cy={-34} rx={3.5} ry={17} transform="rotate(-12 14 -34)" fill="#F66CA1" />
    <ellipse cx={30} cy={-30} rx={8} ry={26} transform="rotate(14 30 -30)" fill="#FFFFFF" stroke={INK()} strokeWidth={5} />
    <ellipse cx={30} cy={-30} rx={3.5} ry={17} transform="rotate(14 30 -30)" fill="#F66CA1" />
    <circle cx={24} cy={-2} r={20} fill="#FFFFFF" stroke={INK()} strokeWidth={5} />
    <circle cx={31} cy={-6} r={3.5} fill={INK()} />
    <circle cx={42} cy={0} r={3.5} fill="#F66CA1" />
    <ellipse cx={-14} cy={40} rx={12} ry={6} fill="#FFFFFF" stroke={INK()} strokeWidth={4} />
    <ellipse cx={14} cy={40} rx={12} ry={6} fill="#FFFFFF" stroke={INK()} strokeWidth={4} />
  </g>
);

const Route: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const stops: { x: number; y: number; l1: string; l2?: string; at: number }[] = p.stops;
  // serpentine road through the stops
  const d = stops.reduce((acc, s, i) => {
    if (i === 0) return `M${s.x} ${s.y}`;
    const pr = stops[i - 1];
    const my = (pr.y + s.y) / 2;
    return `${acc} C${pr.x} ${my} ${s.x} ${my} ${s.x} ${s.y}`;
  }, "");
  const last = stops[stops.length - 1].at;
  const road = interpolate(t, [stops[0].at, last], [0.02, 1], clamp01);
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Title t={t} at={startT} small={p.small} text={p.title} />
      <path d={d} fill="none" stroke={rgba(T.accentSoft, 0.35)} strokeWidth={34} strokeLinecap="round" opacity={prog(t, startT, 0.5)} />
      <Line d={d} p={road} sw={8} dash="22 18" />
      {stops.map((s, i) => {
        const k = spring({ frame: Math.round((t - s.at) * FPSX), fps: FPSX, config: { damping: 11, stiffness: 200, mass: 0.6 } });
        if (t < s.at) return null;
        const right = s.x < 540;
        const tx = right ? s.x + 80 : s.x - 80;
        return (
          <g key={i}>
            {PIN(s.x, s.y, k, String(i + 1))}
            <Txt x={tx} y={s.y - (s.l2 ? 6 : -14)} p={Math.min(1, k)} size={44} weight={800} anchor={right ? "start" : "end"}>{s.l1}</Txt>
            {s.l2 && <Txt x={tx} y={s.y + 46} p={Math.min(1, k)} size={36} weight={500} anchor={right ? "start" : "end"}>{s.l2}</Txt>}
          </g>
        );
      })}
      {p.bunny && (() => {
        // points along the road, by arc length, so the bunny keeps an even pace
        const pts: number[][] = [];
        stops.forEach((st, i) => {
          if (i === 0) return;
          const pr = stops[i - 1];
          const my = (pr.y + st.y) / 2;
          for (let j = 0; j <= 40; j++) pts.push(bezier([pr.x, pr.y], [pr.x, my], [st.x, my], [st.x, st.y], j / 40));
        });
        const len = [0];
        for (let i = 1; i < pts.length; i++) len.push(len[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
        const want = road * len[len.length - 1];
        let i = len.findIndex((l) => l >= want);
        if (i < 1) i = 1;
        const u = (want - len[i - 1]) / Math.max(1e-6, len[i] - len[i - 1]);
        const x = pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * u;
        const y = pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * u;
        const moving = road < 0.999;
        const hop = moving ? Math.abs(Math.sin(t * 7)) * 26 : Math.abs(Math.sin(t * 3)) * 8;
        return <g opacity={prog(t, startT, 0.4)}><Bunny x={x} y={y} flip={pts[i][0] < pts[i - 1][0]} hop={hop} /></g>;
      })()}
      {a.flag !== undefined && t >= a.flag && (
        <g transform={`translate(${stops[stops.length - 1].x + 10} ${stops[stops.length - 1].y - 150})`} opacity={prog(t, a.flag, 0.3)}>
          <path d="M0 0 V110" stroke={INK()} strokeWidth={7} />
          <path d={`M0 0 L${80 * prog(t, a.flag, 0.5)} 22 L0 46 Z`} fill={T.accent} stroke={INK()} strokeWidth={4} />
        </g>
      )}
    </svg>
  );
};

// ---------------------------------------------------------------- answers (icon rows)
const ICONS: Record<string, string> = {
  check: "M15 50 L42 77 L95 22",
  flag: "M25 10 V105 M25 14 L95 30 L25 58",
  coin: "M55 55 m-42 0 a42 42 0 1 0 84 0 a42 42 0 1 0 -84 0 M55 30 V80 M40 42 Q55 30 70 42 Q55 56 40 66 Q55 80 70 68",
  chart: "M10 100 H105 M20 100 V70 M45 100 V55 M70 100 V38 M95 100 V18",
  steps: "M20 95 h30 v-25 h30 v-25 h30 v-25",
};

const Answers: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const rows: { icon: string; text: string; at: number }[] = p.rows;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Title t={t} at={startT} small={p.small} text={p.title} />
      {rows.map((r, i) => {
        const k = prog(t, r.at, 0.4);
        const y = 480 + i * 175;
        return (
          <g key={i} transform={`translate(${(1 - k) * -40} 0)`} opacity={k}>
            <rect x={90} y={y} width={900} height={140} rx={30} fill="#FFFFFF" stroke={rgba(T.primary, 0.12)} strokeWidth={2} />
            <rect x={90} y={y} width={140} height={140} rx={30} fill={T.accent} />
            <g transform={`translate(${105} ${y + 13}) scale(1)`}>
              <Line d={ICONS[r.icon]} p={prog(t, r.at + 0.1, 0.6)} sw={8} />
            </g>
            <Txt x={265} y={y + 85} p={1} size={r.text.length > 26 ? 40 : 46} weight={800}>{r.text}</Txt>
          </g>
        );
      })}
    </svg>
  );
};

// ---------------------------------------------------------------- exam answer sheet
// rows of A-B-C-D bubbles; on its word each row fills its answer (or gets a cross)
const Exam: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const rows: { text: string; at: number; mark?: number }[] = p.rows;
  const cross = !!p.cross;
  const gap = rows.length > 4 ? 172 : 250;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <Title t={t} at={startT} small={p.small} text={p.title} />
      {rows.map((r, i) => {
        const k = prog(t, r.at, 0.35);
        const y = 500 + i * gap;
        const fill = prog(t, r.at + 0.15, 0.3);
        const mark = r.mark ?? i % 4;
        return (
          <g key={i} opacity={Math.max(0.0, k)}>
            <Txt x={180} y={y + 14} p={1} size={34} weight={800} color={T.accentSoft}>{String(i + 1).padStart(2, "0")}</Txt>
            <Txt x={250} y={y + 14} p={1} size={rows.length > 4 ? 50 : 58} weight={800}>{r.text}</Txt>
            {["A", "B", "C", "D"].map((L, j) => {
              const cx = 292 + j * 112;
              const cy = y + 82;
              const on = j === mark;
              return (
                <g key={j}>
                  <circle cx={cx} cy={cy} r={38} fill="#FFFFFF" stroke={rgba(T.primary, 0.55)} strokeWidth={3} />
                  <text x={cx} y={cy + 9} fontFamily={FONT} fontWeight={700} fontSize={30} fill={rgba(T.primary, 0.55)} textAnchor="middle">{L}</text>
                  {on && !cross && <circle cx={cx} cy={cy} r={38 * fill} fill={INK()} />}
                  {on && cross && <Line d={`M${cx - 32} ${cy - 32} L${cx + 32} ${cy + 32} M${cx + 32} ${cy - 32} L${cx - 32} ${cy + 32}`} p={fill} sw={8} />}
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
};

// hours at the desk ≠ effective learning
const NotEqual: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const L = prog(t, a.left, 0.5);
  const R = prog(t, a.right, 0.5);
  const ne = spring({ frame: Math.round((t - (a.ne ?? 0)) * FPSX), fps: FPSX, config: { damping: 10, stiffness: 220, mass: 0.6 } });
  const hand = (t - (a.left ?? startT)) * 4;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      {/* clock + book */}
      <g opacity={L} transform={`translate(300 720)`}>
        <circle r={150} fill="#FFFFFF" stroke={INK()} strokeWidth={10} />
        {Array.from({ length: 12 }).map((_, i) => {
          const an = (i / 12) * Math.PI * 2;
          return <line key={i} x1={Math.cos(an) * 120} y1={Math.sin(an) * 120} x2={Math.cos(an) * 135} y2={Math.sin(an) * 135} stroke={INK()} strokeWidth={6} />;
        })}
        <line x1={0} y1={0} x2={Math.cos(hand) * 95} y2={Math.sin(hand) * 95} stroke={INK()} strokeWidth={10} strokeLinecap="round" />
        <line x1={0} y1={0} x2={Math.cos(hand / 12 - 1.2) * 60} y2={Math.sin(hand / 12 - 1.2) * 60} stroke={T.accentSoft} strokeWidth={12} strokeLinecap="round" />
        <path d="M-150 250 Q-75 215 0 250 Q75 215 150 250 V390 Q75 355 0 390 Q-75 355 -150 390 Z M0 250 V390" fill={rgba(T.accent, 0.5)} stroke={INK()} strokeWidth={8} strokeLinejoin="round" />
      </g>
      <Txt x={300} y={1240} p={L} size={44} weight={800} anchor="middle">Saatlarla kitab</Txt>
      <g transform={`translate(540 980) scale(${Math.max(0, ne)})`}>
        <text y={40} fontFamily={FONT} fontWeight={900} fontSize={170} fill={INK()} textAnchor="middle">≠</text>
      </g>
      {/* lightbulb */}
      <g opacity={R} transform="translate(800 760)">
        <circle r={150 * R} fill={rgba(T.accent, 0.45)} />
        <path d="M-70 10 Q-80 -110 0 -115 Q80 -110 70 10 Q50 40 45 80 H-45 Q-50 40 -70 10 Z" fill="#FFFFFF" stroke={INK()} strokeWidth={9} strokeLinejoin="round" />
        <path d="M-40 105 H40 M-30 135 H30" stroke={INK()} strokeWidth={9} strokeLinecap="round" />
        <path d="M-20 70 V20 L0 -10 L20 20 V70" fill="none" stroke={T.accentSoft} strokeWidth={6} />
      </g>
      <Txt x={800} y={1240} p={R} size={44} weight={800} anchor="middle">Effektiv öyrənmək</Txt>
    </svg>
  );
};

// skin "kids": the bright playroom (expert's page colours) instead of the paper sheet
const wrap = (kind: "route" | "exam", S: React.FC<SceneProps>): React.FC<SceneProps> => (props) => (
  <div style={{ position: "absolute", inset: 0 }}>
    {props.p.skin === "kids" ? <KidsStage t={props.startT + props.f / FPSX} blocks={false} /> : <Sheet kind={kind} />}
    <S {...props} />
  </div>
);

export const SHEET: Record<string, React.FC<SceneProps>> = {
  sh_route: wrap("route", Route),
  sh_answers: wrap("route", Answers),
  sh_exam: wrap("exam", Exam),
  sh_noteq: wrap("exam", NotEqual),
};

// ---------------------------------------------------------------- overlays
type Ov = Pill & { bubble?: boolean; tail?: "l" | "r"; lines?: string[]; tag?: string; maxw?: number };

const rowBox = (o: Ov): React.CSSProperties =>
  o.side === "l" ? { position: "absolute", top: o.top ?? 300, left: 50 } : o.side === "r" ? { position: "absolute", top: o.top ?? 300, right: 50 } : { position: "absolute", top: o.top ?? 300, left: 0, right: 0, display: "flex", justifyContent: "center" };

// white card, navy type, a brand-blue tab with the label
export const Ticket: React.FC<{ o: Ov }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const k = spring({ frame, fps, config: { damping: 13, stiffness: 190, mass: 0.6 } });
  const exit = interpolate(frame, [dur - 7, dur], [1, 0], clamp01);
  const chars = o.parts.map(([s]) => s).join("").length;
  const strikeF = o.strike !== undefined ? Math.round((o.strike - o.in) * fps) : null;
  const strike = strikeF === null ? 0 : interpolate(frame, [strikeF, strikeF + 8], [0, 1], clamp01);
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit }}>
      <div style={rowBox(o)}>
        <div
          style={{
            position: "relative",
            background: "#FFFFFF",
            borderRadius: 28,
            padding: o.label ? "22px 34px 24px" : "18px 32px 22px",
            maxWidth: o.side ? 520 : 940,
            boxShadow: "0 16px 40px rgba(0,0,0,0.28)",
            transform: `translateY(${(1 - k) * 40}px) scale(${0.9 + 0.1 * k})`,
            opacity: Math.min(1, k * 1.6) * (1 - 0.35 * strike),
            textAlign: o.side === "r" ? "right" : o.side === "l" ? "left" : "center",
          }}
        >
          {o.label && (
            <div style={{ position: "absolute", top: -22, left: o.side === "r" ? undefined : 30, right: o.side === "r" ? 30 : undefined, background: T.accent, color: T.primary, fontFamily: FONT, fontWeight: 800, fontSize: 24, letterSpacing: 3, padding: "6px 16px", borderRadius: 12 }}>
              {o.label}
            </div>
          )}
          <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: o.size ?? (chars > 34 ? 46 : chars > 18 ? 54 : 62), lineHeight: 1.12, color: T.primary }}>
            {o.parts.map(([s, hl], i) => (
              // a pale accent (yellow) is unreadable on the white ticket: keep the word dark and mark it underneath
              <span key={i} style={{ color: hl && !isPale(T.accentSoft) ? T.accentSoft : T.primary, backgroundImage: hl && isPale(T.accentSoft) ? `linear-gradient(${T.accent}, ${T.accent})` : undefined, backgroundSize: "100% 38%", backgroundPosition: "0 88%", backgroundRepeat: "no-repeat" }}>{s}</span>
            ))}
          </div>
          {strikeF !== null && <div style={{ position: "absolute", left: 20, top: "52%", height: 8, borderRadius: 4, width: `calc(${strike} * (100% - 40px))`, background: T.primary }} />}
        </div>
      </div>
    </div>
  );
};

// big white type; highlighted parts get a brand-blue highlighter swipe (dark type on it).
// bubble: a white chat bubble with a tail instead (quotes)
export const Marker: React.FC<{ o: Ov }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const k = spring({ frame, fps, config: { damping: 14, stiffness: 200, mass: 0.6 } });
  const exit = interpolate(frame, [dur - 7, dur], [1, 0], clamp01);
  const swipe = interpolate(frame, [5, 15], [0, 100], clamp01);
  const chars = o.parts.map(([s]) => s).join("").length;
  const strikeF = o.strike !== undefined ? Math.round((o.strike - o.in) * fps) : null;
  const strike = strikeF === null ? 0 : interpolate(frame, [strikeF, strikeF + 8], [0, 1], clamp01);
  if (o.bubble) {
    const tailL = (o.tail ?? (o.side === "r" ? "r" : "l")) === "l";
    return (
      <div style={{ position: "absolute", inset: 0, opacity: exit }}>
        <div style={rowBox(o)}>
          <div style={{ position: "relative", background: "#FFFFFF", borderRadius: 34, padding: "18px 30px 22px", maxWidth: o.maxw ?? 640, boxShadow: "0 14px 34px rgba(0,0,0,0.28)", transform: `scale(${k})`, transformOrigin: tailL ? "0% 100%" : "100% 100%", fontFamily: FONT, fontWeight: 700, fontSize: o.size ?? 44, lineHeight: 1.15, color: T.primary }}>
            {o.parts.map(([s]) => s).join("")}
            <div style={{ position: "absolute", bottom: -16, [tailL ? "left" : "right"]: 34, width: 36, height: 36, background: "#FFFFFF", transform: "rotate(45deg)", borderRadius: 6 }} />
          </div>
        </div>
      </div>
    );
  }
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit }}>
      <div style={rowBox(o)}>
        <div style={{ position: "relative", maxWidth: o.side ? 560 : 960, textAlign: o.side === "l" ? "left" : o.side === "r" ? "right" : "center", transform: `translateY(${(1 - k) * 30}px)`, opacity: Math.min(1, k * 1.6) * (1 - 0.4 * strike) }}>
          <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: o.size ?? (chars > 26 ? 60 : chars > 14 ? 74 : 92), lineHeight: 1.12, letterSpacing: -1 }}>
            {o.parts.map(([s, hl], i) => (
              <span
                key={i}
                style={{
                  color: hl ? T.primary : "#FFFFFF",
                  textShadow: hl ? "none" : "0 4px 16px rgba(0,0,0,0.55), 0 2px 4px rgba(0,0,0,0.45)",
                  backgroundImage: hl ? `linear-gradient(${T.accent}, ${T.accent})` : undefined,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "0 60%",
                  backgroundSize: hl ? `${swipe}% 78%` : undefined,
                  padding: hl ? "0 8px" : 0,
                  boxDecorationBreak: "clone",
                  WebkitBoxDecorationBreak: "clone",
                }}
              >
                {s}
              </span>
            ))}
          </div>
          {strikeF !== null && <div style={{ position: "absolute", left: -8, top: "52%", height: 10, borderRadius: 5, width: `calc(${strike} * (100% + 16px))`, background: T.accent, boxShadow: "0 2px 8px rgba(0,0,0,0.35)" }} />}
        </div>
      </div>
    </div>
  );
};

// closing contact card over the speaker (lower half): lines as given, "!" = big line, "#" = tag
export const CallCard: React.FC<{ o: Ov }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = spring({ frame, fps, config: { damping: 14, stiffness: 170, mass: 0.7 } });
  const lines = o.lines ?? [];
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: o.top ?? 260, transform: `translateY(${(1 - k) * 60}px)`, opacity: Math.min(1, k * 1.5) }}>
      <div style={{ background: "#FFFFFF", borderRadius: 36, padding: "34px 40px 38px", boxShadow: "0 20px 50px rgba(0,0,0,0.3)", textAlign: "center", borderBottom: `12px solid ${T.accent}` }}>
        {lines.map((ln, i) => {
          const kk = spring({ frame: frame - 6 - i * 8, fps, config: { damping: 15, stiffness: 170 } });
          const tag = ln.startsWith("#");
          const big = ln.startsWith("!");
          const text = tag || big ? ln.slice(1) : ln;
          return (
            <div key={i} style={{ opacity: kk, transform: `translateY(${(1 - kk) * 20}px)`, marginTop: i ? 14 : 0 }}>
              <span
                style={{
                  display: "inline-block",
                  fontFamily: FONT,
                  fontWeight: tag ? 800 : big ? 900 : 600,
                  fontSize: tag ? 26 : big ? 64 : 42,
                  letterSpacing: tag ? 4 : big ? 1 : 0,
                  lineHeight: 1.15,
                  color: T.primary,
                  background: tag ? T.accent : "transparent",
                  padding: tag ? "6px 18px" : 0,
                  borderRadius: 12,
                }}
              >
                {text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
