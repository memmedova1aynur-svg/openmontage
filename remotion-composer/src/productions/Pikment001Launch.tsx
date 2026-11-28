import React from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame } from "remotion";
import { BRAND, DISPLAY, BODY, GRADIENT } from "../pikment/brand";
import { loadPikmentFonts } from "../pikment/fonts";
import { easeOut, easeInOut, easeBack, prog, lerp, clampOpts } from "../pikment/motion";
import { Finish, Laptop, LightBg, MaskWord, PhoneShell, Sweep, gradText } from "../pikment/Kit";
import { PikmentLogo } from "../pikment/Logo";
import T from "./pikment001.timeline.json";

loadPikmentFonts();

export type Pikment001Props = { audioSrc: string } & Record<string, unknown>;
const L = "pikment_launch/";
const FPS = 30;
const win = (t: number, a: number, b: number) => t >= a && t < b;
const camY = (f: number) => lerp(0, -430, prog(f, T.cards[2] - 0.2, T.cards[3] + 0.9, easeInOut));

/** S1 — kinetic typography hook */
const Hook: React.FC<{ t: number; f: number }> = ({ t, f }) => {
  const [w0, w1, w2, w3] = T.hook.words;
  const out = 1 - prog(f, T.laptop.morph[0], T.laptop.morph[0] + 0.3, easeInOut);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 600, textAlign: "center", opacity: out, transform: `scale(${lerp(1, 0.94, 1 - out)})` }}>
      <div><MaskWord at={w0} size={124}>Pikment</MaskWord><MaskWord at={w1} size={124} gap={0}>artıq</MaskWord></div>
      <div><MaskWord at={w2} size={124} grad>daha</MaskWord><MaskWord at={w2 + 0.12} size={124} grad gap={0}>əlçatan</MaskWord></div>
      <div><MaskWord at={w3} size={124} gap={0}>olacaq.</MaskWord></div>
    </div>
  );
};

/** S1→S2 match cut: the underline becomes the laptop screen. */
const Morph: React.FC<{ f: number }> = ({ f }) => {
  const [u0, u1] = T.hook.underline;
  const [m0, m1] = T.laptop.morph;
  const grow = prog(f, u0, u1, easeOut); // underline draws in
  const m = prog(f, m0, m1, easeInOut); // underline -> screen
  const lap = prog(f, m1 - 0.12, m1 + 0.2, easeOut);
  const shrink = prog(f, T.cards[0] - 0.25, T.cards[0] + 0.55, easeInOut);
  const out = 1 - prog(f, T.cardsOut, T.cardsOut + 0.4, easeInOut);
  const drift = (f / FPS - m1) * 6; // slow turn
  const rotY = m < 1 ? 0 : lerp(-6, -16, prog(f, m1, T.cards[0], easeInOut)) + (f / FPS > T.cards[0] ? lerp(0, 10, shrink) : 0);
  // underline geometry -> screen geometry
  const bw = lerp(560 * grow, 900, m);
  const bh = lerp(14, 562, m);
  const cy = lerp(1090, 930, m);
  const topY = lerp(cy, 440 + 0, shrink);
  const sc = lerp(1, 0.52, shrink);
  const op = out * (1 - 0);
  const showLaptop = f / FPS >= m1 - 0.12;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 1920, opacity: op }}>
      {!showLaptop || lap < 1 ? (
        <div style={{ position: "absolute", left: 540 - bw / 2, top: cy - bh / 2, width: bw, height: bh, borderRadius: lerp(7, 12, m), background: GRADIENT, opacity: 1 - lap }} />
      ) : null}
      {showLaptop && (
        <div style={{ position: "absolute", left: 540 - 472, top: lerp(cy - 330, topY - 330, shrink) + camY(f), width: 944, opacity: lap, transform: `scale(${sc})`, transformOrigin: "50% 50%" }}>
          <Laptop src={L + "site_hero.png"} width={900} rotY={rotY} rotX={lerp(4, 6, m)} scroll={drift} />
        </div>
      )}
    </div>
  );
};

type Card = { src: string; w: number; h: number; label: string };
const CARDS: Card[] = [
  { src: L + "site_telimler_head.png", w: 880, h: 198, label: "Təlimlər" },
  { src: L + "site_xidmetler_head.png", w: 880, h: 204, label: "Xidmətlər" },
  { src: L + "site_mentorluq.png", w: 880, h: 229, label: "Mentorluq" },
  { src: L + "site_kimler_row.png", w: 880, h: 306, label: "Peşəkar inkişaf" },
];
const CARD_Y = [740, 984, 1234, 1496];

