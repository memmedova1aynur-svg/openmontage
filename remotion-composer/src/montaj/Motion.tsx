// Montaj motion graphics kitabxanası — şəffaf fonda render olunur, ffmpeg ilə danışan kadrın üstünə qoyulur.
// Prinsiplər: yay (spring) hərəkəti, maska ilə açılma, sürətə görə yüngül hərəkət bulanıqlığı, ölçülü çıxış.
// Rənglər/şriftlər müştərinin brend profilindən props ilə gəlir — şablon görünüşü olmasın.
import React from "react";
import { AbsoluteFill, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";

const FONT_CSS = `
@font-face{font-family:'Montaj Sans';font-weight:600;src:url('${staticFile("montaj-fonts/montserrat-600.ttf")}')}
@font-face{font-family:'Montaj Sans';font-weight:700;src:url('${staticFile("montaj-fonts/montserrat-700.ttf")}')}
@font-face{font-family:'Montaj Sans';font-weight:800;src:url('${staticFile("montaj-fonts/montserrat-800.ttf")}')}
@font-face{font-family:'Montaj Serif';font-style:italic;src:url('${staticFile("montaj-fonts/playfair-italic.ttf")}')}`;

export type Brand = { ink: string; accent: string; paper: string; soft: string };
const DEF: Brand = { ink: "#2B1D1A", accent: "#7A1E3A", paper: "#FBF6F1", soft: "#F2C9D1" };

// çıxış: son 0.35 s yumşaq sönmə + 24px yuxarı
const useExit = (dur: number) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const k = interpolate(f, [dur - fps * 0.35, dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  return { opacity: 1 - k, transform: `translateY(${-24 * k}px)` };
};
// sürət əsaslı hərəkət bulanıqlığı (After Effects motion blur-un sadə ekvivalenti)
const blurFromVel = (v: number) => `blur(${Math.min(6, Math.abs(v) * 0.08).toFixed(2)}px)`;

export const TitleReveal: React.FC<{ lines: string[]; italic?: number[]; brand?: Brand; y?: number; size?: number; durationInFrames?: number }> =
  ({ lines, italic = [], brand = DEF, y = 130, size = 96 }) => {
    const f = useCurrentFrame(); const { fps, durationInFrames } = useVideoConfig(); const ex = useExit(durationInFrames);
    const bar = spring({ frame: f, fps, config: { damping: 18, stiffness: 140 } });
    return (
      <AbsoluteFill style={{ ...ex }}>
        <style>{FONT_CSS}</style>
        <div style={{ position: "absolute", left: 56, top: y, right: 56, padding: "40px 44px 34px", borderRadius: 34,
          background: brand.paper, opacity: Math.min(1, bar * 1.4), transform: `translateY(${(1 - bar) * 30}px)`,
          boxShadow: "0 22px 60px rgba(0,0,0,0.25)" }}>
          <div style={{ height: 10, width: 140 * bar, background: brand.accent, borderRadius: 5, marginBottom: 26 }} />
          {lines.map((l, i) => {
            const s = spring({ frame: f - 4 - i * 5, fps, config: { damping: 16, stiffness: 120, mass: 0.9 } });
            const sPrev = spring({ frame: f - 5 - i * 5, fps, config: { damping: 16, stiffness: 120, mass: 0.9 } });
            const it = italic.includes(i);
            return (
              <div key={i} style={{ overflow: "hidden", paddingBottom: 8 }}>
                <div style={{ transform: `translateY(${(1 - s) * 110}%)`, filter: blurFromVel((s - sPrev) * 110 * 10),
                  fontFamily: it ? "'Montaj Serif'" : "'Montaj Sans'", fontStyle: it ? "italic" : "normal", fontWeight: it ? 500 : 800,
                  fontSize: it ? size * 1.08 : size, lineHeight: 1.04, color: it ? brand.accent : brand.ink,
                  }}>{l}</div>
              </div>);
          })}
        </div>
      </AbsoluteFill>);
  };

export const LowerThird: React.FC<{ name: string; role: string; brand?: Brand; y?: number }> = ({ name, role, brand = DEF, y = 1400 }) => {
  const f = useCurrentFrame(); const { fps, durationInFrames } = useVideoConfig(); const ex = useExit(durationInFrames);
  const line = interpolate(f, [0, fps * 0.45], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const nm = spring({ frame: f - 6, fps, config: { damping: 20, stiffness: 110 } });
  const rl = interpolate(f, [fps * 0.35, fps * 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ ...ex }}>
      <style>{FONT_CSS}</style>
      <div style={{ position: "absolute", left: 48, top: y - 22, width: 760 * line, height: 170, borderRadius: 22,
        background: "linear-gradient(90deg, rgba(0,0,0,0.55), rgba(0,0,0,0))" }} />
      <div style={{ position: "absolute", left: 72, top: y }}>
        <div style={{ height: 4, width: 520 * line, background: brand.accent, marginBottom: 14 }} />
        <div style={{ overflow: "hidden" }}>
          <div style={{ transform: `translateX(${(1 - nm) * -105}%)`, fontFamily: "'Montaj Sans'", fontWeight: 800, fontSize: 52, color: "#fff",
            textShadow: "0 2px 16px rgba(0,0,0,0.45)" }}>{name}</div>
        </div>
        <div style={{ transform: `translateY(${(1 - rl) * 10}px)`, fontFamily: "'Montaj Sans'", fontWeight: 600, fontSize: 30,
          color: "#FFFFFF", opacity: 0.92 * rl, marginTop: 6, textShadow: "0 2px 12px rgba(0,0,0,0.5)" }}>{role}</div>
      </div>
    </AbsoluteFill>);
};

export const QuestionCard: React.FC<{ q: string; tag?: string; brand?: Brand; y?: number }> = ({ q, tag = "SUAL", brand = DEF, y = 200 }) => {
  const f = useCurrentFrame(); const { fps, durationInFrames } = useVideoConfig(); const ex = useExit(durationInFrames);
  const card = spring({ frame: f, fps, config: { damping: 15, stiffness: 130 } });
  const chip = spring({ frame: f - 6, fps, config: { damping: 9, stiffness: 180 } });
  const words = q.split(" ");
  return (
    <AbsoluteFill style={{ ...ex }}>
      <style>{FONT_CSS}</style>
      <div style={{ position: "absolute", left: 70, right: 70, top: y, transform: `scale(${0.92 + 0.08 * card})`, opacity: card,
        background: brand.paper, borderRadius: 40, padding: "64px 56px 52px", boxShadow: "0 24px 60px rgba(0,0,0,0.22)" }}>
        <div style={{ position: "absolute", top: -30, left: 44, transform: `scale(${chip})`, background: brand.accent, color: "#fff",
          fontFamily: "'Montaj Sans'", fontWeight: 800, fontSize: 34, padding: "10px 26px", borderRadius: 30 }}>{tag}</div>
        <div style={{ fontFamily: "'Montaj Sans'", fontWeight: 800, fontSize: 60, lineHeight: 1.18, color: brand.ink }}>
          {words.map((w, i) => {
            const s = interpolate(f, [8 + i * 2, 16 + i * 2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
            return <span key={i} style={{ display: "inline-block", opacity: s, transform: `translateY(${(1 - s) * 18}px)`, marginRight: 16 }}>{w}</span>;
          })}
        </div>
      </div>
    </AbsoluteFill>);
};
