import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Bg, C, FONT, GRAD, Grad, Subtitle, Swatches, Title, clamp, fr } from "./PikmentSchoolAd";

/**
 * Pikment — "Təlimini seç" (Reels 9:16). Course names, durations and areas are
 * quoted from pikment.az. No trainer names, no prices, no outcome promises.
 */

export interface PikmentChooseAdProps {
  voiceSrc: string;
  logoSrc: string;
  whatsapp: string;
  site: string;
}

const T = {
  s1: [0, 3.5],
  s2: [3.5, 7.2],
  s3: [7.2, 13.1],
  s5: [13.1, 18.5],
} as const;

const AREAS = [
  { n: "Məktəbəqədər", c: "#6C47FF" },
  { n: "Oyun və terapiya", c: "#4553D6" },
  { n: "İnklüziv", c: "#2F6BFF" },
  { n: "Ana və uşaq", c: "#1FA2FF" },
  { n: "Təhsil biznesi", c: "#A78BFA" },
  { n: "Şəxsi inkişaf", c: "#3B6BFF" },
];

const COURSES = [
  { cat: "Məktəbəqədər", ad: "Montessori metodu", m: "6 dərs · 1 ay" },
  { cat: "Məktəbəqədər", ad: "Metodist hazırlığı", m: "12 dərs · 1 ay" },
  { cat: "Məktəbəqədər", ad: "Bağça işi üzrə təlim və təcrübə proqramı", m: "3 ay" },
  { cat: "Oyun və terapiya", ad: "Pedaqoqlar üçün oyun məktəbi", m: "10 dərs · 1 ay" },
  { cat: "Məktəbəqədər", ad: "Uşaq İnkişafı Mütəxəssisliyi Məktəbi", m: "9 ay" },
];

const Areas: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 440, left: 70, right: 70, display: "flex", flexWrap: "wrap", gap: 24, justifyContent: "center" }}>
      {AREAS.map((a, i) => {
        const p = spring({ frame: f - fps * (0.5 + i * 0.28), fps, config: { damping: 14, stiffness: 110 } });
        return (
          <div
            key={a.n}
            style={{
              width: 455,
              height: 170,
              borderRadius: 36,
              background: a.c,
              color: "#fff",
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 46,
              lineHeight: 1.1,
              display: "flex",
              alignItems: "flex-end",
              padding: 30,
              boxSizing: "border-box",
              boxShadow: "0 18px 50px rgba(0,0,0,0.4)",
              opacity: Math.max(p, 0),
              transform: `translateY(${(1 - Math.max(p, 0)) * 70}px) scale(${0.92 + 0.08 * Math.max(p, 0)})`,
            }}
          >
            {a.n}
          </div>
        );
      })}
    </div>
  );
};

const Cards: React.FC<{ selectAt: number }> = ({ selectAt }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sel = spring({ frame: f - fps * selectAt, fps, config: { damping: 14, stiffness: 100 } });
  return (
    <div style={{ position: "absolute", top: 320, left: 70, width: 940 }}>
      {COURSES.map((c, i) => {
        const p = spring({ frame: f - fps * (0.3 + i * 0.5), fps, config: { damping: 16, stiffness: 100 } });
        const last = i === COURSES.length - 1;
        const dim = last ? 1 : 1 - 0.7 * Math.max(sel, 0);
        const scale = last ? 1 + 0.045 * Math.max(sel, 0) : 1;
        return (
          <div
            key={c.ad}
            style={{
              height: 190,
              marginBottom: 20,
              borderRadius: 34,
              background: "#fff",
              boxShadow: last && sel > 0.05 ? "0 0 0 6px #8B6CFF, 0 30px 70px rgba(139,108,255,0.55)" : "0 20px 50px rgba(0,0,0,0.38)",
              padding: "26px 34px",
              boxSizing: "border-box",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 24,
              opacity: Math.max(p, 0) * dim,
              transform: `translateX(${(1 - Math.max(p, 0)) * 140}px) scale(${scale})`,
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ display: "inline-block", fontFamily: FONT, fontWeight: 700, fontSize: 24, color: "#6B6A85", background: "#EEEDFB", borderRadius: 100, padding: "6px 18px" }}>{c.cat}</div>
              <div style={{ marginTop: 12, fontFamily: FONT, fontWeight: 800, fontSize: c.ad.length > 30 ? 36 : 44, lineHeight: 1.12, color: C.navy, letterSpacing: -0.5 }}>{c.ad}</div>
            </div>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 34, color: "#fff", background: GRAD, borderRadius: 100, padding: "14px 26px", whiteSpace: "nowrap" }}>{c.m}</div>
          </div>
        );
      })}
    </div>
  );
};

