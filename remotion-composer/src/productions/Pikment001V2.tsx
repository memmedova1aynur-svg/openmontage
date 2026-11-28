import React from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame } from "remotion";
import { BRAND, DISPLAY, BODY, GRADIENT } from "../pikment/brand";
import { loadPikmentFonts } from "../pikment/fonts";
import { easeOut, easeInOut, easeBack, prog, lerp } from "../pikment/motion";
import { LightBg, LightSweep, MaskWord, gradText } from "../pikment/Kit";
import { LaptopPro, PhonePro } from "../pikment/Devices";
import { PikmentLogo } from "../pikment/Logo";
import T from "./pikment001v2.timeline.json";
import WORDS from "./pikment001v2.words.json";

loadPikmentFonts();
export type Pikment001V2Props = { audioSrc: string } & Record<string, unknown>;
const L = "pikment_launch/";
const FPS = 30;
const Wd = (i: number) => (WORDS as { t0: number }[])[i].t0;
const clampN = (v: number, a: number, b: number) => Math.min(Math.max(v, a), b);
const blur = (px: number): React.CSSProperties => (px > 0.3 ? { filter: `blur(${px}px)` } : {});

/** Depth: soft brand-colour shapes drifting at different speeds behind everything. */
const Depth: React.FC<{ t: number }> = ({ t }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    {[
      { x: 780, y: 260, s: 360, c: BRAND.violet3, r: 24, sp: 0.8 },
      { x: -80, y: 1250, s: 420, c: BRAND.blue, r: 40, sp: -0.6 },
      { x: 700, y: 1560, s: 300, c: BRAND.lavender, r: 30, sp: 0.5 },
    ].map((d, i) => (
      <div key={i} style={{ position: "absolute", left: d.x + Math.sin(t / 4 + i) * 30, top: d.y + Math.cos(t / 5 + i * 2) * 36, width: d.s, height: d.s, borderRadius: d.s * 0.28, background: d.c, opacity: 0.055, transform: `rotate(${d.r + t * d.sp * 3}deg)`, filter: "blur(16px)" }} />
    ))}
  </AbsoluteFill>
);

/* ------------------------------------------------------------------ S1 hook */
const Hook: React.FC<{ f: number }> = ({ f }) => {
  const out = prog(f, T.morph[0] - 0.05, T.morph[0] + 0.3, easeInOut);
  const S = 136;
  const pop = 1 + 0.06 * (1 - prog(f, Wd(3), Wd(3) + 0.5, easeOut)) * (f / FPS >= Wd(3) ? 1 : 0);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 560, textAlign: "center", opacity: 1 - out, transform: `scale(${lerp(1, 0.95, out)})`, ...blur(out * 8) }}>
      <div><MaskWord at={Wd(0)} size={S}>Pikment</MaskWord><MaskWord at={Wd(1)} size={S} gap={0}>artıq</MaskWord></div>
      <div style={{ transform: `scale(${pop})` }}><MaskWord at={Wd(2)} size={S} grad>daha</MaskWord><MaskWord at={Wd(3)} size={S} grad gap={0}>əlçatan</MaskWord></div>
      <div><MaskWord at={Wd(4)} size={S} gap={0}>olacaq.</MaskWord></div>
    </div>
  );
};

