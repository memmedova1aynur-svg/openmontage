import React from "react";
import {
  AbsoluteFill,
  Audio,
  Composition,
  Freeze,
  OffthreadVideo,
  Sequence,
  interpolate,
  registerRoot,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { EndCard, IconChip, PlateCard, TitleCard } from "./icons";
import { CARTOON } from "./cartoon";
import { CounterPop, SKETCH } from "./sketch";
import { PAPER, Paper, RetroOverlay, Strip } from "./paper";
import { ILLUSTRATED } from "./illustrations";
import { BLUEPRINT, BpNote, BpSpark } from "./blueprint";
import { CallCard, Marker, SHEET, Ticket } from "./sheet";
import { Backdrop, CommentCTA, PIP_SIDE, SCENES } from "./scenes";
import { Cutaway, E, EMPH, FONT, FONT_HAND, FPS, Page, Pill, T, ZoomKey, clamp01, rgba, useFonts } from "./theme";

// Point of the speaker the full-frame zoom pushes toward (x, y in 1080x1920).
const FACE = { x: 540, y: 0.36 * 1920 };

// ---------------------------------------------------------------- zoom
const zoomAt = (t: number, fps: number): number => {
  const keys = E.zoom;
  let i = 0;
  while (i + 1 < keys.length && keys[i + 1].t <= t) i++;
  const cur = keys[i];
  const prev = i > 0 ? keys[i - 1] : cur;
  const local = t - cur.t;
  const next = i + 1 < keys.length ? keys[i + 1].t : E.duration;
  // slow drift inside every shot keeps the frame alive
  const drift = 0.018 * Math.min(1, local / Math.max(0.5, next - cur.t));
  if (cur.k === "cut") return cur.s + drift;
  const prog = spring({
    frame: Math.round(local * fps),
    fps,
    config: cur.k === "punch" ? { damping: 11, stiffness: 260, mass: 0.6 } : { damping: 18, stiffness: 120, mass: 0.9 },
  });
  return prev.s + (cur.s - prev.s) * prog + drift;
};

const punchShake = (t: number) => {
  const p = E.zoom.find((k: ZoomKey) => k.k === "punch" && t >= k.t && t < k.t + 0.18);
  if (!p) return 0;
  const local = (t - p.t) / 0.18;
  return Math.sin(local * Math.PI * 6) * (1 - local) * 6;
};

const pipAt = (t: number, fps: number) => {
  const c = E.cutaways.find((c: Cutaway) => (c.kind === "pip" || c.kind === "full" || c.kind === "scene") && t >= c.in - 0.01 && t < c.out + 0.6);
  if (!c) return { p: 0, c: undefined };
  const cfg = { damping: 16, stiffness: 140, mass: 0.8 };
  const enter = spring({ frame: Math.round((t - c.in) * fps), fps, config: cfg });
  const exit = t >= c.out ? spring({ frame: Math.round((t - c.out) * fps), fps, config: cfg }) : 0;
  return { p: Math.max(0, Math.min(1.04, enter - exit)), c };
};

// ---------------------------------------------------------------- captions
// Fixed light panel with calm captions inside. It stays on screen the whole video, so it can also
// hide burned-in text or a distracting area low in the frame without anything jumping in and out.
const PlateCaptions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const pl = E.plate ?? { y: 1570, h: 280, x: 60 };
  const card = E.overlays.find((o) => o.plate && t >= o.in && t < o.out);
  const page = card ? undefined : E.pages.find((p: Page) => t >= p.start && t < p.end);
  const enter = page ? spring({ frame: Math.round((t - page.start) * fps), fps, config: { damping: 18, stiffness: 200, mass: 0.6 } }) : 0;
  const settle = interpolate(frame, [0, 10], [0, 1], clamp01);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: pl.y,
          left: pl.x,
          right: pl.x,
          height: pl.h,
          borderRadius: 44,
          background: "rgba(255,255,255,0.97)",
          borderTop: `10px solid ${T.accentSoft}`,
          boxShadow: "0 18px 50px rgba(0,0,0,0.18)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 40px",
          opacity: settle,
        }}
      >
        {(E.tabs ?? [])
          .filter((tb) => t >= tb.in && t < tb.out)
          .map((tb) => {
            const k = spring({ frame: Math.round((t - tb.in) * fps), fps, config: { damping: 14, stiffness: 180 } });
            const out = interpolate(t, [tb.out - 0.25, tb.out], [1, 0], clamp01);
            return (
              <div
                key={tb.in}
                style={{
                  position: "absolute",
                  top: tb.cta ? -66 : -52,
                  left: "50%",
                  transform: `translateX(-50%) translateY(${(1 - k) * 24}px)`,
                  opacity: Math.min(1, k * 1.5) * out,
                  whiteSpace: "nowrap",
                  padding: tb.cta ? "12px 30px" : "9px 24px",
                  borderRadius: 30,
                  background: T.primary,
                  color: "#FFFFFF",
                  fontFamily: FONT,
                  fontWeight: tb.cta ? 800 : 600,
                  fontSize: tb.cta ? 36 : 29,
                  boxShadow: `0 8px 20px ${rgba(T.primary, 0.3)}`,
                }}
              >
                {tb.text}
              </div>
            );
          })}
        {card && <PlateCard o={card} t={t} />}
        {page && (
          <div style={{ textAlign: "center", lineHeight: 1.18, transform: `translateY(${(1 - enter) * 14}px)`, opacity: Math.min(1, enter * 1.6) }}>
            {page.words.map((w, i) => {
              const active = t >= w.s && t < Math.max(w.e, w.s + 0.12);
              const spoken = t >= w.s;
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    margin: "0 10px",
                    padding: "0 12px",
                    borderRadius: 14,
                    background: active ? T.accentSoft : "transparent",
                    fontFamily: FONT,
                    fontWeight: 800,
                    fontSize: 64,
                    color: T.primary,
                    opacity: spoken ? 1 : 0.4,
                  }}
                >
                  {w.w}
                </span>
              );
            })}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const page = E.pages.find((p: Page) => t >= p.start && t < p.end);
  if (E.style.captions === "plate") return <PlateCaptions />;
  if (!page) return null;
  if (E.style.captions === "paper") {
    const k = spring({ frame: Math.round((t - page.start) * fps), fps, config: { damping: 12, stiffness: 240, mass: 0.5 } });
    const inScene = E.cutaways.some((c) => (c.kind === "split" || c.kind === "scene") && t >= c.in && t < c.out);
    const idx = E.pages.indexOf(page);
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: inScene ? 230 : 430 }}>
        <div style={{ transform: `translateY(${(1 - k) * 30}px) scale(${0.9 + 0.1 * k})`, opacity: Math.min(1, k * 2) }}>
          <Paper color="#FFFDF7" seed={idx + 3} rot={idx % 2 ? 1.5 : -1.5}>
            <div style={{ textAlign: "center", lineHeight: 1.1, maxWidth: 900 }}>
              {page.words.map((w, i) => {
                const active = t >= w.s && t < Math.max(w.e, w.s + 0.12);
                const spoken = t >= w.s;
                return (
                  <span key={i} style={{ display: "inline-block", margin: "0 10px", fontFamily: FONT, fontWeight: 900, fontSize: 64, color: spoken ? "#1F1B18" : "rgba(31,27,24,0.4)", backgroundImage: active ? "linear-gradient(transparent 60%, rgba(244,200,90,0.85) 60%)" : undefined }}>
                    {w.w}
                  </span>
                );
              })}
            </div>
          </Paper>
        </div>
      </AbsoluteFill>
    );
  }
  const enter = spring({ frame: Math.round((t - page.start) * fps), fps, config: { damping: 14, stiffness: 220, mass: 0.6 } });
  const style = E.style.captions;
  if (style === "lower" || style === "marker") return <AltCaptions page={page} t={t} enter={enter} style={style} />;
  // box captions keep their own dark backing, so only bare captions switch colour over pale cutaways
  const onPale = !!T.light && style !== "box" && pipAt(t, fps).p > 0.5;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: E.cutaways.some((c) => (c.kind === "split" || c.kind === "scene") && t >= c.in && t < c.out) ? 230 : 430 }}>
      <div
        style={{
          maxWidth: 940,
          textAlign: "center",
          lineHeight: 1.12,
          padding: style === "box" ? "14px 26px 18px" : style === "frame" ? "16px 30px 20px" : 0,
          borderRadius: style === "frame" ? 0 : 26,
          background: style === "box" ? (T.light ? rgba(T.accent, 0.9) : rgba(T.primary, 0.82)) : style === "frame" ? rgba(T.primary, 0.86) : "transparent",
          position: "relative",
          transform: style === "frame" ? `translateY(${(1 - enter) * 18}px)` : `translateY(${(1 - enter) * 26}px) scale(${0.86 + 0.14 * enter}) rotate(${(1 - enter) * -2.5}deg)`,
          opacity: Math.min(1, enter * 1.6),
        }}
      >
        {page.words.map((w, i) => {
          const active = t >= w.s && t < Math.max(w.e, w.s + 0.12);
          const spoken = t >= w.s;
          const pop = spring({ frame: Math.round((t - w.s) * fps), fps, config: { damping: 10, stiffness: 300, mass: 0.5 } });
          const scale = spoken ? 1 + 0.07 * (1 - pop) * (active ? 1 : 0) + (active ? 0.02 : 0) : 1;
          const chip = style === "chip" && active;
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                margin: "0 20px",
                padding: chip ? "0 14px" : 0,
                borderRadius: 14,
                background: chip ? T.accent : "transparent",
                fontFamily: FONT,
                fontWeight: 900,
                fontSize: 74,
                letterSpacing: -0.5,
                color: chip ? T.onAccent : active ? ((style === "box" || style === "frame") && T.light ? T.accentSoft : T.accent) : onPale ? T.text : "#FFFFFF",
                opacity: spoken ? 1 : 0.55,
                transform: `scale(${scale})`,
                WebkitTextStroke: style === "box" || style === "frame" || chip || onPale ? undefined : "3px rgba(0,0,0,0.85)",
                paintOrder: "stroke fill",
                textShadow: onPale ? "none" : "0 6px 18px rgba(0,0,0,0.55)",
                backgroundImage: (style === "box" || style === "frame") && active ? `linear-gradient(${T.accentSoft}, ${T.accentSoft})` : undefined,
                backgroundRepeat: "no-repeat",
                backgroundPosition: "0 100%",
                backgroundSize: (style === "box" || style === "frame") && active ? `${100 * Math.min(1, pop * 1.2)}% 6px` : undefined,
              }}
            >
              {w.w}
            </span>
          );
        })}
        {style === "frame" && <FrameTicks k={enter} />}
      </div>
    </AbsoluteFill>
  );
};