const End: React.FC<{ logoSrc: string; whatsapp: string; site: string }> = ({ logoSrc, whatsapp, site }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: f, fps, config: { damping: 15, stiffness: 100 } });
  const b = spring({ frame: f - fps * 0.5, fps, config: { damping: 16, stiffness: 100 } });
  const c = spring({ frame: f - fps * 1.3, fps, config: { damping: 12, stiffness: 120 } });
  const d = interpolate(f, [fps * 2.2, fps * 2.7], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 380, left: 0, right: 0, textAlign: "center", opacity: a, transform: `scale(${0.88 + 0.12 * a})` }}>
        <div style={{ display: "inline-block", background: "#fff", borderRadius: 48, padding: "44px 70px", boxShadow: "0 24px 70px rgba(0,0,0,0.45)" }}>
          <Img src={staticFile(logoSrc)} style={{ width: 640, display: "block" }} />
        </div>
      </div>
      <div style={{ position: "absolute", top: 740, left: 70, right: 70, textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: 68, lineHeight: 1.15, color: C.white, opacity: Math.max(b, 0), letterSpacing: -1 }}>
        Müraciət üçün <Grad>WhatsApp-a yaz</Grad>
      </div>
      <div style={{ position: "absolute", top: 960, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${Math.max(c, 0)})` }}>
        <div style={{ background: C.green, color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 62, padding: "30px 64px", borderRadius: 100, boxShadow: "0 20px 50px rgba(23,122,69,0.45)" }}>{whatsapp}</div>
      </div>
      <div style={{ position: "absolute", top: 1140, left: 0, right: 0, textAlign: "center", fontFamily: FONT, fontWeight: 700, fontSize: 46, color: C.white, opacity: d }}>{site}</div>
      <div style={{ position: "absolute", top: 1230, left: 100, right: 100, textAlign: "center", fontFamily: FONT, fontWeight: 500, fontSize: 30, color: C.mute, opacity: d }}>Qiyməti və şərtləri müraciət zamanı deyirik.</div>
    </AbsoluteFill>
  );
};

export const PikmentChooseAd: React.FC<PikmentChooseAdProps> = ({ voiceSrc, logoSrc, whatsapp, site }) => {
  const { fps } = useVideoConfig();
  const S = (k: keyof typeof T) => ({ from: fr(T[k][0], fps), dur: fr(T[k][1] - T[k][0], fps) });
  const s1 = S("s1");
  const s2 = S("s2");
  const s3 = S("s3");
  const s5 = S("s5");
  return (
    <AbsoluteFill>
      <Bg />
      <Audio src={staticFile(voiceSrc)} />

      <Sequence from={s1.from} durationInFrames={s1.dur}>
        <Title>
          Hansı sahədə <Grad>mütəxəssis</Grad> olmaq istəyirsən?
        </Title>
        <Swatches />
        <Subtitle text="Hansı sahədə mütəxəssis olmaq istəyirsən?" start={0.4} end={3.2} />
      </Sequence>

      <Sequence from={s2.from} durationInFrames={s2.dur}>
        <Title top={170} size={80}>
          <Grad>25</Grad> təlim, <Grad>6</Grad> sahə
        </Title>
        <Areas />
        <Subtitle text="Pikment-də iyirmi beş təlim var, altı fərqli sahədə." start={0.1} end={3.5} />
      </Sequence>

      <Sequence from={s3.from} durationInFrames={s3.dur}>
        <Title top={130} size={64}>
          <Grad>1 aydan 9 aya</Grad> qədər
        </Title>
        <Cards selectAt={3.7} />
        <Subtitle text="Bir aylıq təlimlər də var, doqquz aylıq məktəb də." start={0.1} end={3.5} />
        <Subtitle text="Özünə uyğun olanı seç." start={3.7} end={5.7} />
      </Sequence>

      <Sequence from={s5.from} durationInFrames={s5.dur}>
        <End logoSrc={logoSrc} whatsapp={whatsapp} site={site} />
        <Subtitle text="Müraciət üçün WhatsApp-a yaz." start={0.1} end={2.6} />
      </Sequence>
    </AbsoluteFill>
  );
};