/* -------------------------------------- match cut: underline -> laptop screen */
const SW = 860;
const SH = Math.round(SW * 0.625);
const Stage: React.FC<{ f: number; t: number }> = ({ f, t }) => {
  const u = prog(f, T.underline[0], T.underline[1], easeOut);
  const m = prog(f, T.morph[0], T.morph[1], easeInOut);
  const lap = prog(f, T.morph[1] - 0.1, T.morph[1] + 0.25, easeOut);
  const shrink = prog(f, T.shrink[0], T.shrink[1], easeInOut);
  const cam = lerp(0, -380, prog(f, Wd(7) - 0.15, Wd(9) + 0.7, easeInOut));
  const push = prog(f, T.push[0], T.push[1], easeInOut);
  const turn = prog(f, T.morph[1], T.shrink[1], easeInOut);
  const cy = lerp(1060, 930, m);
  const bw = lerp(640 * u, SW, m), bh = lerp(14, SH, m);
  const wy = lerp(930, 470, shrink) + cam; // laptop screen centre
  const scroll = lerp(0, 300, prog(f, T.morph[1], T.shrink[1] + 1.5, easeInOut));
  const showL = t >= T.morph[1] - 0.1;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: 1 - push, transform: `scale(${(1 + 0.05 * prog(f, T.shrink[0], T.push[0], (x) => x)) * lerp(1, 1.9, push)})`, transformOrigin: "50% 45%", ...blur(push * 18) }}>
      {lap < 1 && <div style={{ position: "absolute", left: 540 - bw / 2, top: cy - bh / 2, width: bw, height: bh, borderRadius: lerp(7, 9, m), background: GRADIENT, opacity: 1 - lap }} />}
      {showL && (
        <div style={{ position: "absolute", left: 35, top: wy - (15 + SH / 2), width: SW + 150, opacity: lap, transform: `scale(${lerp(1, 0.52, shrink)})`, transformOrigin: `50% ${15 + SH / 2}px` }}>
          <LaptopPro sw={SW} src={L + "site_scroll.png"} scrollCss={scroll} rotY={lerp(0, -15, turn)} rotX={lerp(2, 5, turn)} glare={0.35} />
        </div>
      )}
      <Cards f={f} />
    </div>
  );
};

type Card = { src: string; h: number; label: string; wi: number };
const CARDS: Card[] = [
  { src: "site_telimler_head.png", h: 194, label: "Təlimlər", wi: 5 },
  { src: "site_xidmetler_head.png", h: 200, label: "Xidmətlər", wi: 6 },
  { src: "site_mentorluq.png", h: 224, label: "Mentorluq", wi: 7 },
  { src: "site_kimler_row.png", h: 299, label: "Peşəkar inkişaf", wi: 9 },
];
const CARD_Y = [700, 942, 1192, 1446];
const Cards: React.FC<{ f: number }> = ({ f }) => {
  const cam = lerp(0, -380, prog(f, Wd(7) - 0.15, Wd(9) + 0.7, easeInOut));
  const conv = prog(f, T.converge, T.converge + 0.6, easeInOut);
  const lineP = prog(f, Wd(5), Wd(9) + 0.6, (x) => x);
  return (
    <div style={{ position: "absolute", inset: 0, transform: `translateY(${cam}px)` }}>
      <div style={{ position: "absolute", left: 82, top: CARD_Y[0] + 97, width: 6, height: (CARD_Y[3] + 150 - CARD_Y[0] - 97) * lineP, borderRadius: 6, background: `linear-gradient(180deg, ${BRAND.violet}, ${BRAND.blue})`, opacity: 1 - conv }} />
      {CARDS.map((c, i) => {
        const at = Wd(c.wi);
        const p = prog(f, at - 0.05, at + 0.75, easeOut);
        const dir = i % 2 === 0 ? -1 : 1;
        const pill = prog(f, at, at + 0.5, easeBack);
        const rot = dir * -6 * (1 - conv);
        const ox = dir * 26 * (1 - conv);
        return (
          <div key={i} style={{ position: "absolute", left: 110, top: CARD_Y[i], width: 860, height: c.h, opacity: Math.min(p * 1.8, 1), transform: `perspective(1800px) translateX(${ox + (1 - p) * 140 * dir}px) translateY(${(1 - p) * 60}px) rotateY(${rot}deg) scale(${lerp(0.9, 1, p) * lerp(1, 0.97, conv)})`, ...blur((1 - p) * 8) }}>
            <div style={{ position: "absolute", inset: 0, borderRadius: 28, overflow: "hidden", background: "#fff", boxShadow: "0 44px 90px rgba(69,36,245,0.20), 0 12px 26px rgba(23,20,40,0.12)", border: `2px solid ${BRAND.line}` }}>
              <Img src={staticFile(L + c.src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />
            </div>
            <div style={{ position: "absolute", left: -44, top: -24, transform: `scale(${pill})`, transformOrigin: "left center", background: GRADIENT, color: "#fff", fontFamily: DISPLAY, fontWeight: 800, fontSize: 40, letterSpacing: -0.8, padding: "12px 30px", borderRadius: 60, boxShadow: "0 16px 36px rgba(69,36,245,0.35)" }}>{c.label}</div>
            <div style={{ position: "absolute", left: -32, top: c.h / 2 - 12, width: 24, height: 24, borderRadius: 24, background: "#fff", border: `6px solid ${BRAND.violet}`, transform: `scale(${pill})`, opacity: 1 - conv }} />
          </div>
        );
      })}
    </div>
  );
};

/* ------------------------------------------------------------------ S4 domain */
const Domain: React.FC<{ f: number }> = ({ f }) => {
  const x0 = Wd(14), x1 = Wd(16);
  const out = prog(f, T.phoneIn[0] - 0.2, T.phoneIn[0] + 0.35, easeInOut);
  const u = prog(f, x1 + 0.1, x1 + 0.7, easeOut);
  const S = 196;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 790, textAlign: "center", opacity: 1 - out, transform: `translateY(${-out * 120}px) scale(${lerp(1.06, 1, prog(f, x0, x0 + 1.6, easeOut)) * lerp(1, 0.96, out)})`, ...blur(out * 10) }}>
      <div><MaskWord at={x0 - 0.03} size={S} gap={0} weight={800}>pikment</MaskWord><MaskWord at={x1 - 0.03} size={S} gap={0} grad weight={800}>.az</MaskWord></div>
      <div style={{ margin: "30px auto 0", width: 780 * u, height: 14, borderRadius: 14, background: GRADIENT }} />
    </div>
  );
};