/** S3 — real site sections as one connected composition; camera scrolls with the voice. */
const Cards: React.FC<{ f: number }> = ({ f }) => {
  const t0 = T.cards[0];
  const cam = camY(f);
  const out = prog(f, T.cardsOut, T.cardsOut + 0.45, easeInOut);
  const zoomOut = lerp(1, 0.9, out);
  const lineEnd = prog(f, t0, T.cards[3] + 0.5, (x) => x);
  const lineH = CARD_Y[3] + 160 - CARD_Y[0] + 60;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: 1 - out, transform: `translateY(${cam}px) scale(${zoomOut})`, transformOrigin: "50% 40%" }}>
      <div style={{ position: "absolute", left: 76, top: CARD_Y[0] - 40, width: 6, height: lineH * lineEnd, borderRadius: 6, background: `linear-gradient(180deg, ${BRAND.violet}, ${BRAND.blue})` }} />
      {CARDS.map((c, i) => {
        const at = T.cards[i];
        const p = prog(f, at, at + 0.7, easeOut);
        const dir = i % 2 === 0 ? -1 : 1;
        const pill = prog(f, at + 0.1, at + 0.55, easeBack);
        return (
          <div key={i} style={{ position: "absolute", left: 100, top: CARD_Y[i], width: c.w, height: c.h, opacity: Math.min(p * 1.6, 1), transform: `translateX(${(1 - p) * 120 * dir}px) translateY(${(1 - p) * 50}px) scale(${0.92 + 0.08 * p})` }}>
            <div style={{ position: "absolute", inset: 0, borderRadius: 28, overflow: "hidden", background: "#fff", boxShadow: "0 40px 90px rgba(69,36,245,0.20), 0 10px 24px rgba(23,20,40,0.12)", border: `2px solid ${BRAND.line}` }}>
              <Img src={staticFile(c.src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />
            </div>
            <div style={{ position: "absolute", left: -48, top: -24, transform: `scale(${pill})`, transformOrigin: "left center", background: GRADIENT, color: "#fff", fontFamily: DISPLAY, fontWeight: 800, fontSize: 40, letterSpacing: -0.8, padding: "12px 30px", borderRadius: 60, boxShadow: "0 16px 36px rgba(69,36,245,0.35)" }}>{c.label}</div>
            <div style={{ position: "absolute", left: -32 - 10, top: c.h / 2 - 12, width: 24, height: 24, borderRadius: 24, background: "#fff", border: `6px solid ${BRAND.violet}`, transform: `scale(${pill})` }} />
          </div>
        );
      })}
    </div>
  );
};

/** S4 — domain */
const Domain: React.FC<{ f: number }> = ({ f }) => {
  const [d0, d1] = T.domain;
  const out = prog(f, d1 - 0.35, d1, easeInOut);
  const u = prog(f, d0 + 0.5, d0 + 1.2, easeOut);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 800, textAlign: "center", opacity: 1 - out, transform: `translateY(${-out * 40}px)` }}>
      <div><MaskWord at={d0} size={178} gap={0}>pikment</MaskWord><MaskWord at={d0 + 0.12} size={178} gap={0} grad>.az</MaskWord></div>
      <div style={{ margin: "26px auto 0", width: 760 * u, height: 14, borderRadius: 14, background: GRADIENT }} />
    </div>
  );
};

const APP_SCALE = 460 / 643;
const SLICES = [
  { src: "app_theme.png", y: 152, h: 167 },
  { src: "app_item1.png", y: 340, h: 153 },
  { src: "app_item2.png", y: 518, h: 154 },
  { src: "app_item3.png", y: 696, h: 153 },
  { src: "app_item4.png", y: 872, h: 153 },
];

