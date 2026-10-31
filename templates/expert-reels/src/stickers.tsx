import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, T, clamp01 } from "./theme";

// Instagram-style stickers over the speaker's chest (never the face): a question box and a poll.
//   qbox: o.head (orange gradient header text), o.question (body text), o.top
//   poll: o.question, o.options [{text, at}], o.pick (index) + o.pickAt: the picked option fills orange
//         with a check, the others fade and get struck through
// A theme may set sticker / stickerLight / stickerDeep / stickerInk to recolour the stickers (e.g. pink); default orange.
const TH = T as any;
const ORANGE = TH.sticker ?? "#E0662A";
const LIGHT = TH.stickerLight ?? "#F2994A";
const DEEP = TH.stickerDeep ?? "#B8460F";
const INK = TH.stickerInk ?? "#3A2418";

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
      <div style={{ background: `linear-gradient(120deg, ${ORANGE} 0%, ${LIGHT} 100%)`, padding: "34px 44px 30px", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: o.headSize ?? 58, lineHeight: 1.1, color: "#FFFFFF" }}>{o.head}</div>
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
              <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${100 * fill}%`, background: `linear-gradient(90deg, ${ORANGE}, ${LIGHT})` }} />
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

// checklist: a white card (o.title) whose items tick in one by one as they are named (o.items [{text, at}])
export const Checklist: React.FC<{ o: any }> = ({ o }) => {
  const { k, exit, t } = useIn(o);
  const items: { text: string; at: number }[] = o.items ?? [];
  return (
    <Card o={{ ...o, rot: o.rot ?? 0 }} k={k} exit={exit}>
      <div style={{ background: `linear-gradient(120deg, ${ORANGE} 0%, ${LIGHT} 100%)`, padding: "24px 40px", fontFamily: FONT, fontWeight: 900, fontSize: o.headSize ?? 46, color: "#FFFFFF", textAlign: "center" }}>{o.title}</div>
      <div style={{ padding: "22px 40px 30px", display: "flex", flexDirection: "column", gap: 18 }}>
        {items.map((it, i) => {
          const a = interpolate(t, [it.at, it.at + 0.3], [0, 1], clamp01);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 22, opacity: 0.25 + 0.75 * a }}>
              <div style={{ width: 64, height: 64, borderRadius: 32, flexShrink: 0, border: `5px solid ${ORANGE}`, background: a > 0.5 ? ORANGE : "#FFFFFF", color: "#FFFFFF", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT, fontWeight: 900, fontSize: 38, transform: `scale(${0.8 + 0.2 * a})` }}>{a > 0.5 ? "✓" : ""}</div>
              <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: o.size ?? 44, color: INK, lineHeight: 1.1 }}>{it.text}</div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// dm: an Instagram direct-message thread: o.hint above, then the keyword o.keyword types into the
// message field (o.typeAt) and is sent as an orange bubble (o.sendAt)
export const DM: React.FC<{ o: any }> = ({ o }) => {
  const { k, exit, t } = useIn(o);
  const word: string = o.keyword ?? "";
  const typed = Math.floor(interpolate(t, [o.typeAt ?? o.in, (o.typeAt ?? o.in) + 0.5], [0, word.length], clamp01));
  const sent = interpolate(t, [o.sendAt ?? o.in + 1, (o.sendAt ?? o.in + 1) + 0.3], [0, 1], clamp01);
  return (
    <Card o={{ ...o, rot: o.rot ?? 0 }} k={k} exit={exit}>
      <div style={{ padding: "26px 36px 10px", fontFamily: FONT, fontWeight: 800, fontSize: o.hintSize ?? 40, color: DEEP, textAlign: "center", lineHeight: 1.15 }}>{o.hint}</div>
      <div style={{ height: 130, position: "relative" }}>
        <div style={{ position: "absolute", right: 40, top: 20, opacity: sent, transform: `translateY(${(1 - sent) * 40}px) scale(${0.8 + 0.2 * sent})`, transformOrigin: "100% 100%", background: `linear-gradient(120deg, ${ORANGE}, ${LIGHT})`, color: "#FFFFFF", borderRadius: "40px 40px 10px 40px", padding: "20px 40px", fontFamily: FONT, fontWeight: 900, fontSize: 56, letterSpacing: 2 }}>{word}</div>
      </div>
      <div style={{ margin: "0 30px 30px", height: 92, borderRadius: 46, border: "3px solid #E8DDD3", display: "flex", alignItems: "center", padding: "0 18px 0 34px", gap: 16 }}>
        <div style={{ flex: 1, fontFamily: FONT, fontWeight: 800, fontSize: 42, color: sent > 0.5 ? "#B9A99B" : INK }}>{sent > 0.5 ? "Mesaj yaz…" : word.slice(0, typed) || "Mesaj yaz…"}</div>
        <div style={{ background: sent > 0.5 || typed < word.length ? "#F4EEE8" : ORANGE, color: sent > 0.5 || typed < word.length ? "#B9A99B" : "#FFFFFF", borderRadius: 30, padding: "12px 26px", fontFamily: FONT, fontWeight: 800, fontSize: 34 }}>Göndər</div>
      </div>
    </Card>
  );
};

// tip: a big orange numeral next to a short line on a cream band (numbered advice: "1 · …")
export const Tip: React.FC<{ o: any }> = ({ o }) => {
  const { k, exit, frame, fps } = useIn(o);
  const kn = spring({ frame: frame - 4, fps, config: { damping: 11, stiffness: 200, mass: 0.6 } });
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: o.top ?? 200, opacity: Math.min(1, k * 1.6) * exit, transform: `translateX(${(1 - k) * -60}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 28, background: "rgba(247,230,208,0.97)", borderRadius: 30, padding: "18px 36px 18px 26px", boxShadow: "0 18px 44px rgba(40,15,0,0.3)" }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: o.numSize ?? 150, lineHeight: 0.9, color: ORANGE, transform: `scale(${0.6 + 0.4 * kn})`, minWidth: 100, textAlign: "center" }}>{o.num}</div>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: o.size ?? 50, lineHeight: 1.1, color: INK }}>
          {o.text}
          {o.sub && <div style={{ fontWeight: 700, fontSize: (o.size ?? 50) * 0.66, color: DEEP, marginTop: 6 }}>{o.sub}</div>}
        </div>
      </div>
    </div>
  );
};