/* ---------------------------------------------------------- phone with real UI */
const PW = 440;
const AS = PW / 643;
const SLICES = [
  { src: "app_theme.png", y: 152 }, { src: "app_item1.png", y: 340 }, { src: "app_item2.png", y: 518 }, { src: "app_item3.png", y: 696 }, { src: "app_item4.png", y: 872 },
];
const OFF = 44;
const AppScreen: React.FC<{ f: number }> = ({ f }) => {
  const hp = prog(f, T.phoneIn[1] - 0.2, T.phoneIn[1] + 0.4, easeOut);
  return (
    <div style={{ position: "absolute", inset: 0, background: BRAND.bg }}>
      <div style={{ position: "absolute", left: 20 * AS, top: 35 * AS + OFF, width: 400 * AS, opacity: hp, transform: `translateY(${(1 - hp) * 16}px)`, ...blur((1 - hp) * 6) }}>
        <Img src={staticFile(L + "app_header.png")} style={{ width: "100%" }} />
      </div>
      {SLICES.map((s, i) => {
        const at = T.pops[i];
        const p = prog(f, at, at + 0.6, easeBack);
        const settle = prog(f, at + 0.35, at + 1.0, easeOut);
        const img = i === 0 ? "app_theme.png" : s.src;
        return (
          <div key={i} style={{ position: "absolute", left: 33 * AS, top: s.y * AS + OFF, width: 580 * AS, opacity: Math.min(p * 2.2, 1), transform: `translateY(${(1 - p) * 70}px) scale(${lerp(0.8, 1, p)})`, filter: `drop-shadow(0 ${lerp(30, 5, settle)}px ${lerp(40, 10, settle)}px rgba(69,36,245,${lerp(0.42, 0.09, settle)}))${p < 1 ? ` blur(${(1 - p) * 5}px)` : ""}`, zIndex: 10 - i }}>
            <Img src={staticFile(L + img)} style={{ width: "100%", display: "block" }} />
          </div>
        );
      })}
    </div>
  );
};

