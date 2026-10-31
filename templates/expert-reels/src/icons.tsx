import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, Pill, T, clamp01, rgba } from "./theme";

// Simple line icons (24x24 grid). "c:x,y,r" is a circle; anything else is an SVG path.
export const ICONS: Record<string, string[]> = {
  ear: ["M7 9a5 5 0 1 1 10 0c0 3.5-3.5 4.5-3.5 8a3 3 0 0 1-6 0", "M10 9a2 2 0 1 1 4 0", "M19.5 5.5c1.2 1.6 1.2 4.4 0 6"],
  shirt: ["M8 3L3 6l2 4 3-1v12h8V9l3 1 2-4-5-3c-1 1.8-2.2 2.7-4 2.7S9 4.8 8 3z"],
  food: ["M6 3v6a2 2 0 0 0 4 0V3", "M8 3v18", "c:17,7,3", "M17 10v11"],
  home: ["M3 11l9-7 9 7", "M5 10v10h14V10", "M10 20v-5h4v5"],
  motion: ["M4 12a8 8 0 0 1 14-5.3", "M18 3v4h-4", "M20 12a8 8 0 0 1-14 5.3", "M6 21v-4h4"],
  scissors: ["c:6,6,3", "c:6,18,3", "M8.6 7.6L20 19", "M8.6 16.4L20 5"],
  clock: ["c:12,12,9", "M12 7v5l3.5 2"],
  laptop: ["M4 5h16v11H4z", "M2 19h20", "M10 10l3 1.5-3 1.5z"],
  brain: ["M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 3 3", "M15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-3 3", "M12 4v16", "M9 9h-1.5", "M15 14h1.5"],
  sun: ["c:12,12,4", "M12 2v2", "M12 20v2", "M2 12h2", "M20 12h2", "M4.9 4.9l1.4 1.4", "M17.7 17.7l1.4 1.4", "M4.9 19.1l1.4-1.4", "M17.7 6.3l1.4-1.4"],
  heart: ["M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"],
  person: ["c:12,5,2.5", "M12 8v7", "M7 11h10", "M12 15l-3.5 6", "M12 15l3.5 6"],
  puzzle: ["M4 8h4a2 2 0 1 1 4 0h4v4a2 2 0 1 1 0 4v4H4z"],
  check: ["c:12,12,9", "M8 12.5l2.6 2.6L16 9.6"],
  blocks: ["M4 14h7v7H4z", "M13 14h7v7h-7z", "M8.5 7h7v7h-7z"],
  waves: ["M3 9c3-3 6 3 9 0s6 3 9 0", "M3 15c3-3 6 3 9 0s6 3 9 0"],
  shield: ["M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z", "M8.5 12l2.5 2.5 4.5-5"],
  chair: ["M7 3v10h10V3", "M6 13h12", "M7 13v8", "M17 13v8", "M7 8h10"],
  drop: ["M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z", "M9.5 15a2.5 2.5 0 0 0 2.5 2.5"],
  mute: ["M3 10v4h4l5 4V6L7 10z", "M16 9l5 6", "M21 9l-5 6"],
  hand: ["M8 13V6a1.5 1.5 0 0 1 3 0v5", "M11 11V4.5a1.5 1.5 0 0 1 3 0V11", "M14 11V6a1.5 1.5 0 0 1 3 0v7", "M8 12.5a1.5 1.5 0 0 0-3 0V15a6 6 0 0 0 6 6h1a5 5 0 0 0 5-5v-3"],
  people: ["c:8,7,2.5", "c:16,7,2.5", "M3.5 19a4.5 4.5 0 0 1 9 0", "M11.5 19a4.5 4.5 0 0 1 9 0"],
  teacher: ["c:7,6,2.5", "M7 9v6", "M4 21l3-6 3 6", "M12 4h9v8h-9", "M7 11l5-3"],
  phone: ["M7 2h10a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z", "M11 18.5h2"],
  tablet: ["M4 3h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z", "M11 18h2"],
  tv: ["M3 6h18v12H3z", "M8 21h8", "M9 2l3 4 3-4"],
  star: ["M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"],
  ball: ["c:12,12,9", "M3.5 9.5c5 2 12 2 17 0", "M3.5 14.5c5-2 12-2 17 0"],
  moon: ["M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"],
  baby: ["c:12,13,7", "M12 6c0-1.8 1.4-3 3-2.4", "c:9.5,12,0.7", "c:14.5,12,0.7", "M10 15.5c1.1 1 2.9 1 4 0"],
  bottle: ["M9 9h6v10a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z", "M10 9V6h4v3", "M11 3.5h2V6h-2z", "M9 13h2.5", "M9 16h2.5"],
  hug: ["c:9,6,2.5", "c:15.5,9.5,2", "M4 21c0-5 2.5-8 5-8s4 1.2 5 3", "M6.5 15.5c2.5 2.5 7 3 11 0"],
  book: ["M4 5c3-1 6-1 8 1v14c-2-2-5-2-8-1z", "M20 5c-3-1-6-1-8 1v14c2-2 5-2 8-1z"],
};

