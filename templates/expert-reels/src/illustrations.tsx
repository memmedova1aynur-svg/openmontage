import React from "react";
import { interpolate, spring, useVideoConfig } from "remotion";
import { FONT, T, clamp01, rgba } from "./theme";

// Flat, hand-built SVG illustrations for split-screen explainers (no stock, no generated images).
// Every scene takes the clip-local frame `f`, its props `p` and the absolute start time `startT`.

const SKIN = "#F2CDB0";
const HAIR = "#3A2A22";
const INK = () => T.primary;

type Pose = "up" | "cling" | "ears" | "down" | "reach" | "back" | "out";
type Face = "smile" | "frown" | "open" | "calm";

// A child, drawn on a 200 x 260 grid with the hips at (100, 175).
const Child: React.FC<{ pose: Pose; face: Face; f: number; shirt?: string; eyesClosed?: boolean; sit?: boolean }> = ({ pose, face, f, shirt, eyesClosed, sit }) => {
  const ink = INK();
  const sw = 9;
  const wave = Math.sin(f / 5) * 6;
  const arm = (side: 1 | -1) => {
    const sx = 100 + side * 26;
    const sy = 112;
    switch (pose) {
      case "up":
        return `M${sx} ${sy} L${sx + side * 22} ${sy - 40 + (side > 0 ? wave : -wave)}`;
      case "cling":
        return `M${sx} ${sy} L${sx + side * 10} ${sy - 30}`;
      case "ears":
        return `M${sx} ${sy} Q${sx + side * 26} ${sy - 30} ${100 + side * 36} ${62}`;
      case "reach":
        return side > 0 ? `M${sx} ${sy} L${sx + 46} ${sy + 34 + wave / 2}` : `M${sx} ${sy} L${sx - 20} ${sy + 40}`;
      case "back":
        return `M${sx} ${sy} L${sx + side * 34} ${sy - 18}`;
      case "out":
        return `M${sx} ${sy} L${sx + side * 58} ${sy + (side > 0 ? 6 : -6) + wave / 3}`;
      default:
        return `M${sx} ${sy} L${sx + side * 12} ${sy + 46}`;
    }
  };
  const legs = sit ? ["M88 175 L70 200 L70 230", "M112 175 L130 200 L130 230"] : ["M90 175 L84 232", "M110 175 L116 232"];
  const mouth =
    face === "smile" ? "M88 74 Q100 86 112 74" : face === "frown" ? "M88 82 Q100 72 112 82" : face === "open" ? "M94 76 Q100 88 106 76 Z" : "M90 78 L110 78";
  return (
    <g>
      {legs.map((d, i) => (
        <path key={i} d={d} stroke={ink} strokeWidth={sw} strokeLinecap="round" fill="none" />
      ))}
      <path d={arm(-1)} stroke={SKIN} strokeWidth={sw} strokeLinecap="round" fill="none" />
      <path d={arm(1)} stroke={SKIN} strokeWidth={sw} strokeLinecap="round" fill="none" />
      <rect x={72} y={102} width={56} height={78} rx={20} fill={shirt ?? T.accent} />
      <circle cx={100} cy={66} r={32} fill={SKIN} />
      <path d="M68 62 Q70 30 100 30 Q132 30 132 62 Q122 44 100 46 Q80 46 68 62 Z" fill={HAIR} />
      {eyesClosed ? (
        <>
          <path d="M84 64 Q89 68 94 64" stroke={HAIR} strokeWidth={3} fill="none" strokeLinecap="round" />
          <path d="M106 64 Q111 68 116 64" stroke={HAIR} strokeWidth={3} fill="none" strokeLinecap="round" />
        </>
      ) : (
        <>
          <circle cx={89} cy={63} r={face === "frown" ? 4.5 : 3.6} fill={HAIR} />
          <circle cx={111} cy={63} r={face === "frown" ? 4.5 : 3.6} fill={HAIR} />
        </>
      )}
      {face === "frown" && <path d="M82 54 L94 57 M118 54 L106 57" stroke={HAIR} strokeWidth={3} strokeLinecap="round" />}
      <path d={mouth} stroke={HAIR} strokeWidth={3.5} fill={face === "open" ? HAIR : "none"} strokeLinecap="round" />
      <circle cx={80} cy={76} r={5} fill="#F4A6A6" opacity={face === "smile" ? 0.6 : 0} />
      <circle cx={120} cy={76} r={5} fill="#F4A6A6" opacity={face === "smile" ? 0.6 : 0} />
    </g>
  );
};

