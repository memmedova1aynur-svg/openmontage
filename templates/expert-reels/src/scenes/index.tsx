import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { E, EMPH, FONT, T, clamp01, rgba } from "../theme";

// Every cutaway scene leaves the corner held by the speaker circle free:
// content lives in y 300..880 across the full width, plus the lower area on
// the side opposite the circle (see PIP_SIDE).
export const PIP_SIDE = E.style.pipCorner === "bl" ? "left" : "right";
const FREE_X = PIP_SIDE === "right" ? 56 : 1080 - 56 - 560; // lower free column

type SceneProps = { f: number; p: Record<string, any>; startT: number };

// "word **accent** word" -> spans with accent colour
// onAccent: the text sits on an accent-coloured surface, so emphasis becomes an underline
export const Rich: React.FC<{ text: string; onAccent?: boolean }> = ({ text, onAccent }) => (
  <>
    {text.split(/(\*\*[^*]+\*\*)/).map((chunk, i) =>
      chunk.startsWith("**") ? (
        <span key={i} style={onAccent ? { textDecoration: "underline", textDecorationThickness: 5, textUnderlineOffset: 6 } : { color: EMPH }}>
          {chunk.slice(2, -2)}
        </span>
      ) : (
        <React.Fragment key={i}>{chunk}</React.Fragment>
      ),
    )}
  </>
);

// item i appears at p.times[i] (absolute seconds) when given, else staggered
const appearFrame = (p: Record<string, any>, i: number, startT: number, fps: number, first: number, gap: number) =>
  Array.isArray(p.times) && p.times[i] !== undefined ? Math.round((p.times[i] - startT) * fps) : first + i * gap;

