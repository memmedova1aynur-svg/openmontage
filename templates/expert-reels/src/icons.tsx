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
        ...(centre ? { left: "50%", maxWidth: 900, whiteSpace: "nowrap", translate: "-50% 0" } : { [right ? "right" : "left"]: 36 }),
        display: "flex",
        flexDirection: right ? "row-reverse" : "row",
        alignItems: "center",
        gap: 14,
        ...(centre ? {} : { maxWidth: 370 }),
        opacity: exit,
        transform: `translateY(${float}px)`,
      }}
    >
      <div style={{ position: "relative", flex: "0 0 auto", width: 96, height: 96, borderRadius: 48, background: rgba(T.accentSoft, 0.97), boxShadow: `0 8px 22px ${rgba(ink, 0.18)}`, border: `3px solid ${rgba(T.accent, 0.9)}`, transform: `scale(${pop})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width={56} height={56} viewBox="0 0 24 24" fill="none" stroke={ink} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
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
      <div
        style={{
          padding: "8px 14px 10px",
          borderRadius: 16,
          background: "rgba(255,255,255,0.88)",
          textAlign: right ? "right" : "left",
          transform: `translateX(${(1 - label) * (right ? 30 : -30)}px)`,
          opacity: label,
        }}
      >
        <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 31, lineHeight: 1.12, color: ink }}>{text}</div>
        {o.sub && <div style={{ fontFamily: FONT, fontWeight: 500, fontSize: 25, lineHeight: 1.2, color: rgba(ink, 0.8), marginTop: 3 }}>{o.sub}</div>}
      </div>
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
            ? { textShadow: "0 0 14px rgba(255,255,255,0.95), 0 0 4px rgba(255,255,255,0.9)" }
            : { padding: "16px 34px 20px", borderRadius: 28, background: "rgba(255,255,255,0.93)", boxShadow: `0 12px 34px ${rgba(T.primary, 0.18)}` }),
        }}
      >
        {o.label && (
          <div style={{ display: "inline-block", padding: "5px 16px", borderRadius: 20, background: T.accentSoft, fontFamily: FONT, fontWeight: 800, fontSize: 22, letterSpacing: 3, color: T.primary, marginBottom: 8 }}>{o.label}</div>
        )}
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: o.small ? 44 : 50, lineHeight: 1.08, color: T.primary }}>{o.parts.map(([t]) => t).join("")}</div>
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