// ---------------------------------------------------------------- scene art (each in a 300 x 300 box)
const SwingArt: React.FC<{ f: number; scared?: boolean }> = ({ f, scared }) => {
  const ink = INK();
  const amp = scared ? 3 : 16;
  const a = Math.sin(f / (scared ? 3 : 9)) * amp;
  return (
    <svg viewBox="0 0 300 300" width="100%" height="100%">
      <path d="M40 285 L90 20 L210 20 L260 285" stroke={ink} strokeWidth={10} fill="none" strokeLinejoin="round" />
      <g transform={`rotate(${a} 150 22)`}>
        <path d="M118 22 L118 196 M182 22 L182 196" stroke={rgba(ink, 0.7)} strokeWidth={4} />
        <rect x={108} y={192} width={84} height={12} rx={6} fill={ink} />
        <g transform="translate(50 30) scale(1)">
          <Child pose={scared ? "cling" : "up"} face={scared ? "frown" : "smile"} f={f} sit shirt={scared ? "#9CC9B2" : T.accent} />
        </g>
      </g>
      {!scared &&
        [0, 1].map((i) => (
          <path key={i} d={`M${60 + i * 170} ${150 + i * 10} q 12 -14 0 -28`} stroke={rgba(ink, 0.5)} strokeWidth={4} fill="none" strokeLinecap="round" opacity={0.5 + 0.5 * Math.sin(f / 6 + i)} />
        ))}
      {scared && <path d="M222 70 q 8 12 0 20 q -8 -8 0 -20 Z" fill="#8FC7E8" opacity={0.6 + 0.4 * Math.sin(f / 4)} />}
    </svg>
  );
};

const SandArt: React.FC<{ f: number; refuse?: boolean }> = ({ f, refuse }) => {
  const ink = INK();
  return (
    <svg viewBox="0 0 300 300" width="100%" height="100%">
      <rect x={20} y={222} width={260} height={62} rx={14} fill="#F3DFB2" stroke={rgba(ink, 0.35)} strokeWidth={4} />
      <path d="M220 222 L232 180 L262 180 L270 222 Z" fill="#F6C66B" />
      <path d="M236 180 Q247 162 258 180" stroke={ink} strokeWidth={3} fill="none" />
      {refuse ? (
        <>
          <g transform="translate(40 20)">
            <Child pose="back" face="frown" f={f} shirt="#9CC9B2" />
          </g>
          {[0, 1, 2].map((i) => (
            <path key={i} d={`M${208 + i * 6} ${110 + i * 14} l 14 -6`} stroke="#E5484D" strokeWidth={4} strokeLinecap="round" opacity={0.5 + 0.5 * Math.sin(f / 4 + i)} />
          ))}
        </>
      ) : (
        <>
          <g transform="translate(40 40)">
            <Child pose="reach" face="smile" f={f} sit />
          </g>
          {[0, 1, 2, 3, 4].map((i) => {
            const k = ((f / 2 + i * 7) % 30) / 30;
            return <circle key={i} cx={196 + i * 9 + k * 20} cy={200 - Math.sin(k * Math.PI) * 50} r={4} fill="#E2BE72" opacity={1 - k} />;
          })}
        </>
      )}
    </svg>
  );
};

const NoiseArt: React.FC<{ f: number; cover?: boolean }> = ({ f, cover }) => {
  const ink = INK();
  return (
    <svg viewBox="0 0 300 300" width="100%" height="100%">
      <g transform="translate(50 40)">
        <Child pose={cover ? "ears" : "out"} face={cover ? "frown" : "smile"} f={f} eyesClosed={cover} shirt={cover ? "#9CC9B2" : T.accent} />
      </g>
      {cover
        ? [0, 1].map((s) =>
            [0, 1, 2].map((i) => (
              <path
                key={`${s}${i}`}
                d={s ? `M${236 + i * 14} 70 l 10 14 l -10 14 l 10 14` : `M${64 - i * 14} 70 l -10 14 l 10 14 l -10 14`}
                stroke="#E5484D"
                strokeWidth={4}
                fill="none"
                strokeLinecap="round"
                opacity={0.35 + 0.5 * Math.abs(Math.sin(f / 3 + i))}
              />
            )),
          )
        : [0, 1, 2].map((i) => {
            const k = ((f / 3 + i * 10) % 30) / 30;
            return (
              <text key={i} x={i % 2 ? 230 : 40} y={120 - k * 70} fontSize={34} fill={ink} opacity={1 - k} fontFamily={FONT}>
                ♪
              </text>
            );
          })}
    </svg>
  );
};