// Icon in a soft circle + short label, pinned to the left or right edge beside the speaker.
// The circle pops in, the icon draws itself, the label slides out of the circle.
export const IconChip: React.FC<{ o: Pill }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const pop = spring({ frame, fps, config: { damping: 11, stiffness: 190, mass: 0.6 } });
  const draw = interpolate(frame, [4, 22], [0, 1], clamp01);
  const label = spring({ frame: frame - 6, fps, config: { damping: 16, stiffness: 170 } });
  const exit = interpolate(frame, [dur - 8, dur], [1, 0], clamp01);
  const float = Math.sin(frame / 18) * 4 * Math.min(1, frame / 20);
  const right = o.side === "r";
  const centre = o.side === undefined;
  const ink = T.primary;
  const text = o.parts.map(([t]) => t).join("");
  return (
    <div
      style={{
        position: "absolute",
        top: o.top ?? 420,
        ...(centre ? { left: "50%", maxWidth: 900, whiteSpace: "nowrap", translate: "-50% 0" } : { [right ? "right" : "left"]: o.stack ? 14 : 36 }),
        display: "flex",
        // stack: circle above a centred label - a narrow chip for the side column next to a close-up head
        flexDirection: o.stack ? "column" : right ? "row-reverse" : "row",
        alignItems: "center",
        gap: o.stack ? 8 : 14,
        ...(centre ? {} : { maxWidth: o.stack ? 240 : 370 }),
        opacity: exit,
        transform: `translateY(${float}px) scale(${centre ? 1.25 : 1})`,
        transformOrigin: "50% 0%",
      }}
    >
      <div style={{ position: "relative", flex: "0 0 auto", width: o.stack ? 150 : 96, height: o.stack ? 150 : 96, borderRadius: o.stack ? 75 : 48, background: o.tint ?? rgba(T.accentSoft, 0.97), boxShadow: `0 8px 22px ${rgba(ink, 0.18)}`, border: o.tint ? "4px solid #FFFFFF" : `3px solid ${rgba(T.accent, 0.9)}`, transform: `scale(${pop}) rotate(${(1 - pop) * -40}deg)`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width={o.stack ? 86 : 56} height={o.stack ? 86 : 56} viewBox="0 0 24 24" fill="none" stroke={o.tint ? "#FFFFFF" : ink} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          {(ICONS[o.icon ?? "heart"] ?? []).map((d, i) => {
            const common = { key: i, pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - draw };
            if (d.startsWith("c:")) {
              const [cx, cy, r] = d.slice(2).split(",").map(Number);
              return <circle {...common} cx={cx} cy={cy} r={r} />;
            }
            return <path {...common} d={d} />;
          })}
        </svg>
        {o.badge && (
          <div style={{ position: "absolute", top: -8, [right ? "left" : "right"]: -8, minWidth: 34, height: 34, borderRadius: 17, background: ink, color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 20, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 6px" }}>
            {o.badge}
          </div>
        )}
      </div>
      {(text.trim() || o.sub) && <div
        style={{
          padding: "8px 14px 10px",
          borderRadius: 16,
          background: "rgba(255,255,255,0.88)",
          textAlign: o.stack ? "center" : right ? "right" : "left",
          transform: o.stack ? `translateY(${(1 - label) * -20}px)` : `translateX(${(1 - label) * (right ? 30 : -30)}px)`,
          opacity: label,
        }}
      >
        <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: o.stack ? 34 : 31, lineHeight: 1.12, color: ink }}>{text}</div>
        {o.sub && <div style={{ fontFamily: FONT, fontWeight: 500, fontSize: 25, lineHeight: 1.2, color: rgba(ink, 0.8), marginTop: 3 }}>{o.sub}</div>}
      </div>}
    </div>
  );
};

// Compact opening title: small tag, title, one-line subtitle. Kept small so it sits above the head.
export const TitleCard: React.FC<{ o: Pill }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const enter = spring({ frame, fps, config: { damping: 15, stiffness: 160, mass: 0.7 } });
  const exit = interpolate(frame, [dur - 9, dur], [1, 0], clamp01);
  const line = interpolate(frame, [8, 26], [0, 1], clamp01);
  return (
    <div style={{ position: "absolute", top: o.top ?? 130, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: Math.min(1, enter * 1.5) * exit }}>
      <div
        style={{
          maxWidth: 780,
          textAlign: "center",
          transform: `translateY(${(1 - enter) * -30}px)`,
          // bare: no card, just type with a soft light halo so it reads on the wall
          ...(o.small
            ? { textShadow: "0 0 16px rgba(255,255,255,1), 0 0 6px rgba(255,255,255,1), 0 0 2px rgba(255,255,255,1)" }
            : { padding: "16px 34px 20px", borderRadius: 28, background: "rgba(255,255,255,0.93)", boxShadow: `0 12px 34px ${rgba(T.primary, 0.18)}` }),
        }}
      >
        {o.label && (
          <div style={{ display: "inline-block", padding: "5px 16px", borderRadius: 20, background: T.accentSoft, fontFamily: FONT, fontWeight: 800, fontSize: 22, letterSpacing: 3, color: T.primary, marginBottom: 8 }}>{o.label}</div>
        )}
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: o.small ? 54 : 50, lineHeight: 1.08, color: T.primary }}>{o.parts.map(([t]) => t).join("")}</div>
        <div style={{ height: 4, width: `${line * 46}%`, margin: "10px auto 8px", borderRadius: 2, background: T.accent }} />
        {o.sub && <div style={{ fontFamily: FONT, fontWeight: o.small ? 600 : 500, fontSize: o.small ? 24 : 27, lineHeight: 1.25, color: rgba(T.primary, 0.9) }}>{o.sub}</div>}
      </div>
    </div>
  );
};