// "lower": white type on a soft dark band across the lower frame, active word in the brand blue
// "marker": white type, the active word sits on a brand-blue highlighter swipe (navy type)
const AltCaptions: React.FC<{ page: Page; t: number; enter: number; style: "lower" | "marker" }> = ({ page, t, enter, style }) => {
  const inScene = E.cutaways.some((c) => (c.kind === "split" || c.kind === "scene") && t >= c.in && t < c.out);
  const lower = style === "lower";
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: inScene ? 230 : 430 }}>
      {lower && !inScene && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 300, height: 380, background: `linear-gradient(180deg, ${rgba(T.primaryDeep, 0)} 0%, ${rgba(T.primaryDeep, 0.62)} 45%, ${rgba(T.primaryDeep, 0.62)} 75%, ${rgba(T.primaryDeep, 0)} 100%)` }} />
      )}
      <div style={{ position: "relative", maxWidth: 960, textAlign: "center", lineHeight: 1.16, transform: `translateY(${(1 - enter) * 16}px)`, opacity: Math.min(1, enter * 1.8) }}>
        {page.words.map((w, i) => {
          const active = t >= w.s && t < Math.max(w.e, w.s + 0.12);
          const spoken = t >= w.s;
          const onPaper = inScene && !lower;
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                margin: "0 8px",
                padding: style === "marker" ? "0 10px" : 0,
                borderRadius: 6,
                fontFamily: FONT,
                fontWeight: lower ? 700 : 900,
                fontSize: lower ? 66 : 72,
                letterSpacing: lower ? 0 : -0.5,
                color: style === "marker" && active ? T.primary : lower && active ? T.accent : onPaper ? T.primary : "#FFFFFF",
                opacity: spoken ? 1 : lower ? 0.6 : 0.5,
                background: style === "marker" && active ? T.accent : "transparent",
                transform: style === "marker" && active ? "rotate(-1.5deg)" : undefined,
                textShadow: style === "marker" && active ? "none" : onPaper ? "none" : "0 3px 12px rgba(0,0,0,0.6), 0 1px 3px rgba(0,0,0,0.5)",
              }}
            >
              {w.w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// corner brackets around the "frame" caption panel
const FrameTicks: React.FC<{ k: number }> = ({ k }) => {
  const l = 26 * k;
  const w = `5px solid ${T.accent}`;
  const c = (pos: React.CSSProperties) => <div style={{ position: "absolute", width: l, height: l, ...pos }} />;
  return (
    <>
      {c({ left: -12, top: -12, borderLeft: w, borderTop: w })}
      {c({ right: -12, top: -12, borderRight: w, borderTop: w })}
      {c({ right: -12, bottom: -12, borderRight: w, borderBottom: w })}
      {c({ left: -12, bottom: -12, borderLeft: w, borderBottom: w })}
    </>
  );
};

// ---------------------------------------------------------------- keyword pops
// Short emphasised words that bounce in around the speaker (top / left / right),
// for talking-only videos where cards and cutaways would be too much.
const POP_POS: Record<string, { box: React.CSSProperties; rot: number }> = {
  t: { box: { top: 330, left: 0, right: 0, display: "flex", justifyContent: "center" }, rot: -2 },
  tl: { box: { top: 400, left: 50 }, rot: -5 },
  tr: { box: { top: 400, right: 50 }, rot: 5 },
  // side pops are anchored by their bottom edge so a long one grows upward, never into the captions (box top ~y 1375)
  l: { box: { bottom: 600, left: 40 }, rot: -3 },
  r: { box: { bottom: 600, right: 40 }, rot: 3 },
};

// a pop with `top` sits on a row: centred, or pinned to the left / right edge with `side`
const rowPos = (o: Pill): React.CSSProperties =>
  o.side === "l" ? { top: o.top, left: 40 } : o.side === "r" ? { top: o.top, right: 40 } : { top: o.top, left: 0, right: 0, display: "flex", justifyContent: "center" };

// Boxless typography (M02): large white type with a soft shadow, emphasis in the brand colour.
// Calm entrance (rise + fade), no wobble; an optional strike crosses the phrase out.
const TypePop: React.FC<{ o: Pill }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 140, mass: 0.7 } });
  const exit = interpolate(frame, [dur - 8, dur], [1, 0], clamp01);
  const chars = o.parts.map(([txt]) => txt).join("").length;
  const strikeF = o.strike !== undefined ? Math.round((o.strike - o.in) * fps) : null;
  const strike = strikeF === null ? 0 : interpolate(frame, [strikeF, strikeF + 8], [0, 1], clamp01);
  const pos = o.top !== undefined ? rowPos(o) : POP_POS[o.pos ?? "t"].box;
  const words = o.parts.flatMap(([txt, hl]) => txt.split(/(?<= )/).map((w) => ({ w, hl })));
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", ...pos }}>
        <div
          style={{
            position: "relative",
            maxWidth: o.side ? 560 : 960,
            fontFamily: o.hand ? FONT_HAND : FONT,
            fontWeight: o.hand ? 700 : 900,
            fontSize: o.size ?? (o.hand ? (chars > 30 ? 66 : 84) : chars > 22 ? 62 : chars > 14 ? 74 : 88),
            lineHeight: o.hand ? 1.0 : 1.06,
            letterSpacing: o.hand ? 0 : -1,
            textAlign: o.side === "l" ? "left" : o.side === "r" ? "right" : "center",
            color: o.hand || o.ink ? T.primary : T.text,
            textShadow: o.hand || o.ink ? "0 0 18px rgba(255,255,255,0.9), 0 0 4px rgba(255,255,255,0.9)" : "0 4px 18px rgba(0,0,0,0.55), 0 2px 4px rgba(0,0,0,0.5)",
            transform: `translateY(${(1 - enter) * 40}px)`,
            opacity: Math.min(1, enter * 1.6) * exit * (1 - 0.45 * strike),
          }}
        >
          {words.map(({ w, hl }, i) => (
            <span key={i} style={{ display: "inline-block", whiteSpace: "pre", color: o.hand || o.ink ? T.primary : hl ? EMPH : T.text, textDecoration: o.hand && hl ? `underline 6px ${T.accentSoft}` : undefined, textUnderlineOffset: 10 }}>
              {w}
            </span>
          ))}
          {strikeF !== null && (
            <div style={{ position: "absolute", left: -10, top: "52%", height: 9, width: `calc(${strike * 100}% + 20px)`, background: "#E5484D", borderRadius: 5, boxShadow: "0 2px 8px rgba(0,0,0,0.4)" }} />
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const KeywordPop: React.FC<{ o: Pill }> = ({ o }) => {
  const frame = useCurrentFrame();
  const lightPop = E.style.pops === "light";
  const popChars = o.parts.map(([txt]) => txt).join("").length;
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const pos = o.top !== undefined ? { box: rowPos(o), rot: 0 } : POP_POS[o.pos ?? "t"];
  const enter = spring({ frame, fps, config: { damping: 9, stiffness: 220, mass: 0.6 } });
  const exit = interpolate(frame, [dur - 7, dur], [1, 0], clamp01);
  const float = Math.sin(frame / 16) * 6 * Math.min(1, frame / 15);
  const wobble = Math.sin(frame / 9) * 1.2 * Math.max(0, 1 - frame / 30);
  const words = o.parts.flatMap(([txt, hl]) => txt.split(/(?<= )/).map((w) => ({ w, hl })));
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", ...pos.box }}>
        <div
          style={{
            maxWidth: o.small ? 360 : o.pos === "t" ? 900 : 500,
            padding: o.small ? "10px 20px 13px" : "16px 28px 20px",
            borderRadius: 26,
            background: lightPop ? "rgba(255,255,255,0.96)" : rgba(T.primary, 0.92),
            boxShadow: "0 16px 40px rgba(0,0,0,0.4)",
            borderBottom: `${o.small ? 6 : 8}px solid ${lightPop ? T.primary : T.accent}`,
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: o.small ? 38 : popChars > 16 ? 50 : 60,
            lineHeight: 1.08,
            color: T.text,
            textAlign: o.side === "r" || o.pos === "r" || o.pos === "tr" ? "right" : o.side === "l" ? "left" : o.pos === "t" ? "center" : "left",
            transform: `translateY(${float}px) scale(${enter * (0.85 + 0.15 * exit)}) rotate(${pos.rot * enter + wobble}deg)`,
            transformOrigin: o.pos === "r" || o.pos === "tr" ? "100% 50%" : o.pos === "t" ? "50% 50%" : "0% 50%",
            opacity: Math.min(1, enter * 2) * exit,
          }}
        >
          {/* one span per word so long phrases wrap inside the bubble instead of running off-screen */}
          {words.map(({ w, hl }, i) => (
            <span
              key={i}
              style={{
                display: "inline-block",
                whiteSpace: "pre",
                color: lightPop ? T.primary : hl ? EMPH : T.text,
                // on white cards the emphasis is a brand-colour marker stroke instead of coloured text
                background: lightPop && hl ? `linear-gradient(transparent 55%, ${rgba(T.accent, 0.75)} 55%)` : undefined,
              }}
            >
              {w}
            </span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- keyword pills
const PillCard: React.FC<{ o: Pill }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const enter = spring({ frame, fps, config: { damping: 12, stiffness: 180, mass: 0.7 } });
  const exit = interpolate(frame, [dur - 8, dur], [1, 0], clamp01);
  const bar = spring({ frame: frame - 6, fps, config: { damping: 20, stiffness: 120 } });
  const big = o.kind !== "pill";
  const side = E.style.pills === "side-tag" && !big;
  const words = o.parts.flatMap(([txt, hl]) => txt.split(/(?<= )/).map((w) => ({ w, hl })));
  // once in, the card keeps breathing so it never sits dead still
  const settle = Math.min(1, frame / 20);
  const float = Math.sin(frame / 20) * 5 * settle;
  const tilt = side ? 0 : Math.sin(frame / 31) * 0.6 * settle;
  const shine = interpolate(frame, [14, 34], [-40, 140], clamp01);
  const firstHl = words.findIndex((x) => x.hl);
  return (
    <AbsoluteFill style={{ alignItems: side ? "flex-start" : "center" }}>
      <div
        style={{
          marginTop: (E.pillTop ?? 300) + (big ? 0 : 20),
          marginLeft: side ? 0 : undefined,
          padding: big ? "30px 46px 36px" : side ? "22px 40px 26px 34px" : "22px 40px 28px",
          background: rgba(T.primary, T.cardAlpha),
          borderRadius: side ? "0 34px 34px 0" : 34,
          borderLeft: side ? `12px solid ${T.accent}` : undefined,
          position: "relative",
          overflow: "hidden",
          textAlign: side ? "left" : "center",
          maxWidth: 960,
          boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
          transform: side
            ? `translateX(${(1 - enter) * -500}px) translateY(${float}px)`
            : `translateY(${(1 - enter) * -70 + float}px) scale(${(0.7 + 0.3 * enter) * (0.92 + 0.08 * exit)}) rotate(${(1 - enter) * -4 + tilt}deg)`,
          opacity: Math.min(1, enter * 1.5) * exit,
        }}
      >
        {o.label && (
          <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 28, letterSpacing: 4, color: T.accent, marginBottom: 8, opacity: interpolate(frame, [4, 12], [0, 1], clamp01) }}>
            {o.label}
          </div>
        )}
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: big ? 66 : 52, lineHeight: 1.18, color: T.text }}>
          {words.map(({ w, hl }, i) => {
            const ws = spring({ frame: frame - 4 - i * 3, fps, config: { damping: 14, stiffness: 200, mass: 0.5 } });
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  whiteSpace: "pre",
                  color: hl ? EMPH : T.text,
                  opacity: ws,
                  transform: `translateY(${(1 - ws) * 22}px)`,
                  // highlighted words get a marker stroke that sweeps in behind them
                  backgroundImage: hl ? `linear-gradient(${rgba(T.light ? T.accentSoft : T.accent, T.light ? 0.38 : 0.28)}, ${rgba(T.light ? T.accentSoft : T.accent, T.light ? 0.38 : 0.28)})` : undefined,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "0 82%",
                  backgroundSize: hl ? `${interpolate(frame, [12 + (i - firstHl) * 3, 26 + (i - firstHl) * 3], [0, 100], clamp01)}% 34%` : undefined,
                }}
              >
                {w}
              </span>
            );
          })}
        </div>
        {!side && <div style={{ position: "absolute", left: 0, bottom: 0, height: 9, width: `${bar * 100}%`, background: T.accent }} />}
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: `${shine}%`,
            width: "28%",
            transform: "skewX(-20deg)",
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)",
            pointerEvents: "none",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- speaker-in-corner cutaways