/** Phone screen: ONLY the real app UI slices the user provided. */
const AppScreen: React.FC<{ f: number }> = ({ f }) => {
  const hp = prog(f, T.phoneIn + 0.3, T.phoneIn + 0.8, easeOut);
  return (
    <div style={{ position: "absolute", inset: 0, background: BRAND.bg }}>
      <div style={{ position: "absolute", left: 20 * APP_SCALE, top: 35 * APP_SCALE, width: 400 * APP_SCALE, opacity: hp, transform: `translateY(${(1 - hp) * 14}px)` }}>
        <Img src={staticFile(L + "app_header.png")} style={{ width: "100%" }} />
      </div>
      {SLICES.map((s, i) => {
        const at = T.appPops[i];
        const p = prog(f, at, at + 0.55, easeBack);
        const settle = prog(f, at + 0.4, at + 1.0, easeOut);
        return (
          <div key={i} style={{ position: "absolute", left: 33 * APP_SCALE, top: s.y * APP_SCALE, width: 580 * APP_SCALE, opacity: Math.min(p * 2, 1), transform: `translateY(${(1 - p) * 60}px) scale(${lerp(0.82, 1, p)})`, filter: `drop-shadow(0 ${lerp(26, 4, settle)}px ${lerp(34, 8, settle)}px rgba(69,36,245,${lerp(0.4, 0.08, settle)}))`, zIndex: 10 - i }}>
            <Img src={staticFile(L + s.src)} style={{ width: "100%", display: "block" }} />
          </div>
        );
      })}
    </div>
  );
};

/** S5/S6 — headline, phone, then phone + laptop together */
const Devices: React.FC<{ f: number; t: number }> = ({ f, t }) => {
  const inP = prog(f, T.phoneIn, T.phoneIn + 0.9, easeOut);
  const tog = prog(f, T.together, T.together + 0.8, easeInOut);
  const lapIn = prog(f, T.together, T.together + 0.7, easeOut);
  const exit = prog(f, T.sweep2[0], T.sweep2[0] + 0.35, easeInOut);
  const phoneRot = lerp(-10, 6, prog(f, T.phoneIn, T.together, easeInOut));
  const x = lerp(540, 330, tog);
  const y = lerp(1180 + (1 - inP) * 900, 1260, tog);
  const sc = lerp(0.98, 0.74, tog);
  return (
    <div style={{ position: "absolute", inset: 0, opacity: 1 - exit }}>
      {t >= T.together && (
        <div style={{ position: "absolute", left: 640 - 472, top: 1000 - 330, opacity: lapIn, transform: `translateX(${(1 - lapIn) * 160}px) scale(0.62)`, transformOrigin: "50% 50%" }}>
          <Laptop src={L + "site_hero.png"} width={900} rotY={-14} rotX={5} scroll={0} />
        </div>
      )}
      <div style={{ position: "absolute", left: x - 244, top: y - 441, transform: `scale(${sc})`, transformOrigin: "50% 50%" }}>
        <PhoneShell width={460} rotY={phoneRot} rotX={3}>
          <AppScreen f={f} />
        </PhoneShell>
      </div>
    </div>
  );
};

const Headline: React.FC<{ f: number }> = ({ f }) => {
  const out = prog(f, T.appLabel - 0.25, T.appLabel + 0.1, easeInOut);
  const h = T.headline;
  const s = 92;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 270, textAlign: "center", opacity: 1 - out, transform: `translateY(${-out * 40}px)` }}>
      <div><MaskWord at={h} size={s}>Pedaqoqlar</MaskWord><MaskWord at={h + 0.18} size={s} gap={0}>üçün</MaskWord></div>
      <div><MaskWord at={h + 0.5} size={s} grad>yeni</MaskWord><MaskWord at={h + 0.65} size={s} grad gap={0}>rəqəmsal</MaskWord></div>
      <div><MaskWord at={h + 1.0} size={s} gap={0}>imkanlar.</MaskWord></div>
    </div>
  );
};