// An icon card that takes over the caption plate for a moment (the face stays clear).
export const PlateCard: React.FC<{ o: Pill; t: number }> = ({ o, t }) => {
  const { fps } = useVideoConfig();
  const f = Math.round((t - o.in) * fps);
  const dur = Math.round((o.out - o.in) * fps);
  const pop = spring({ frame: f, fps, config: { damping: 12, stiffness: 200, mass: 0.6 } });
  const draw = interpolate(f, [3, 18], [0, 1], clamp01);
  const txt = spring({ frame: f - 4, fps, config: { damping: 16, stiffness: 180 } });
  const exit = interpolate(f, [dur - 6, dur], [1, 0], clamp01);
  const ink = T.primary;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 28, opacity: exit, maxWidth: 900 }}>
      <div style={{ position: "relative", flex: "0 0 auto", width: 128, height: 128, borderRadius: 64, background: T.accentSoft, border: `4px solid ${T.accent}`, transform: `scale(${pop})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width={74} height={74} viewBox="0 0 24 24" fill="none" stroke={ink} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          {(ICONS[o.icon ?? "heart"] ?? []).map((d, i) => {
            const common = { key: i, pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - draw };
            if (d.startsWith("c:")) {
              const [cx, cy, r] = d.slice(2).split(",").map(Number);
              return <circle {...common} cx={cx} cy={cy} r={r} />;
            }
            return <path {...common} d={d} />;
          })}
        </svg>
        {o.badge && (
          <div style={{ position: "absolute", top: -6, right: -6, width: 42, height: 42, borderRadius: 21, background: ink, color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 24, display: "flex", alignItems: "center", justifyContent: "center" }}>{o.badge}</div>
        )}
      </div>
      <div style={{ textAlign: "left", transform: `translateX(${(1 - txt) * 30}px)`, opacity: txt }}>
        {o.label && <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 24, letterSpacing: 3, color: rgba(ink, 0.75), marginBottom: 4 }}>{o.label}</div>}
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 54, lineHeight: 1.06, color: ink }}>{o.parts.map(([x]) => x).join("")}</div>
        {o.sub && <div style={{ fontFamily: FONT, fontWeight: 500, fontSize: 30, lineHeight: 1.2, color: rgba(ink, 0.85), marginTop: 6 }}>{o.sub}</div>}
      </div>
    </div>
  );
};

// Full-screen closing card over the held last frame: question, offer, nudge.
export const EndCard: React.FC<{ o: Pill }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bg = interpolate(frame, [0, 10], [0, 1], clamp01);
  const lines: string[] = (o as any).lines ?? [];
  return (
    <div style={{ position: "absolute", inset: 0, background: `linear-gradient(180deg, ${rgba("#F7FCF9", 0.97)} 0%, ${rgba(T.accentSoft, 0.98)} 100%)`, opacity: bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "0 90px", gap: 34, textAlign: "center" }}>
      {lines.map((ln, i) => {
        const k = spring({ frame: frame - 6 - i * 10, fps, config: { damping: 15, stiffness: 160 } });
        const tag = ln.startsWith("#");
        const big = ln.startsWith("!");
        const text = tag || big ? ln.slice(1) : ln;
        return (
          <div
            key={i}
            style={{
              opacity: k,
              transform: `translateY(${(1 - k) * 30}px)`,
              fontFamily: FONT,
              fontWeight: tag ? 800 : big ? 900 : 600,
              fontSize: tag ? 28 : big ? 66 : 44,
              letterSpacing: tag ? 4 : 0,
              lineHeight: 1.18,
              color: T.primary,
              padding: tag ? "8px 22px" : 0,
              borderRadius: 20,
              background: tag ? "#FFFFFF" : "transparent",
            }}
          >
            {text}
          </div>
        );
      })}
    </div>
  );
};
