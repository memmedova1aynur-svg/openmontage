import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, clamp01 } from "./theme";

// Instagram-style stickers over the speaker's chest (never the face): a question box and a poll.
//   qbox: o.head (orange gradient header text), o.question (body text), o.top
//   poll: o.question, o.options [{text, at}], o.pick (index) + o.pickAt: the picked option fills orange
//         with a check, the others fade and get struck through
const ORANGE = "#E0662A";
const DEEP = "#B8460F";
const INK = "#3A2418";

const useIn = (o: any) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const k = spring({ frame, fps, config: { damping: 16, stiffness: 170, mass: 0.7 } });
  const exit = interpolate(frame, [dur - 8, dur], [1, 0], clamp01);
  return { frame, fps, t: o.in + frame / fps, k, exit };
};

const Card: React.FC<{ o: any; k: number; exit: number; children: React.ReactNode }> = ({ o, k, exit, children }) => (
  <div style={{ position: "absolute", left: 0, right: 0, top: o.top ?? 1060, display: "flex", justifyContent: "center", opacity: Math.min(1, k * 1.6) * exit }}>
    <div style={{ width: o.width ?? 860, background: "#FFFFFF", borderRadius: 40, overflow: "hidden", boxShadow: "0 24px 60px rgba(40,15,0,0.35)", transform: `translateY(${(1 - k) * 50}px) scale(${0.9 + 0.1 * k}) rotate(${o.rot ?? -1.5}deg)` }}>
      {children}
    </div>
  </div>
);

export const QBox: React.FC<{ o: any }> = ({ o }) => {
  const { k, exit, frame } = useIn(o);
  const kb = interpolate(frame, [8, 18], [0, 1], clamp01);
  return (
    <Card o={o} k={k} exit={exit}>
      <div style={{ background: `linear-gradient(120deg, ${ORANGE} 0%, #F2994A 100%)`, padding: "34px 44px 30px", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: o.headSize ?? 58, lineHeight: 1.1, color: "#FFFFFF" }}>{o.head}</div>
      {o.question && (
        <div style={{ padding: "30px 44px 36px", textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: o.size ?? 46, lineHeight: 1.18, color: INK, opacity: kb }}>{o.question}</div>
      )}
    </Card>
  );
};

export const Poll: React.FC<{ o: any }> = ({ o }) => {
  const { k, exit, t } = useIn(o);
  const opts: { text: string; at: number }[] = o.options ?? [];
  const pk = o.pickAt !== undefined ? interpolate(t, [o.pickAt, o.pickAt + 0.35], [0, 1], clamp01) : 0;
  return (
    <Card o={o} k={k} exit={exit}>
      <div style={{ padding: "34px 40px 14px", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: o.size ?? 50, lineHeight: 1.12, color: DEEP }}>{o.question}</div>
      <div style={{ padding: "10px 34px 36px", display: "flex", flexDirection: "column", gap: 20 }}>
        {opts.map((op, i) => {
          const a = interpolate(t, [op.at, op.at + 0.3], [0, 1], clamp01);
          const picked = i === o.pick;
          const fill = picked ? pk : 0;
          const fade = !picked && o.pick !== undefined ? pk : 0;
          return (
            <div key={i} style={{ position: "relative", height: o.optH ?? 112, borderRadius: 56, background: "#F4EEE8", overflow: "hidden", opacity: a * (1 - 0.5 * fade), transform: `translateX(${(1 - a) * 40}px)` }}>
              <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${100 * fill}%`, background: `linear-gradient(90deg, ${ORANGE}, #F2994A)` }} />
              <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 16, fontFamily: FONT, fontWeight: 800, fontSize: op.text.length > 26 ? 38 : 44, color: fill > 0.5 ? "#FFFFFF" : INK }}>
                {picked && fill > 0.3 && <span style={{ fontWeight: 900 }}>✓</span>}
                <span style={{ position: "relative" }}>
                  {op.text}
                  {fade > 0 && <span style={{ position: "absolute", left: -6, top: "52%", height: 6, width: `calc(${fade} * (100% + 12px))`, background: DEEP, borderRadius: 3 }} />}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