const Header: React.FC<{ f: number; label?: string; title?: string; align?: "center" | "left"; top?: number; left?: number; width?: number }> = ({
  f,
  label,
  title,
  align = "center",
  top = 330,
  left = 0,
  width = 1080,
}) => {
  const { fps } = useVideoConfig();
  const s = spring({ frame: f - 2, fps, config: { damping: 14, stiffness: 160 } });
  return (
    <div style={{ position: "absolute", top, left, width, textAlign: align, transform: `translateY(${(1 - s) * -40}px)`, opacity: s }}>
      {label && <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 30, letterSpacing: 6, color: T.accent }}>{label}</div>}
      {title && (
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 62, color: T.text, lineHeight: 1.1, marginTop: 10, whiteSpace: "pre-line" }}>
          <Rich text={title} />
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------- timeline
// props: label, title, steps ["AY|1", ...] (top|big), footer, footerAt (abs s), times[]
export const Timeline: React.FC<SceneProps> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const steps: string[] = p.steps;
  const n = steps.length;
  const perRow = n <= 3 ? n : Math.ceil(n / 2);
  const xs = (k: number) => (perRow === 1 ? [540] : Array.from({ length: k }, (_, i) => 200 + (680 / (perRow - 1)) * i));
  const row1 = xs(perRow).map((x) => [x, 600]);
  const row2 = xs(n - perRow)
    .map((_, i) => [row1[perRow - 1 - i][0], 820])
    .slice(0, n - perRow);
  const nodes = [...row1, ...row2];
  let path = `M${nodes[0][0]} ${nodes[0][1]}`;
  nodes.slice(1).forEach(([x, y], i) => {
    const [px, py] = nodes[i];
    path += py !== y ? ` C${px + 110} ${py} ${px + 110} ${y} ${x} ${y}` : ` L${x} ${y}`;
  });
  const lit = nodes.map((_, i) => appearFrame(p, i, startT, fps, 18, 16));
  const draw = interpolate(f, [12, lit[n - 1]], [0, 1], clamp01);
  const footerF = p.footerAt !== undefined ? Math.round((p.footerAt - startT) * fps) : lit[n - 1] + 12;
  const goal = spring({ frame: f - footerF, fps, config: { damping: 12, stiffness: 170 } });
  return (
    <AbsoluteFill>
      <Header f={f} label={p.label} title={p.title} />
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        <path d={path} fill="none" stroke={rgba(T.text, 0.15)} strokeWidth={10} strokeLinecap="round" />
        <path d={path} fill="none" stroke={T.accent} strokeWidth={10} strokeLinecap="round" strokeDasharray={2400} strokeDashoffset={2400 * (1 - draw)} />
      </svg>
      {nodes.map(([x, y], i) => {
        const on = spring({ frame: f - lit[i], fps, config: { damping: 9, stiffness: 240, mass: 0.6 } });
        const [top, big] = steps[i].includes("|") ? steps[i].split("|") : ["", steps[i]];
        const live = on > 0.05;
        return (
          <div key={i} style={{ position: "absolute", left: x - 60, top: y - 60, width: 120, height: 120 }}>
            <div
              style={{
                width: 120,
                height: 120,
                borderRadius: 60,
                background: live ? T.accent : rgba(T.text, 0.06),
                border: `6px solid ${live ? T.text : rgba(T.text, 0.25)}`,
                transform: `scale(${0.7 + 0.3 * Math.min(on, 1.15)})`,
                boxShadow: live ? `0 0 ${40 * on}px ${rgba(T.accent, 0.65)}` : "none",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: FONT,
                color: live ? T.onAccent : rgba(T.text, 0.6),
              }}
            >
              {top && <div style={{ fontWeight: 700, fontSize: 22, letterSpacing: 2 }}>{top}</div>}
              <div style={{ fontWeight: 900, fontSize: big.length > 2 ? 30 : 46, lineHeight: 1 }}>{big}</div>
            </div>
          </div>
        );
      })}
      {p.footer && (
        <div
          style={{
            position: "absolute",
            left: FREE_X,
            top: 945,
            padding: "14px 24px",
            borderRadius: 22,
            background: rgba(T.text, 0.08),
            border: `2px solid ${T.accent}`,
            fontFamily: FONT,
            fontWeight: 800,
            fontSize: 34,
            color: T.text,
            opacity: goal,
            transform: `translateY(${(1 - goal) * 30}px)`,
          }}
        >
          <Rich text={p.footer} />
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- phone
// props: label, title, checks[], times[] (for checks), tiles (count, default 9)
export const Phone: React.FC<SceneProps> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const phoneLeft = PIP_SIDE === "right" ? 90 : 520;
  const textLeft = PIP_SIDE === "right" ? 610 : 60;
  const tiles = p.tiles ?? 9;
  const palette = [T.accent, rgba(T.text, 0.18), T.accentSoft, rgba(T.text, 0.08)];
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: phoneLeft,
          top: 330,
          width: 470,
          height: 900,
          borderRadius: 64,
          background: T.primaryDeep,
          border: `10px solid ${rgba(T.text, 0.18)}`,
          boxShadow: "0 30px 80px rgba(0,0,0,0.5)",
          overflow: "hidden",
        }}
      >
        <div style={{ width: 150, height: 30, borderRadius: 15, background: "#000", margin: "16px auto 0" }} />
        <div style={{ display: "flex", alignItems: "center", padding: "26px 26px 10px" }}>
          <div style={{ width: 104, height: 104, borderRadius: 52, padding: 5, background: `linear-gradient(45deg, ${T.accent}, #E1306C, #833AB4)` }}>
            <div style={{ width: "100%", height: "100%", borderRadius: 50, background: T.primary, border: `4px solid ${T.primaryDeep}` }} />
          </div>
          <div style={{ display: "flex", flex: 1, justifyContent: "space-around", fontFamily: FONT, color: T.text, textAlign: "center" }}>
            {["Post", "İzləyici", "İzlənən"].map((l, i) => (
              <div key={l}>
                <div style={{ width: 44, height: 22, borderRadius: 6, margin: "0 auto 6px", background: rgba(T.text, 0.8), opacity: interpolate(f, [8 + i * 3, 14 + i * 3], [0, 1], clamp01) }} />
                <div style={{ fontSize: 16, fontWeight: 600, opacity: 0.8 }}>{l}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ padding: "6px 26px 18px" }}>
          {[230, 300, 180].map((w, i) => (
            <div key={i} style={{ width: w, height: 14, borderRadius: 7, marginTop: 10, background: i === 0 ? T.text : rgba(T.text, 0.35), opacity: interpolate(f, [10 + i * 3, 16 + i * 3], [0, 1], clamp01) }} />
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 4, padding: "0 4px" }}>
          {Array.from({ length: tiles }, (_, i) => {
            const s = spring({ frame: f - 16 - i * 4.2, fps, config: { damping: 11, stiffness: 220, mass: 0.5 } });
            return (
              <div key={i} style={{ aspectRatio: "3 / 4", background: palette[(i * 7) % palette.length], transform: `scale(${s})`, opacity: Math.min(1, s), display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, color: rgba(T.text, 0.85) }}>
                {i % 3 === 1 ? "▶" : ""}
              </div>
            );
          })}
        </div>
      </div>
      <div style={{ position: "absolute", left: textLeft, top: 380, width: 420 }}>
        {p.label && <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 30, letterSpacing: 6, color: T.accent }}>{p.label}</div>}
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 56, color: T.text, lineHeight: 1.1, margin: "10px 0 30px" }}>
          <Rich text={p.title ?? "Instagram"} />
        </div>
        {(p.checks ?? []).map((c: string, i: number) => <Check key={c} f={f} at={appearFrame(p, i, startT, fps, 30, 22)} text={c} />)}
      </div>
    </AbsoluteFill>
  );
};