const Devices: React.FC<{ f: number; t: number }> = ({ f, t }) => {
  const rise = prog(f, T.phoneIn[0], T.phoneIn[1], easeOut);
  const tog = prog(f, T.together[0], T.together[1], easeInOut);
  const lapIn = prog(f, T.together[0], T.together[1] + 0.1, easeOut);
  const soonT = Wd(27);
  const hit = f / FPS >= soonT ? Math.exp(-(f / FPS - soonT) * 5) * Math.sin((f / FPS - soonT) * 22) * 0.05 : 0;
  const iris = prog(f, T.band[0], T.band[0] + 0.55, easeInOut);
  const rotY = lerp(-14, 5, prog(f, T.phoneIn[0], T.together[0], easeInOut)) + Math.sin(t * 0.9) * 1.6;
  const bp = t >= T.together[1] ? 0.014 * Math.exp(-((t * 2) % 1) * 6) : 0;
  const fl = t >= T.phoneIn[1] ? Math.sin(t * 1.5) * 7 : 0;
  const px = lerp(540, 330, tog), py = lerp(1115 + (1 - rise) * 1000, 1165, tog);
  const sc = lerp(0.9, 0.74, tog) * (1 + hit + bp);
  const scroll = 40 + (t - T.together[0]) * 10;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: 1 - iris * 0.6, ...blur(iris * 6) }}>
      {t >= T.together[0] - 0.05 && (
        <div style={{ position: "absolute", left: 350, top: 852 - fl * 0.6, width: 1010, opacity: lapIn, transform: `translateX(${(1 - lapIn) * 220}px) scale(${0.7 * (1 + hit + bp)})`, transformOrigin: "0 0" }}>
          <LaptopPro sw={SW} src={L + "site_scroll.png"} scrollCss={scroll} rotY={-11} rotX={4} glare={0.35} />
        </div>
      )}
      <div style={{ position: "absolute", left: px - (PW + 36) / 2, top: py + fl - (Math.round(PW * 1194 / 643) + 36) / 2, transform: `scale(${sc})`, transformOrigin: "50% 50%" }}>
        <PhonePro sw={PW} rotY={rotY} rotX={lerp(6, 2, rise)} glare={0.4}>
          <AppScreen f={f} />
        </PhonePro>
      </div>
    </div>
  );
};

const Headline: React.FC<{ f: number }> = ({ f }) => {
  const out = prog(f, Wd(24) - 0.3, Wd(24) - 0.02, easeInOut);
  const s = 98;
  const kick = prog(f, Wd(17), Wd(17) + 0.5, easeOut);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 262, textAlign: "center", opacity: 1 - out, transform: `translateY(${-out * 50}px)`, ...blur(out * 8) }}>
      <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 46, letterSpacing: 6, textTransform: "uppercase", color: BRAND.violet2, opacity: kick, transform: `translateY(${(1 - kick) * 16}px)`, marginBottom: 18 }}>İndi isə</div>
      <div><MaskWord at={Wd(19)} size={s}>Pedaqoqlar</MaskWord><MaskWord at={Wd(20)} size={s} gap={0}>üçün</MaskWord></div>
      <div><MaskWord at={Wd(21)} size={s} grad>yeni</MaskWord><MaskWord at={Wd(22)} size={s} grad gap={0}>rəqəmsal</MaskWord></div>
      <div><MaskWord at={Wd(23)} size={s} gap={0}>imkanlar.</MaskWord></div>
    </div>
  );
};