const BalanceArt: React.FC<{ f: number }> = ({ f }) => {
  const ink = INK();
  const tilt = Math.sin(f / 10) * 7;
  return (
    <svg viewBox="0 0 300 300" width="100%" height="100%">
      <rect x={40} y={262} width={220} height={16} rx={8} fill={ink} />
      <path d="M150 262 L136 288 L164 288 Z" fill={rgba(ink, 0.6)} />
      <g transform={`rotate(${tilt} 150 262)`}>
        <g transform="translate(50 32)">
          <Child pose="out" face="calm" f={f} />
        </g>
      </g>
    </svg>
  );
};

const BodyArt: React.FC<{ f: number }> = ({ f }) => {
  const ink = INK();
  const joints = [
    [100, 112],
    [74, 136],
    [126, 136],
    [90, 178],
    [110, 178],
    [86, 232],
    [114, 232],
  ];
  return (
    <svg viewBox="0 0 300 300" width="100%" height="100%">
      <g transform="translate(50 30)">
        <Child pose="out" face="calm" f={f} shirt={rgba(T.accent, 0.8)} />
        {joints.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={7 + 3 * Math.abs(Math.sin(f / 6 + i))} fill="none" stroke={ink} strokeWidth={3} opacity={0.8} />
        ))}
      </g>
      <path d="M26 150 q -14 -40 10 -70 M274 150 q 14 -40 -10 -70" stroke={rgba(ink, 0.5)} strokeWidth={4} fill="none" strokeLinecap="round" />
    </svg>
  );
};

const InnerArt: React.FC<{ f: number }> = ({ f }) => {
  const ink = INK();
  const beat = 1 + 0.12 * Math.max(0, Math.sin(f / 4)) ** 4;
  return (
    <svg viewBox="0 0 300 300" width="100%" height="100%">
      <g transform="translate(50 30)">
        <Child pose="down" face="calm" f={f} shirt={rgba(T.accent, 0.55)} />
      </g>
      <g transform={`translate(150 168) scale(${beat}) translate(-150 -168)`}>
        <path d="M150 186 C120 166 128 146 141 146 C147 146 150 152 150 152 C150 152 153 146 159 146 C172 146 180 166 150 186 Z" fill="#E5484D" />
      </g>
      {[0, 1, 2].map((i) => {
        const k = ((f / 3 + i * 10) % 30) / 30;
        return <circle key={i} cx={150} cy={168} r={20 + k * 60} fill="none" stroke={rgba(ink, 0.6)} strokeWidth={3} opacity={1 - k} />;
      })}
    </svg>
  );
};

const ART: Record<string, React.FC<{ f: number }>> = {
  "swing-happy": ({ f }) => <SwingArt f={f} />,
  "swing-scared": ({ f }) => <SwingArt f={f} scared />,
  "sand-play": ({ f }) => <SandArt f={f} />,
  "sand-refuse": ({ f }) => <SandArt f={f} refuse />,
  "noise-calm": ({ f }) => <NoiseArt f={f} />,
  "noise-cover": ({ f }) => <NoiseArt f={f} cover />,
  balance: BalanceArt,
  body: BodyArt,
  inner: InnerArt,
};