const Check: React.FC<{ f: number; at: number; text: string; size?: number; gap?: number }> = ({ f, at, text, size = 32, gap = 22 }) => {
  const { fps } = useVideoConfig();
  const s = spring({ frame: f - at, fps, config: { damping: 13, stiffness: 200 } });
  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: gap, opacity: s, transform: `translateX(${(1 - s) * 40}px)` }}>
      <div style={{ width: size * 1.6, height: size * 1.6, borderRadius: 14, background: T.accent, color: T.onAccent, fontSize: size * 1.05, fontWeight: 900, fontFamily: FONT, display: "flex", alignItems: "center", justifyContent: "center", marginRight: 16, flexShrink: 0 }}>✓</div>
      <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: size, color: T.text, lineHeight: 1.15 }}>
        <Rich text={text} />
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- checklist
// props: label, title, items[], times[]
export const Checklist: React.FC<SceneProps> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Header f={f} label={p.label} title={p.title} />
      <div style={{ position: "absolute", left: 90, top: 530, width: 900 }}>
        {(p.items as string[]).map((it, i) => (
          <Check key={i} f={f} at={appearFrame(p, i, startT, fps, 14, 14)} text={it} size={p.items.length <= 3 ? 46 : 36} gap={p.items.length <= 3 ? 28 : 16} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- chat
// props: label, title, messages [{from: "me"|"them", text}], times[]
export const Chat: React.FC<SceneProps> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const msgs: { from: string; text: string }[] = p.messages;
  return (
    <AbsoluteFill>
      <Header f={f} label={p.label} title={p.title} />
      <div style={{ position: "absolute", left: 70, right: 70, top: 540, display: "flex", flexDirection: "column", gap: 22 }}>
        {msgs.map((m, i) => {
          const at = appearFrame(p, i, startT, fps, 14, 26);
          const typing = f >= at - 14 && f < at;
          const s = spring({ frame: f - at, fps, config: { damping: 12, stiffness: 210, mass: 0.6 } });
          const me = m.from === "me";
          if (f < at - 14) return null;
          return (
            <div key={i} style={{ alignSelf: me ? "flex-end" : "flex-start", maxWidth: 720 }}>
              <div
                style={{
                  padding: "22px 30px",
                  borderRadius: 36,
                  borderBottomRightRadius: me ? 8 : 36,
                  borderBottomLeftRadius: me ? 36 : 8,
                  background: me ? T.accent : rgba(T.text, 0.12),
                  color: me ? T.onAccent : T.text,
                  fontFamily: FONT,
                  fontWeight: 700,
                  fontSize: 36,
                  lineHeight: 1.25,
                  transform: `scale(${typing ? 1 : 0.85 + 0.15 * s})`,
                  transformOrigin: me ? "100% 100%" : "0% 100%",
                }}
              >
                {typing ? <span style={{ letterSpacing: 6 }}>{".".repeat(1 + (Math.floor(f / 5) % 3))}</span> : <Rich text={m.text} onAccent={me} />}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- questions
// props: questions[], times[]  (floating thought bubbles, scattered)
export const Questions: React.FC<SceneProps> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const spots = [
    [90, 380, -3],
    [330, 560, 2],
    [120, 740, -2],
    [380, 900, 3],
  ];
  return (
    <AbsoluteFill>
      {(p.questions as string[]).map((q, i) => {
        const at = appearFrame(p, i, startT, fps, 4, 18);
        const s = spring({ frame: f - at, fps, config: { damping: 10, stiffness: 200, mass: 0.6 } });
        const [x, y, rot] = spots[i % spots.length];
        const bob = Math.sin((f + i * 20) / 18) * 6;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: PIP_SIDE === "right" ? x : 1080 - x - 620,
              top: y + bob,
              maxWidth: 620,
              padding: "24px 32px",
              borderRadius: 40,
              background: i % 2 ? rgba(T.text, 0.12) : T.accent,
              color: i % 2 ? T.text : T.onAccent,
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 40,
              lineHeight: 1.2,
              opacity: Math.min(1, s * 1.4),
              transform: `scale(${0.6 + 0.4 * s}) rotate(${rot * s}deg)`,
              boxShadow: "0 18px 40px rgba(0,0,0,0.35)",
            }}
          >
            <Rich text={q} onAccent={i % 2 === 0} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- stat
// props: label, value (number), prefix, suffix, caption, countSeconds
export const Stat: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const dur = Math.round((p.countSeconds ?? 1.2) * fps);
  const v = interpolate(f, [6, 6 + dur], [0, p.value], { ...clamp01, easing: (x) => 1 - Math.pow(1 - x, 3) });
  const s = spring({ frame: f, fps, config: { damping: 12, stiffness: 160 } });
  return (
    <AbsoluteFill>
      <Header f={f} label={p.label} />
      <div style={{ position: "absolute", top: 420, width: "100%", textAlign: "center", transform: `scale(${0.7 + 0.3 * s})`, opacity: s }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 220, color: T.accent, lineHeight: 1 }}>
          {p.prefix ?? ""}
          {Number.isInteger(p.value) ? Math.round(v) : v.toFixed(1)}
          {p.suffix ?? ""}
        </div>
        {p.caption && (
          <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 48, color: T.text, marginTop: 24, padding: "0 80px" }}>
            <Rich text={p.caption} />
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

export const SCENES: Record<string, React.FC<SceneProps>> = {
  timeline: Timeline,
  phone: Phone,
  checklist: Checklist,
  chat: Chat,
  questions: Questions,
  stat: Stat,
};

// ---------------------------------------------------------------- comment CTA
// Speaker stays full screen; an Instagram-style comment bar types the keyword.
// props: hint, keyword, avatar, type_start, type_end, send (absolute seconds)
export const CommentCTA: React.FC<{ p: Record<string, any>; startT: number }> = ({ p, startT }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const f = frame - Math.round(startT * fps);
  const enter = spring({ frame: f, fps, config: { damping: 13, stiffness: 170, mass: 0.7 } });
  const word: string = p.keyword;
  const typed = Math.floor(interpolate(t, [p.type_start, p.type_end], [0, word.length], clamp01));
  const sent = t >= p.send;
  const sendPop = spring({ frame: Math.round((t - p.send) * fps), fps, config: { damping: 8, stiffness: 260, mass: 0.5 } });
  const caret = Math.floor(frame / 8) % 2 === 0;
  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div style={{ marginTop: 300, transform: `translateY(${(1 - enter) * -120}px) scale(${0.85 + 0.15 * enter})`, opacity: Math.min(1, enter * 1.5), position: "relative" }}>
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 34, color: "#fff", textAlign: "center", marginBottom: 16, textShadow: "0 4px 14px rgba(0,0,0,0.6)" }}>
          <Rich text={p.hint ?? "Şərhlərdə **yaz** 👇"} />
        </div>
        <div style={{ width: 940, height: 132, borderRadius: 66, background: "#fff", display: "flex", alignItems: "center", padding: "0 18px", boxShadow: "0 18px 50px rgba(0,0,0,0.4)", transform: `scale(${sent ? 1 + 0.05 * (1 - Math.min(1, sendPop)) : 1})` }}>
          <div style={{ width: 92, height: 92, borderRadius: 46, background: T.primary, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 50 }}>{p.avatar ?? "🙋‍♀️"}</div>
          <div style={{ flex: 1, marginLeft: 24, fontFamily: FONT, fontSize: word.length > 12 ? 40 : 48, fontWeight: typed ? 900 : 600, color: typed ? T.primary : "#9AA3B2", letterSpacing: typed ? 1 : 0 }}>
            {typed ? word.slice(0, typed) : "Şərh yaz..."}
            {!sent && t >= p.type_start - 0.4 && <span style={{ color: T.accent, opacity: caret ? 1 : 0 }}>|</span>}
          </div>
          <div style={{ padding: "18px 30px", borderRadius: 40, background: typed === word.length ? T.accent : "#E5E8EE", fontFamily: FONT, fontWeight: 900, fontSize: 34, color: T.onAccent, transform: `scale(${sent ? 1 + 0.25 * Math.max(0, 1 - sendPop) * Math.sin(sendPop * 6) : 1})` }}>
            Paylaş
          </div>
        </div>
        {sent &&
          [0, 1, 2, 3, 4].map((i) => {
            const k = Math.max(0, t - p.send) * fps;
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: 760 + (i - 2) * 46 + Math.sin(k / 5 + i) * 18,
                  top: 150 - k * (6 + i * 1.3),
                  fontSize: 56 + i * 6,
                  opacity: interpolate(k, [0, 4, 16], [0, 1, 0.2], { extrapolateRight: "clamp" }),
                  transform: `scale(${Math.min(1.2, sendPop)})`,
                }}
              >
                ❤️
              </div>
            );
          })}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- backdrops
export const Backdrop: React.FC<{ p: number }> = ({ p }) => {
  const frame = useCurrentFrame();
  const base = `radial-gradient(120% 80% at 30% 20%, ${T.primary} 0%, ${T.primary} 45%, ${T.primaryDeep} 100%)`;
  let layer: React.CSSProperties = {};
  switch (E.style.backdrop) {
    case "grid":
      layer = {
        backgroundImage: `linear-gradient(${rgba(T.accent, 0.12)} 2px, transparent 2px), linear-gradient(90deg, ${rgba(T.accent, 0.12)} 2px, transparent 2px)`,
        backgroundSize: "90px 90px",
        backgroundPosition: `0px ${frame * 1.2}px`,
      };
      break;
    case "diagonal":
      layer = {
        backgroundImage: `repeating-linear-gradient(135deg, ${rgba(T.accent, 0.08)} 0 26px, transparent 26px 70px)`,
        backgroundPosition: `${frame * 1.5}px 0px`,
      };
      break;
    case "orbs":
      layer = {
        backgroundImage: `radial-gradient(circle at ${30 + Math.sin(frame / 40) * 10}% ${30 + Math.cos(frame / 50) * 8}%, ${rgba(T.accent, 0.35)} 0, transparent 28%), radial-gradient(circle at ${75 + Math.cos(frame / 45) * 8}% ${70 + Math.sin(frame / 35) * 8}%, ${rgba(T.accentSoft, 0.25)} 0, transparent 30%)`,
      };
      break;
    default:
      layer = {
        backgroundImage: `radial-gradient(${rgba(T.accent, 0.18)} 2px, transparent 2.5px)`,
        backgroundSize: "54px 54px",
        backgroundPosition: `${frame * 0.6}px ${frame * 0.9}px`,
      };
  }
  return (
    <AbsoluteFill style={{ opacity: Math.min(1, p), background: base }}>
      <AbsoluteFill style={{ ...layer, opacity: 0.7 }} />
    </AbsoluteFill>
  );
};