const PIP_CENTER = { x: PIP_SIDE === "right" ? 840 : 240, y: 1125 };


const PipPanels: React.FC<{ c: Cutaway; p: number }> = ({ c, p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const panels = c.panels ?? [];
  return (
    <AbsoluteFill style={{ opacity: Math.min(1, p * 1.3) }}>
      {panels.map((pn, i) => {
        const start = i === 0 ? c.in : pn.at;
        const end = i + 1 < panels.length ? panels[i + 1].at : c.out + 0.6;
        if (t < start - 0.1 || t >= end + 0.25) return null;
        const Scene = SCENES[pn.kind] ?? BLUEPRINT[pn.kind] ?? SHEET[pn.kind] ?? CARTOON[pn.kind] ?? SKETCH[pn.kind] ?? PAPER[pn.kind] ?? ILLUSTRATED[pn.kind];
        if (!Scene) return null;
        // outgoing panel slides away, incoming slides in
        const out = i + 1 < panels.length ? interpolate(t, [end - 0.15, end + 0.2], [1, 0], clamp01) : 1;
        const inn = i > 0 ? spring({ frame: Math.round((t - start) * fps), fps, config: { damping: 15, stiffness: 150 } }) : 1;
        return (
          <AbsoluteFill key={i} style={{ opacity: Math.min(out, Math.min(1, inn * 1.4)), transform: `translateX(${(1 - out) * -300 + (1 - inn) * 500}px)` }}>
            <Scene f={frame - Math.round(start * fps)} p={pn.props} startT={start} />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

const CounterFrame: React.FC<{ o: Pill }> = ({ o }) => <CounterPop o={o} f={useCurrentFrame()} />;

// ---------------------------------------------------------------- main
const Reel: React.FC = () => {
  useFonts();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const z = zoomAt(t, fps);
  const shake = punchShake(t);
  const { p: cutP, c: pipCut } = pipAt(t, fps);
  // "full" cutaways replace the speaker entirely for a few seconds (voice continues);
  // "pip" cutaways keep her in a corner frame.
  // "scene": a full-frame animation covers the speaker (her voice continues); scenes draw their own world
  const scene = pipCut?.kind === "scene";
  const full = pipCut?.kind === "full" || scene;
  const p = full ? 0 : cutP;
  const pc = Math.min(1, p);
  const [fx, fy] = E.pip.focus;
  const ox = FACE.x + (fx - FACE.x) * pc;
  const oy = FACE.y + (fy - FACE.y) * pc;
  const sc = (z * (1 - p) + E.pip.scale * p) * (full ? 1 + 0.08 * Math.min(1, cutP) : 1);
  const dx = (PIP_CENTER.x - ox) * p;
  const dy = (PIP_CENTER.y - oy) * p;
  const r = E.pip.radius;
  const rLocal = 2300 * (1 - pc) + (r / E.pip.scale) * pc;
  const rounded = E.style.pipShape === "rounded";
  const clip = rounded
    ? `inset(${Math.max(0, oy - rLocal)}px ${Math.max(0, 1080 - ox - rLocal)}px ${Math.max(0, 1920 - oy - rLocal)}px ${Math.max(0, ox - rLocal)}px round ${(70 / E.pip.scale) * pc}px)`
    : `circle(${rLocal}px at ${ox}px ${oy}px)`;
  // "split": the speaker slides down (no scaling, so no quality loss) and an illustration
  // panel opens in the top part of the frame.
  const splitCut = E.cutaways.find((c) => c.kind === "split" && t >= c.in - 0.01 && t < c.out + 0.7);
  const spIn = splitCut ? spring({ frame: frame - Math.round(splitCut.in * fps), fps, config: { damping: 18, stiffness: 120, mass: 0.8 } }) : 0;
  const spOut = splitCut && t >= splitCut.out ? spring({ frame: frame - Math.round(splitCut.out * fps), fps, config: { damping: 18, stiffness: 120, mass: 0.8 } }) : 0;
  const sp = Math.max(0, Math.min(1, spIn * (1 - spOut)));
  const SPLIT_TOP = E.split?.top ?? 900;
  const SPLIT_SHIFT = E.split?.shift ?? 520;
  const shiftY = SPLIT_SHIFT * sp;
  const splitClip = `inset(${sp * (SPLIT_TOP - SPLIT_SHIFT)}px ${30 * sp}px ${-shiftY}px ${30 * sp}px round ${44 * sp}px)`;
  // past the end of the footage (an end card's tail) the last picture is held
  const vFrames = Math.floor((E.videoDur ?? E.duration) * fps);
  const retroP = E.retro ? interpolate(t, [E.retro.out - 0.15, E.retro.out + 0.25], [1, 0], clamp01) * (t >= E.retro.in ? 1 : 0) : 0;
  const video = <OffthreadVideo src={staticFile(E.video ?? "base.mp4")} />;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {sp > 0.001 && <AbsoluteFill style={{ background: `linear-gradient(180deg, #F7FCF9 0%, ${T.accentSoft} 100%)`, opacity: Math.min(1, sp * 1.5) }} />}
      {!full && p > 0.001 && <Backdrop p={p} />}
      {!full && pipCut && p > 0.001 && <PipPanels c={pipCut} p={p} />}
      <AbsoluteFill
        style={{
          transform: `translate(${shake + dx}px, ${shake * 0.4 + dy + shiftY}px) scale(${sc})`,
          transformOrigin: `${ox}px ${oy}px`,
          clipPath: p > 0.001 ? clip : sp > 0.001 ? splitClip : undefined,
        }}
      >
        <AbsoluteFill style={{ filter: retroP > 0.001 ? `grayscale(${retroP}) contrast(${1 + 0.3 * retroP}) brightness(${1 - 0.08 * retroP})` : undefined }}>
          {frame >= vFrames - 1 ? <Freeze frame={vFrames - 2}>{video}</Freeze> : video}
        </AbsoluteFill>
      </AbsoluteFill>
      {retroP > 0.001 && <RetroOverlay p={retroP} />}
      {splitCut && sp > 0.001 && (
        <AbsoluteFill style={{ height: SPLIT_TOP, overflow: "hidden", opacity: Math.min(1, sp * 1.4), transform: `translateY(${(1 - sp) * -60}px)` }}>
          <PipPanels c={splitCut} p={1} />
        </AbsoluteFill>
      )}
      {p > 0.02 && (
        <div
          style={{
            position: "absolute",
            left: ox + dx - (r + 8),
            top: oy + dy - (r + 8),
            width: 2 * (r + 8),
            height: 2 * (r + 8),
            borderRadius: rounded ? 76 : "50%",
            border: `8px solid ${T.accent}`,
            boxShadow: "0 16px 40px rgba(0,0,0,0.45)",
            opacity: Math.max(0, (p - 0.75) / 0.25),
          }}
        />
      )}
      {scene && pipCut && cutP > 0.001 && (
        <AbsoluteFill style={{ opacity: Math.min(1, cutP * 1.4), transform: `scale(${1.08 - 0.08 * Math.min(1, cutP)})` }}>
          <PipPanels c={pipCut} p={1} />
        </AbsoluteFill>
      )}
      {full && !scene && pipCut && cutP > 0.001 && (
        <AbsoluteFill style={{ transform: `scale(${1.06 - 0.06 * Math.min(1, cutP)})` }}>
          <Backdrop p={cutP} />
          {/* centre scenes vertically; the tall phone mock stays high so it clears the captions */}
          <AbsoluteFill style={{ transform: `translateY(${(pipCut.panels ?? []).filter((pn) => t >= pn.at - 0.1).slice(-1)[0]?.kind === "phone" ? 20 : 170}px)` }}>
            <PipPanels c={pipCut} p={cutP} />
          </AbsoluteFill>
        </AbsoluteFill>
      )}
      {E.cutaways
        .filter((c) => c.kind === "comment" && t >= c.in && t < c.out)
        .map((c) => (
          <CommentCTA key={c.id} p={c.props ?? {}} startT={c.in} />
        ))}
      {E.overlays.filter((o) => !o.plate).map((o) => (
        <Sequence key={o.id} from={Math.round(o.in * FPS)} durationInFrames={Math.round((o.out - o.in) * FPS)}>
          {o.kind === "ticket" ? <Ticket o={o as any} /> : o.kind === "marker" ? <Marker o={o as any} /> : o.kind === "callcard" ? <CallCard o={o as any} /> : o.kind === "note" ? <BpNote o={o as any} /> : o.kind === "spark" ? <BpSpark o={o as any} /> : o.kind === "strip" ? <Strip o={o as any} /> : o.kind === "counter" ? <CounterFrame o={o} /> : o.kind === "icon" ? <IconChip o={o} /> : o.kind === "title" ? <TitleCard o={o} /> : o.kind === "end" ? <EndCard o={o} /> : o.kind !== "pop" ? <PillCard o={o} /> : E.style.pops === "type" || o.hand || o.strike !== undefined ? <TypePop o={o} /> : <KeywordPop o={o} />}
        </Sequence>
      ))}
      <Captions />
      {E.sfx.map((s, i) => (
        <Sequence key={i} from={Math.max(0, Math.round(s.t * FPS))} durationInFrames={40}>
          <Audio src={staticFile(s.src)} volume={s.vol} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

registerRoot(() => (
  <Composition id="Reel" component={Reel} durationInFrames={Math.round(E.duration * FPS)} fps={FPS} width={1080} height={1920} />
));