/** S6 — climax: TEZLİKLƏ */
const Soon: React.FC<{ f: number }> = ({ f }) => {
  const lab = prog(f, T.appLabel, T.appLabel + 0.5, easeOut);
  const labOut = prog(f, T.soon - 0.1, T.soon + 0.15, easeInOut);
  const p = prog(f, T.soon, T.soon + 0.5, easeBack);
  const exit = prog(f, T.sweep2[0], T.sweep2[0] + 0.35, easeInOut);
  const pulse = 1 + 0.012 * Math.sin((f / FPS - T.soon) * Math.PI * 2 * 1);
  const flash = f / FPS < T.soon ? 0 : 1 - prog(f, T.soon, T.soon + 0.25, easeOut);
  return (
    <>
      <div style={{ position: "absolute", left: 0, right: 0, top: 330, textAlign: "center", fontFamily: DISPLAY, fontWeight: 800, fontSize: 74, letterSpacing: -2, color: BRAND.ink, opacity: lab * (1 - labOut) * (1 - exit), transform: `translateY(${(1 - lab) * 40}px)` }}>
        Pikment <span style={gradText}>mobil tətbiqi</span>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 300, textAlign: "center", opacity: p * (1 - exit), transform: `scale(${lerp(1.35, 1, p) * pulse})` }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 800, fontSize: 168, letterSpacing: -6, lineHeight: 1, ...gradText }}>TEZLİKLƏ</div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 44, letterSpacing: -0.5, color: BRAND.ink, marginTop: 18, opacity: prog(f, T.soon + 0.3, T.soon + 0.8, easeOut) }}>Pikment mobil tətbiqi</div>
      </div>
      <div style={{ position: "absolute", inset: 0, background: "#fff", opacity: flash * 0.5, pointerEvents: "none" }} />
    </>
  );
};

const FAN = ["#A78BFA", "#6d4aff", "#4553d8", "#2b6bff", "#21A0FF"];

/** S7 — logo, tagline, colour fan from the brand's own swatches */
const Ending: React.FC<{ f: number; t: number }> = ({ f, t }) => {
  const l0 = T.logo;
  const reveal = prog(f, l0 + 0.15, l0 + 1.0, easeInOut);
  const lp = prog(f, l0 + 0.1, l0 + 1.0, easeOut);
  const shift = (t - l0) * 0.11;
  const words = [["Hər", 0], ["kəsin", 0.3], ["öz", 0.55], ["rəngi", 0.85], ["var.", 1.2]] as [string, number][];
  const fan = prog(f, l0 + 2.4, l0 + 3.3, easeBack);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div style={{ position: "absolute", left: 90, top: 640, transform: `scale(${lerp(0.94, 1, lp)})`, transformOrigin: "50% 50%", opacity: lp > 0 ? 1 : 0 }}>
        <PikmentLogo width={900} reveal={reveal} shift={shift} ink="#000000" />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 930, textAlign: "center" }}>
        {words.map(([w, d], i) => (
          <MaskWord key={i} at={l0 + 1.1 + d} size={84} weight={700} grad={w === "rəngi"} gap={i === words.length - 1 ? 0 : 0.24}>{w}</MaskWord>
        ))}
      </div>
      <div style={{ position: "absolute", left: 540, top: 1380 }}>
        {FAN.map((c, i) => {
          const a = (i - 2) * 11 * fan;
          return (
            <div key={i} style={{ position: "absolute", left: -70, top: -130, width: 140, height: 250, borderRadius: 26, background: c, transformOrigin: "50% 100%", transform: `translateY(${(1 - fan) * 120}px) rotate(${a}deg)`, opacity: fan > 0 ? 1 : 0, boxShadow: "0 20px 40px rgba(23,20,40,0.22)", border: "4px solid rgba(255,255,255,0.85)" }} />
          );
        })}
      </div>
    </div>
  );
};

export const Pikment001Launch: React.FC<Pikment001Props> = ({ audioSrc }) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const s1 = prog(f, T.sweep1[0], T.sweep1[1], (x) => x);
  const s2 = prog(f, T.sweep2[0], T.sweep2[1], (x) => x);
  const camZ = 1 + 0.02 * (t / T.total);
  return (
    <AbsoluteFill style={{ background: BRAND.bg, fontFamily: BODY }}>
      <LightBg />
      <AbsoluteFill style={{ transform: `scale(${camZ})` }}>
        {t < T.sweep1[0] + 0.3 && (<><Hook t={t} f={f} /><Morph f={f} /><Cards f={f} /></>)}
        {win(t, T.sweep1[0] + 0.3, T.sweep1[1] + 2.2) && t < T.headline - 0.1 && <Domain f={f} />}
        {t >= T.headline - 0.05 && t < T.sweep2[0] + 0.45 && (<><Headline f={f} /><Devices f={f} t={t} /><Soon f={f} /></>)}
        {t >= T.sweep2[0] + 0.3 && <Ending f={f} t={t} />}
      </AbsoluteFill>
      <Sweep p={s1} />
      <Sweep p={s2} />
      <Finish />
      <Audio src={staticFile(audioSrc)} />
    </AbsoluteFill>
  );
};
