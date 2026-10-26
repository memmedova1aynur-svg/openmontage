import React from "react";
import {
  AbsoluteFill,
  Audio,
  Composition,
  OffthreadVideo,
  Sequence,
  interpolate,
  registerRoot,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Backdrop, CommentCTA, PIP_SIDE, SCENES } from "./scenes";
import { Cutaway, E, EMPH, FONT, FPS, Page, Pill, T, ZoomKey, clamp01, rgba, useFonts } from "./theme";

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
  const c = E.cutaways.find((c: Cutaway) => (c.kind === "pip" || c.kind === "full") && t >= c.in - 0.01 && t < c.out + 0.6);
  if (!c) return { p: 0, c: undefined };
  const cfg = { damping: 16, stiffness: 140, mass: 0.8 };
  const enter = spring({ frame: Math.round((t - c.in) * fps), fps, config: cfg });
  const exit = t >= c.out ? spring({ frame: Math.round((t - c.out) * fps), fps, config: cfg }) : 0;
  return { p: Math.max(0, Math.min(1.04, enter - exit)), c };
};

// ---------------------------------------------------------------- captions
const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const page = E.pages.find((p: Page) => t >= p.start && t < p.end);
  if (!page) return null;
  const enter = spring({ frame: Math.round((t - page.start) * fps), fps, config: { damping: 14, stiffness: 220, mass: 0.6 } });
  const style = E.style.captions;
  // box captions keep their own dark backing, so only bare captions switch colour over pale cutaways
  const onPale = !!T.light && style !== "box" && pipAt(t, fps).p > 0.5;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 430 }}>
      <div
        style={{
          maxWidth: 940,
          textAlign: "center",
          lineHeight: 1.12,
          padding: style === "box" ? "14px 26px 18px" : 0,
          borderRadius: 26,
          background: style === "box" ? (T.light ? rgba(T.accent, 0.9) : rgba(T.primary, 0.82)) : "transparent",
          transform: `translateY(${(1 - enter) * 26}px) scale(${0.86 + 0.14 * enter}) rotate(${(1 - enter) * -2.5}deg)`,
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
                color: chip ? T.onAccent : active ? (style === "box" && T.light ? T.accentSoft : T.accent) : onPale ? T.text : "#FFFFFF",
                opacity: spoken ? 1 : 0.55,
                transform: `scale(${scale})`,
                WebkitTextStroke: style === "box" || chip || onPale ? undefined : "3px rgba(0,0,0,0.85)",
                paintOrder: "stroke fill",
                textShadow: onPale ? "none" : "0 6px 18px rgba(0,0,0,0.55)",
                backgroundImage: style === "box" && active ? `linear-gradient(${T.accentSoft}, ${T.accentSoft})` : undefined,
                backgroundRepeat: "no-repeat",
                backgroundPosition: "0 100%",
                backgroundSize: style === "box" && active ? `${100 * Math.min(1, pop * 1.2)}% 6px` : undefined,
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
        const Scene = SCENES[pn.kind];
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
  const full = pipCut?.kind === "full";
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
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {!full && p > 0.001 && <Backdrop p={p} />}
      {!full && pipCut && p > 0.001 && <PipPanels c={pipCut} p={p} />}
      <AbsoluteFill
        style={{
          transform: `translate(${shake + dx}px, ${shake * 0.4 + dy}px) scale(${sc})`,
          transformOrigin: `${ox}px ${oy}px`,
          clipPath: p > 0.001 ? clip : undefined,
        }}
      >
        <OffthreadVideo src={staticFile(E.video ?? "base.mp4")} />
      </AbsoluteFill>
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
      {full && pipCut && cutP > 0.001 && (
        <AbsoluteFill style={{ transform: `scale(${1.06 - 0.06 * Math.min(1, cutP)})` }}>
          <Backdrop p={cutP} />
          <AbsoluteFill style={{ transform: "translateY(170px)" }}>
            <PipPanels c={pipCut} p={cutP} />
          </AbsoluteFill>
        </AbsoluteFill>
      )}
      {E.cutaways
        .filter((c) => c.kind === "comment" && t >= c.in && t < c.out)
        .map((c) => (
          <CommentCTA key={c.id} p={c.props ?? {}} startT={c.in} />
        ))}
      {E.overlays.map((o) => (
        <Sequence key={o.id} from={Math.round(o.in * FPS)} durationInFrames={Math.round((o.out - o.in) * FPS)}>
          <PillCard o={o} />
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