const Soon: React.FC<{ f: number }> = ({ f }) => {
  const t = f / FPS;
  const st = Wd(27);
  const iris = prog(f, T.band[0], T.band[0] + 0.55, easeInOut);
  const lab = clampN(prog(f, st - 0.15, st + 0.6, easeInOut), 0, 1);
  const p = prog(f, st, st + 0.55, easeBack);
  const ring = prog(f, st, st + 1.0, easeOut);
  const flash = t < st ? 0 : 1 - prog(f, st, st + 0.22, easeOut);
  const shake = t >= st ? Math.exp(-(t - st) * 9) * Math.sin((t - st) * 70) * 5 : 0;
  return (
    <>
      <div style={{ position: "absolute", left: 0, right: 0, top: lerp(262, 232, lab), textAlign: "center", transform: `scale(${lerp(1, 0.5, lab)})`, transformOrigin: "50% 0", opacity: 1 - iris, ...blur(iris * 8) }}>
        <div><MaskWord at={Wd(24)} size={104} gap={0}>Pikment</MaskWord></div>
        <div><MaskWord at={Wd(25)} size={104} grad>mobil</MaskWord><MaskWord at={Wd(26)} size={104} grad gap={0}>tətbiqi</MaskWord></div>
      </div>
      <div style={{ position: "absolute", left: 540 - 300, top: 1120 - 300, width: 600, height: 600, borderRadius: 600, border: `4px solid ${BRAND.violet3}`, opacity: t >= st ? 0.5 * (1 - ring) : 0, transform: `scale(${lerp(0.3, 3.2, ring)})` }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 540, textAlign: "center", opacity: 1 - iris, transform: `translateY(${shake}px)`, ...blur(iris * 8) }}>
        <div style={{ display: "inline-block", fontFamily: DISPLAY, fontWeight: 800, fontSize: 176, letterSpacing: -7, lineHeight: 1.05, whiteSpace: "nowrap" }}>
          {"TEZLİKLƏ".split("").map((ch, i) => {
            const q = prog(f, st + i * 0.035, st + 0.5 + i * 0.035, easeBack);
            return <span key={i} style={{ display: "inline-block", opacity: Math.min(q * 2, 1), transform: `translateY(${(1 - q) * 70}px) scale(${lerp(1.5, 1, q)})`, ...gradText, ...blur((1 - q) * 8) }}>{ch}</span>;
          })}
        </div>
      </div>
      <div style={{ position: "absolute", inset: 0, background: "#fff", opacity: flash * 0.45, pointerEvents: "none" }} />
    </>
  );
};

/* ------------------------------------------------------------------- ending */
const FAN = ["#A78BFA", "#6d4aff", "#4553d8", "#2b6bff", "#21A0FF"];
const Ending: React.FC<{ f: number; t: number }> = ({ f, t }) => {
  const l0 = Wd(28);
  const reveal = prog(f, l0 - 0.2, l0 + 0.7, easeInOut);
  const lp = prog(f, l0 - 0.25, l0 + 0.7, easeOut);
  const shift = Math.max(t - l0, 0) * 0.14;
  const fan = prog(f, T.fan, T.fan + 0.9, easeBack);
  const dm = prog(f, T.fan + 0.5, T.fan + 1.1, easeOut);
  const br = Math.sin((t - T.fan) * 1.4);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div style={{ position: "absolute", left: 100, top: 600, opacity: lp > 0 ? 1 : 0, transform: `scale(${lerp(0.95, 1, lp)}) translateY(${(1 - lp) * 20}px)` }}>
        <PikmentLogo width={880} reveal={reveal} shift={shift} ink="#000000" />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 868, textAlign: "center" }}>
        {[29, 30, 31, 32, 33].map((wi, i) => (
          <MaskWord key={wi} at={Wd(wi) - 0.04} size={90} weight={700} grad={wi === 32} gap={i === 4 ? 0 : 0.24}>{(WORDS as { w: string }[])[wi].w + (wi === 33 ? "." : "")}</MaskWord>
        ))}
      </div>
      <div style={{ position: "absolute", left: 540 - 450, top: 1250 - 450, width: 900, height: 900, borderRadius: 900, background: `radial-gradient(circle, ${BRAND.violet3}33, ${BRAND.blue}00 65%)`, opacity: t >= T.fan ? 1 - prog(f, T.fan, T.fan + 1.6, easeOut) : 0, transform: `scale(${lerp(0.2, 2.2, prog(f, T.fan, T.fan + 1.6, easeOut))})` }} />
      <div style={{ position: "absolute", left: 540, top: 1420, transform: "scale(1.3)" }}>
        {FAN.map((c, i) => {
          const fi = prog(f, T.fan + i * 0.07, T.fan + 0.9 + i * 0.07, easeBack);
          const a = (i - 2) * (12 + br * 1.4) * fi;
          return <div key={i} style={{ position: "absolute", left: -72, top: -134, width: 144, height: 258, borderRadius: 28, background: c, transformOrigin: "50% 100%", transform: `translateY(${(1 - fi) * 160 + Math.sin(t * 1.7 + i) * 3}px) rotate(${a}deg)`, opacity: fi > 0 ? 1 : 0, boxShadow: "0 24px 46px rgba(23,20,40,0.22)", border: "4px solid rgba(255,255,255,0.88)" }} />;
        })}
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1090, textAlign: "center", fontFamily: DISPLAY, fontWeight: 700, fontSize: 48, letterSpacing: -0.5, color: BRAND.inkSoft, opacity: dm, transform: `translateY(${(1 - dm) * 16}px)` }}>pikment.az</div>
    </div>
  );
};

