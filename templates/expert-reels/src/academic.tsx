import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { EMPH, FONT, Pill, T, clamp01, rgba } from "./theme";

// Academic editorial: cream paper cards, navy type, a thin gold rule and small gold
// small-caps labels (teacher-education brands). Overlay "edcard" + full-frame scene "ac_skills".

const FPSX = 30;
const ease = Easing.out(Easing.cubic);
const prog = (t: number, at: number | undefined, d = 0.45) => (at === undefined ? 1 : ease(interpolate(t, [at, at + d], [0, 1], clamp01)));
const GOLD = () => EMPH;
// gold is too light for text on cream: labels, numbers and emphasis use a deeper gold
const GOLD_TXT = "#946C22";
const CREAM = () => T.accent;

// ---------------------------------------------------------------- overlay card
export const EdCard: React.FC<{ o: Pill & { num?: string; big?: boolean } }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const k = spring({ frame, fps, config: { damping: 16, stiffness: 170, mass: 0.7 } });
  const rule = interpolate(frame, [4, 16], [0, 1], clamp01);
  const exit = interpolate(frame, [dur - 7, dur], [1, 0], clamp01);
  const chars = o.parts.map(([s]) => s).join("").length;
  const size = o.size ?? (o.big ? (chars > 26 ? 60 : 72) : chars > 30 ? 44 : chars > 18 ? 52 : 60);
  const box: React.CSSProperties =
    o.side === "l" ? { position: "absolute", top: o.top ?? 280, left: 60 } : o.side === "r" ? { position: "absolute", top: o.top ?? 280, right: 60 } : { position: "absolute", top: o.top ?? 280, left: 0, right: 0, display: "flex", justifyContent: "center" };
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit }}>
      <div style={box}>
        <div
          style={{
            position: "relative",
            maxWidth: o.side ? 720 : 940,
            background: CREAM(),
            padding: o.label ? "22px 40px 28px" : "20px 38px 24px",
            borderRadius: 6,
            boxShadow: "0 18px 44px rgba(0,0,0,0.30)",
            transform: `translateY(${(1 - k) * 36}px)`,
            opacity: Math.min(1, k * 1.6),
            display: "flex",
            gap: 22,
            alignItems: "center",
          }}
        >
          {o.num && <div style={{ fontFamily: FONT, fontWeight: 300, fontSize: size * 1.35, lineHeight: 1, color: GOLD_TXT }}>{o.num}</div>}
          <div style={{ textAlign: o.num ? "left" : "center", flex: 1 }}>
            {o.label && (
              <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 26, letterSpacing: 5, color: GOLD_TXT, marginBottom: 8 }}>{o.label}</div>
            )}
            <div style={{ height: 3, width: `${rule * 100}%`, background: GOLD(), margin: o.num ? "0 0 12px" : "0 auto 12px", maxWidth: o.num ? 120 : 160 }} />
            <div style={{ fontFamily: FONT, fontWeight: o.big ? 800 : 700, fontSize: size, lineHeight: 1.12, color: T.primary }}>
              {o.parts.map(([s, hl], i) => (
                <span key={i} style={{ color: hl ? GOLD_TXT : T.primary, fontWeight: hl ? 900 : undefined }}>{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- four skills on a cream page
const ICON: Record<string, string> = {
  reading: "M10 30 Q45 15 80 30 V100 Q45 85 10 100 Z M80 30 Q115 15 150 30 V100 Q115 85 80 100",
  writing: "M30 110 L40 80 L110 10 L130 30 L60 100 Z M100 20 L120 40 M30 110 L60 100",
  speaking: "M15 20 H135 Q145 20 145 30 V80 Q145 90 135 90 H65 L35 115 V90 H15 Q5 90 5 80 V30 Q5 20 15 20 Z M35 48 H115 M35 66 H95",
  listening: "M20 85 V65 Q20 10 75 10 Q130 10 130 65 V85 M10 75 H40 V115 H10 Z M110 75 H140 V115 H110 Z",
};

const Skills: React.FC<{ f: number; p: Record<string, any>; startT: number }> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const tiles: [string, string, number][] = [
    ["reading", "Reading", a.reading],
    ["writing", "Writing", a.writing],
    ["speaking", "Speaking", a.speaking],
    ["listening", "Listening", a.listening],
  ];
  const head = prog(t, startT, 0.5);
  const fmt = prog(t, a.formats, 0.4);
  const pr = prog(t, a.practice, 0.4);
  return (
    <div style={{ position: "absolute", inset: 0, background: CREAM() }}>
      <div style={{ position: "absolute", inset: 46, border: `2px solid ${rgba(T.primary, 0.18)}` }} />
      <div style={{ position: "absolute", top: 250, left: 0, right: 0, textAlign: "center", opacity: head }}>
        <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 26, letterSpacing: 8, color: GOLD_TXT }}>{p.label}</div>
        <div style={{ margin: "14px auto", height: 3, width: 160 * head, background: GOLD() }} />
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 64, color: T.primary }}>{p.title}</div>
        <div style={{ fontFamily: FONT, fontWeight: 500, fontSize: 38, color: T.primary, marginTop: 10, opacity: fmt }}>{p.sub}</div>
      </div>
      {tiles.map(([ic, name, at], i) => {
        const k = prog(t, at, 0.45);
        const draw = prog(t, at === undefined ? undefined : at + 0.05, 0.6);
        const x = 110 + (i % 2) * 450;
        const y = 640 + Math.floor(i / 2) * 400;
        return (
          <div key={i} style={{ position: "absolute", left: x, top: y, width: 410, height: 360, background: "#FFFFFF", border: `2px solid ${rgba(T.primary, 0.12)}`, borderTop: `8px solid ${T.primary}`, borderRadius: 6, boxShadow: "0 12px 30px rgba(20,40,75,0.12)", opacity: Math.min(1, k * 1.8), transform: `translateY(${(1 - k) * 40}px)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 26 }}>
            <svg width={150} height={125} viewBox="0 0 150 125">
              <path d={ICON[ic]} pathLength={1} fill="none" stroke={T.primary} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={1} strokeDashoffset={1 - draw} />
            </svg>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 52, color: T.primary }}>{name}</div>
            <div style={{ height: 4, width: 90 * draw, background: GOLD() }} />
          </div>
        );
      })}
      <div style={{ position: "absolute", top: 1460, left: 0, right: 0, textAlign: "center", opacity: pr, transform: `translateY(${(1 - pr) * 20}px)` }}>
        <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 40, color: CREAM(), background: T.primary, padding: "12px 30px", borderRadius: 6 }}>{p.practice}</span>
      </div>
    </div>
  );
};

export const ACADEMIC: Record<string, React.FC<{ f: number; p: Record<string, any>; startT: number }>> = {
  ac_skills: Skills,
};