// ---------------------------------------------------------------- scenes
const Card: React.FC<{ art: string; label: string; f: number; fps: number; tag?: string }> = ({ art, label, f, fps, tag }) => {
  const k = spring({ frame: f, fps, config: { damping: 13, stiffness: 170, mass: 0.7 } });
  const Art = ART[art];
  return (
    <div style={{ width: 490, display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${0.6 + 0.4 * k}) translateY(${(1 - k) * 40}px)`, opacity: Math.min(1, k * 1.6) }}>
      <div style={{ width: 490, height: 520, borderRadius: 48, background: "#FFFFFF", boxShadow: `0 16px 40px ${rgba(T.primary, 0.16)}`, border: `4px solid ${T.accentSoft}`, padding: 20, position: "relative" }}>
        {tag && (
          <div style={{ position: "absolute", top: 18, left: 22, padding: "4px 14px", borderRadius: 14, background: T.accentSoft, fontFamily: FONT, fontWeight: 800, fontSize: 24, color: T.primary }}>{tag}</div>
        )}
        {Art && <Art f={f} />}
      </div>
      <div style={{ marginTop: 18, fontFamily: FONT, fontWeight: 800, fontSize: 44, lineHeight: 1.12, color: T.primary, textAlign: "center", maxWidth: 480 }}>{label}</div>
    </div>
  );
};

// Two children side by side: the second appears only when "digəri" is said.
export const PairScene: React.FC<{ f: number; p: Record<string, any>; startT: number }> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const t = startT + f / fps;
  const fB = Math.round((t - p.b.at) * fps);
  return (
    <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 30 }}>
      <Card art={p.a.art} label={p.a.label} tag={p.a.tag} f={f} fps={fps} />
      <div style={{ width: 490 }}>{fB >= 0 && <Card art={p.b.art} label={p.b.label} tag={p.b.tag} f={fB} fps={fps} />}</div>
    </div>
  );
};

const SENSES: { label: string; d: string[] }[] = [
  { label: "Görmə", d: ["M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z", "c:12,12,3"] },
  { label: "Eşitmə", d: ["M7 9a5 5 0 1 1 10 0c0 3.5-3.5 4.5-3.5 8a3 3 0 0 1-6 0", "M10 9a2 2 0 1 1 4 0"] },
  { label: "İybilmə", d: ["M12 3c-1 4-4 8-4 12a3 3 0 0 0 3 3", "M12 18a3 3 0 0 0 4-1", "M9 18c-2 0-3-1-3-2"] },
  { label: "Dad", d: ["M4 11c3-3 13-3 16 0-3 6-13 6-16 0z", "M4 11c3 2 13 2 16 0", "M12 13v4"] },
  { label: "Toxunma", d: ["M8 13V5a2 2 0 0 1 4 0v6", "M12 10a2 2 0 0 1 4 0v2", "M16 11a2 2 0 0 1 4 0v4a7 7 0 0 1-7 7h-1a7 7 0 0 1-6-4l-2-4a2 2 0 0 1 3-2l1 2"] },
];

// Five senses arrive one by one; then each extra system takes the stage, big, on its word.
export const SensesScene: React.FC<{ f: number; p: Record<string, any>; startT: number }> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const t = startT + f / fps;
  const ink = T.primary;
  const feats: { art: string; label: string; at: number }[] = p.features ?? [];
  const cur = [...feats].reverse().find((x) => t >= x.at);
  const shrink = feats.length ? interpolate(t, [feats[0].at - 0.2, feats[0].at + 0.3], [1, 0.62], clamp01) : 1;
  return (
    <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ display: "flex", gap: 22, transform: `scale(${shrink})`, transformOrigin: "50% 0%" }}>
        {SENSES.map((s, i) => {
          const at = (p.times ?? [])[i] ?? startT + i * 0.2;
          const k = spring({ frame: Math.round((t - at) * fps), fps, config: { damping: 11, stiffness: 200, mass: 0.6 } });
          const draw = interpolate(t - at, [0.05, 0.5], [0, 1], clamp01);
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${k})`, opacity: t >= at ? 1 : 0 }}>
              <div style={{ width: 150, height: 150, borderRadius: 75, background: "#FFFFFF", border: `5px solid ${T.accent}`, boxShadow: `0 10px 26px ${rgba(ink, 0.15)}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width={84} height={84} viewBox="0 0 24 24" fill="none" stroke={ink} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
                  {s.d.map((d, j) => {
                    const c = { key: j, pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - draw };
                    if (d.startsWith("c:")) {
                      const [cx, cy, r] = d.slice(2).split(",").map(Number);
                      return <circle {...c} cx={cx} cy={cy} r={r} />;
                    }
                    return <path {...c} d={d} />;
                  })}
                </svg>
              </div>
              <div style={{ marginTop: 10, fontFamily: FONT, fontWeight: 700, fontSize: 30, color: ink }}>{s.label}</div>
            </div>
          );
        })}
      </div>
      {cur && (
        <div key={cur.art} style={{ marginTop: -40 }}>
          <Feature art={cur.art} label={cur.label} f={Math.round((t - cur.at) * fps)} fps={fps} />
        </div>
      )}
    </div>
  );
};

const Feature: React.FC<{ art: string; label: string; f: number; fps: number }> = ({ art, label, f, fps }) => {
  const k = spring({ frame: f, fps, config: { damping: 10, stiffness: 160, mass: 0.8 } });
  const Art = ART[art];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 30, transform: `scale(${0.5 + 0.5 * k})`, opacity: Math.min(1, k * 1.8) }}>
      <div style={{ width: 400, height: 400, borderRadius: 200, background: "#FFFFFF", border: `6px solid ${T.accent}`, boxShadow: `0 18px 44px ${rgba(T.primary, 0.2)}`, padding: 40 }}>{Art && <Art f={f} />}</div>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 64, lineHeight: 1.05, color: T.primary, maxWidth: 420 }}>{label}</div>
    </div>
  );
};

export const ILLUSTRATED: Record<string, React.FC<{ f: number; p: Record<string, any>; startT: number }>> = {
  pair: PairScene,
  senses: SensesScene,
};
