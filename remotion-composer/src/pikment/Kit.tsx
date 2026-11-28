import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate } from "remotion";
import { BRAND, DISPLAY, BODY, GRADIENT, FPS } from "./brand";
import { easeOut, easeInOut, prog, clampOpts, lerp } from "./motion";

/** Light lavender field with two soft violet-blue light pools that drift slowly. */
export const LightBg: React.FC<{ dark?: number }> = ({ dark = 0 }) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  return (
    <AbsoluteFill style={{ background: BRAND.bg }}>
      <div style={{ position: "absolute", width: 1300, height: 1300, left: -420 + Math.sin(t / 3) * 60, top: -380 + Math.cos(t / 4) * 50, borderRadius: "50%", background: "radial-gradient(circle, rgba(120,69,245,0.20), rgba(120,69,245,0) 62%)" }} />
      <div style={{ position: "absolute", width: 1200, height: 1200, right: -460 + Math.cos(t / 3.5) * 60, bottom: -260 + Math.sin(t / 4.5) * 60, borderRadius: "50%", background: "radial-gradient(circle, rgba(52,96,245,0.20), rgba(52,96,245,0) 62%)" }} />
      {dark > 0 && <AbsoluteFill style={{ background: BRAND.dark, opacity: dark }} />}
    </AbsoluteFill>
  );
};

export const gradText: React.CSSProperties = { background: GRADIENT, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" };

/** One word that rises out of a mask line (kinetic typography). */
export const MaskWord: React.FC<{ children: React.ReactNode; at: number; dur?: number; grad?: boolean; size: number; weight?: number; color?: string; gap?: number }> = ({ children, at, dur = 0.55, grad, size, weight = 800, color = BRAND.ink, gap = 0.26 }) => {
  const f = useCurrentFrame();
  const p = prog(f, at, at + dur, easeOut);
  return (
    <span style={{ display: "inline-block", overflow: "hidden", verticalAlign: "top", paddingBottom: size * 0.16, marginBottom: -size * 0.16, marginRight: gap * size }}>
      <span style={{ display: "inline-block", fontFamily: DISPLAY, fontWeight: weight, fontSize: size, letterSpacing: -size * 0.03, lineHeight: 1.08, color, transform: `translateY(${(1 - p) * 110}%)`, opacity: p > 0 ? 1 : 0, ...(grad ? gradText : {}) }}>{children}</span>
    </span>
  );
};

/** Gradient underline bar. */
export const Underline: React.FC<{ p: number; width: number; height?: number }> = ({ p, width, height = 14 }) => (
  <div style={{ width: width * p, height, borderRadius: height, background: GRADIENT }} />
);

/** Premium laptop: lid + screen content + aluminium base, rendered in CSS 3D. */
export const Laptop: React.FC<{ src: string; width?: number; rotY?: number; rotX?: number; shadow?: number; scroll?: number }> = ({ src, width = 900, rotY = -18, rotX = 8, shadow = 1, scroll = 0 }) => {
  const sw = width, sh = width * 0.625; // 16:10
  const bezel = 22;
  return (
    <div style={{ width: sw + bezel * 2, perspective: 2200 }}>
      <div style={{ transformStyle: "preserve-3d", transform: `rotateX(${rotX}deg) rotateY(${rotY}deg)` }}>
        <div style={{ width: sw + bezel * 2, height: sh + bezel * 2, borderRadius: 30, background: "linear-gradient(145deg,#2b2b33,#0e0e13)", padding: bezel, boxShadow: `0 ${60 * shadow}px ${110 * shadow}px rgba(44,30,120,${0.38 * shadow}), 0 ${14 * shadow}px ${30 * shadow}px rgba(23,20,40,${0.28 * shadow}), inset 0 0 0 2px rgba(255,255,255,0.08)`, position: "relative" }}>
          <div style={{ position: "absolute", top: 8, left: "50%", width: 7, height: 7, borderRadius: 7, background: "#1b1b22", transform: "translateX(-50%)" }} />
          <div style={{ width: sw, height: sh, borderRadius: 10, overflow: "hidden", background: BRAND.dark, position: "relative" }}>
            <Img src={staticFile(src)} style={{ width: "100%", height: "auto", transform: `translateY(${-scroll}px)` }} />
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(115deg, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0) 38%)" }} />
          </div>
        </div>
        <div style={{ width: sw + bezel * 2 + 90, marginLeft: -45, height: 26, borderRadius: "0 0 40px 40px", background: "linear-gradient(180deg,#d9d8e2,#a9a8b6 70%,#8f8e9d)", boxShadow: `0 ${30 * shadow}px ${60 * shadow}px rgba(44,30,120,${0.3 * shadow})`, position: "relative" }}>
          <div style={{ position: "absolute", top: 0, left: "50%", width: 170, height: 9, marginLeft: -85, borderRadius: "0 0 14px 14px", background: "rgba(0,0,0,0.18)" }} />
        </div>
      </div>
    </div>
  );
};

/** Realistic phone shell. The screen shows ONLY the supplied real-app artwork (children). */
export const PhoneShell: React.FC<{ width?: number; children: React.ReactNode; rotY?: number; rotX?: number; shadow?: number }> = ({ width = 460, children, rotY = 0, rotX = 0, shadow = 1 }) => {
  const bz = 14, h = width * 1.857, r = width * 0.17;
  return (
    <div style={{ width: width + bz * 2, perspective: 2000 }}>
      <div style={{ width: width + bz * 2, height: h + bz * 2, borderRadius: r + bz, background: "linear-gradient(150deg,#6e6d78,#2a2a32 40%,#55545f)", padding: bz, boxShadow: `0 ${60 * shadow}px ${110 * shadow}px rgba(44,30,120,${0.4 * shadow}), 0 ${16 * shadow}px ${34 * shadow}px rgba(23,20,40,${0.3 * shadow}), inset 0 0 0 2px rgba(255,255,255,0.18)`, transform: `rotateX(${rotX}deg) rotateY(${rotY}deg)`, position: "relative" }}>
        <div style={{ width, height: h, borderRadius: r, overflow: "hidden", background: BRAND.bg, position: "relative" }}>
          {children}
          <div style={{ position: "absolute", top: 18, left: "50%", width: width * 0.28, height: 34, marginLeft: -width * 0.14, borderRadius: 20, background: "#0a0a0f", zIndex: 5 }} />
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(120deg, rgba(255,255,255,0.20) 0%, rgba(255,255,255,0) 32%)", zIndex: 6, pointerEvents: "none" }} />
        </div>
      </div>
    </div>
  );
};

/** Gradient sweep used between sections. p: 0→1 across. */
export const Sweep: React.FC<{ p: number }> = ({ p }) => {
  const left = lerp(-175, 115, p);
  return (
    <AbsoluteFill style={{ overflow: "hidden", pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: -200, bottom: -200, width: "160%", left: `${left}%`, transform: "skewX(-12deg)", background: `linear-gradient(90deg, ${BRAND.violet}, ${BRAND.violet3} 50%, ${BRAND.blue})`, opacity: p > 0 && p < 1 ? 1 : 0 }} />
    </AbsoluteFill>
  );
};

/** Subtle film grain + soft vignette for a finished, non-template look. */
export const Finish: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 60%, rgba(23,20,40,0.10) 100%)" }} />
);

export { interpolate, easeInOut, clampOpts, BODY };