/* brand-gradient band sweeping bottom -> top; the scene swaps while it fully covers the frame */
const Transition: React.FC<{ f: number }> = ({ f }) => {
  const t = f / FPS;
  if (t < T.band[0] || t > T.band[1]) return null;
  const e = prog(f, T.band[0], T.band[1], easeInOut);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: -60, right: -60, top: lerp(1920, -3000, e), height: 3000, background: GRADIENT, borderRadius: "50% 50% 50% 50% / 140px 140px 140px 140px" }} />
    </AbsoluteFill>
  );
};

const BAND_MID = (T.band[0] + T.band[1]) / 2;
const Grain: React.FC<{ f: number }> = ({ f }) => (
  <AbsoluteFill style={{ pointerEvents: "none", opacity: 0.07, mixBlendMode: "multiply", backgroundImage: `url(${staticFile("pikment_site/grain.png")})`, backgroundPosition: `${(f * 137) % 400}px ${(f * 71) % 400}px` }} />
);

export const Pikment001V2: React.FC<Pikment001V2Props> = ({ audioSrc }) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const cz = 1 + 0.018 * (t / T.total);
  return (
    <AbsoluteFill style={{ background: BRAND.bg, fontFamily: BODY }}>
      <LightBg />
      <Depth t={t} />
      <AbsoluteFill style={{ transform: `scale(${cz})` }}>
        {t < T.push[1] && (<><Hook f={f} /><Stage f={f} t={t} /></>)}
        {t >= T.push[1] - 0.2 && t < T.phoneIn[0] + 0.6 && <Domain f={f} />}
        {t >= T.phoneIn[0] - 0.1 && t < BAND_MID && (<><Headline f={f} /><Devices f={f} t={t} /><Soon f={f} /></>)}
        {t >= BAND_MID && <Ending f={f} t={t} />}
      </AbsoluteFill>
      <Transition f={f} />
      <LightSweep p={prog(f, Wd(27), Wd(27) + 0.9, (x) => x)} strength={0.55} />
      <LightSweep p={prog(f, Wd(28) + 0.05, Wd(28) + 1.0, (x) => x)} strength={0.4} />
      <LightSweep p={prog(f, T.fan + 0.4, T.fan + 1.6, (x) => x)} strength={0.35} />
      <Grain f={f} />
      <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 62%, rgba(23,20,40,0.09) 100%)" }} />
      <Audio src={staticFile(audioSrc)} />
    </AbsoluteFill>
  );
};
