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

/**
 * Pikment — "Uşaq İnkişafı Mütəxəssisliyi Məktəbi" (Reels 9:16, 28 s).
 * Built from REAL captures of pikment.az (card, stats) in the site's own
 * dark-navy look. Every fact on screen is quoted from the site; no prices,
 * no outcome promises, certificate is described as Pikment's own.
 */

export interface PikmentSchoolAdProps {
  voiceSrc: string;
  logoSrc: string;
  cardSrc: string;
  statsSrc: string;
  whatsapp: string;
  site: string;
}

const C = {
  navy: "#14132B",
  navy2: "#1E1C3F",
  white: "#F6F5FF",
  blue: "#3B6BFF",
  purple: "#8B6CFF",
  lav: "#A78BFA",
  sky: "#21A0FF",
  mute: "#B9B6D8",
  green: "#177A45",
};
const FONT = "Inter, 'DejaVu Sans', sans-serif";
const GRAD = "linear-gradient(90deg, #8B6CFF, #3B6BFF 60%, #21A0FF)";

const T = {
  s1: [0, 3.4],
  s2: [3.4, 6.9],
  s3: [6.9, 10.8],
  s4: [10.8, 14.1],
  s5: [14.1, 17.4],
  s6: [17.4, 24],
} as const;

const fr = (s: number, fps: number) => Math.round(s * fps);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Bg: React.FC = () => {
  const f = useCurrentFrame();
  const blob = (x: number, y: number, r: number, color: string, ph: number) => (
    <div
      style={{
        position: "absolute",
        left: x + Math.sin(f / 70 + ph) * 35 - r,
        top: y + Math.cos(f / 80 + ph) * 35 - r,
        width: r * 2,
        height: r * 2,
        borderRadius: "50%",
        background: color,
        filter: "blur(120px)",
      }}
    />
  );
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${C.navy} 0%, #191736 100%)` }}>
      {blob(200, 300, 300, "rgba(139,108,255,0.22)", 0)}
      {blob(920, 1000, 340, "rgba(59,107,255,0.20)", 2)}
      {blob(300, 1650, 300, "rgba(33,160,255,0.14)", 4)}
    </AbsoluteFill>
  );
};

const Title: React.FC<{ children: React.ReactNode; top?: number; size?: number }> = ({ children, top = 170, size = 88 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: f, fps, config: { damping: 20, stiffness: 110 } });
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 70,
        right: 70,
        textAlign: "center",
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: size,
        lineHeight: 1.1,
        letterSpacing: -2,
        color: C.white,
        opacity: p,
        transform: `translateY(${(1 - p) * 36}px)`,
      }}
    >
      {children}
    </div>
  );
};

const Grad: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span style={{ background: GRAD, WebkitBackgroundClip: "text", color: "transparent" }}>{children}</span>
);

const Subtitle: React.FC<{ text: string; start: number; end: number }> = ({ text, start, end }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = fr(start, fps);
  const b = fr(end, fps);
  const op = interpolate(f, [a, a + 6, b - 6, b], [0, 1, 1, 0], clamp);
  return (
    <div style={{ position: "absolute", left: 60, right: 60, bottom: 330, display: "flex", justifyContent: "center", opacity: op }}>
      <div
        style={{
          background: "rgba(246,245,255,0.95)",
          borderRadius: 26,
          padding: "18px 32px",
          fontFamily: FONT,
          fontWeight: 600,
          fontSize: 42,
          lineHeight: 1.25,
          color: C.navy,
          textAlign: "center",
          boxShadow: "0 12px 40px rgba(0,0,0,0.35)",
        }}
      >
        {text}
      </div>
    </div>
  );
};

/* --- S1: hook with the site's colour-swatch motif --- */
const SWATCHES = [
  { c: "#A78BFA", n: "Lavanda" },
  { c: "#6C47FF", n: "Pikment" },
  { c: "#4553D6", n: "İndiqo" },
  { c: "#2F6BFF", n: "Səma" },
  { c: "#1FA2FF", n: "Dəniz" },
];
const Swatches: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 700 }}>
      {SWATCHES.map((s, i) => {
        const p = spring({ frame: f - 8 - i * 5, fps, config: { damping: 14, stiffness: 90 } });
        const ang = (i - 2) * 11 * Math.max(p, 0);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 540 - 150,
              top: 120,
              width: 300,
              height: 470,
              borderRadius: 34,
              background: s.c,
              transformOrigin: "50% 100%",
              transform: `rotate(${ang}deg) translateY(${(1 - Math.max(p, 0)) * 300}px)`,
              boxShadow: "0 24px 60px rgba(0,0,0,0.4)",
              opacity: Math.max(p, 0),
            }}
          >
            <div style={{ position: "absolute", left: 26, bottom: 26, fontFamily: FONT, fontWeight: 700, fontSize: 30, color: "rgba(255,255,255,0.92)" }}>{s.n}</div>
          </div>
        );
      })}
    </div>
  );
};

/* --- Card scenes (real capture) --- */
const CARD_W = 960;
const CARD_H = Math.round((960 * 1038) / 1050);
const Card: React.FC<{ src: string; focus?: number; ring?: { y0: number; y1: number } }> = ({ src, focus = 0, ring }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: f, fps, config: { damping: 18, stiffness: 90 } });
  const z = interpolate(f, [0, fps * 4], [1, 1.05], clamp);
  const zoom = 1 + focus * 0.12;
  const ringOp = ring ? interpolate(f, [fps * 0.5, fps * 0.9], [0, 1], clamp) : 0;
  return (
    <div
      style={{
        position: "absolute",
        left: (1080 - CARD_W) / 2,
        top: 320 + (1 - enter) * 160,
        width: CARD_W,
        height: CARD_H,
        opacity: enter,
        transformOrigin: "50% 62%",
        transform: `scale(${z * zoom})`,
        borderRadius: 40,
        boxShadow: "0 40px 100px rgba(0,0,0,0.5)",
        overflow: "hidden",
      }}
    >
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", display: "block" }} />
      {ring && (
        <div
          style={{
            position: "absolute",
            left: 30,
            right: 30,
            top: `${ring.y0 * 100}%`,
            height: `${(ring.y1 - ring.y0) * 100}%`,
            borderRadius: 22,
            border: `6px solid ${C.purple}`,
            boxShadow: "0 0 0 9999px rgba(20,19,43,0.0), 0 0 40px rgba(139,108,255,0.7)",
            opacity: ringOp,
          }}
        />
      )}
    </div>
  );
};

const Chips: React.FC<{ items: string[]; top: number }> = ({ items, top }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top, left: 60, right: 60, display: "flex", gap: 20, justifyContent: "center", flexWrap: "wrap" }}>
      {items.map((t, i) => {
        const p = spring({ frame: f - fps * (0.4 + i * 0.25), fps, config: { damping: 13, stiffness: 120 } });
        return (
          <div
            key={i}
            style={{
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 46,
              color: "#fff",
              padding: "14px 36px",
              borderRadius: 100,
              background: GRAD,
              boxShadow: "0 16px 40px rgba(59,107,255,0.4)",
              transform: `scale(${Math.max(p, 0)})`,
            }}
          >
            {t}
          </div>
        );
      })}
    </div>
  );
};

/* --- S4: real stats capture --- */
const Stats: React.FC<{ src: string }> = ({ src }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: f, fps, config: { damping: 18, stiffness: 90 } });
  const note = interpolate(f, [fps * 1.4, fps * 1.9], [0, 1], clamp);
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: 45,
          top: 700,
          width: 990,
          opacity: p,
          transform: `translateY(${(1 - p) * 120}px)`,
          borderRadius: 34,
          overflow: "hidden",
          boxShadow: "0 30px 80px rgba(0,0,0,0.5)",
        }}
      >
        <Img src={staticFile(src)} style={{ width: "100%", display: "block" }} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 1010,
          textAlign: "center",
          fontFamily: FONT,
          fontWeight: 500,
          fontSize: 32,
          lineHeight: 1.35,
          color: C.mute,
          opacity: note,
        }}
      >
        Rəqəmlər Pikment adı ilə keçirilən təlimlərə aiddir.
      </div>
    </>
  );
};

/* --- S5: certificate, quoted honestly --- */
const Cert: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: f, fps, config: { damping: 14, stiffness: 100 } });
  const small = interpolate(f, [fps * 1.0, fps * 1.4], [0, 1], clamp);
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 640,
          left: 140,
          right: 140,
          padding: "70px 50px",
          borderRadius: 44,
          background: C.navy2,
          border: `3px solid rgba(167,139,250,0.5)`,
          textAlign: "center",
          transform: `scale(${0.85 + 0.15 * Math.max(p, 0)})`,
          opacity: Math.max(p, 0),
          boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
        }}
      >
        <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke={C.lav} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="9" r="5.5" />
          <path d="M8.5 13.5 7 21l5-2.6 5 2.6-1.5-7.5" />
        </svg>
        <div style={{ marginTop: 26, fontFamily: FONT, fontWeight: 800, fontSize: 76, color: C.white, letterSpacing: -1.5 }}>
          <Grad>Pikment</Grad> sertifikatı
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          top: 1180,
          left: 120,
          right: 120,
          textAlign: "center",
          fontFamily: FONT,
          fontWeight: 500,
          fontSize: 32,
          lineHeight: 1.35,
          color: C.mute,
          opacity: small,
        }}
      >
        Pikment-in öz sertifikatıdır; dövlət nümunəli sənəd deyil.
      </div>
    </>
  );
};

/* --- S6: end card --- */
const End: React.FC<{ logoSrc: string; whatsapp: string; site: string }> = ({ logoSrc, whatsapp, site }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: f, fps, config: { damping: 15, stiffness: 100 } });
  const b = spring({ frame: f - fps * 0.6, fps, config: { damping: 16, stiffness: 100 } });
  const c = spring({ frame: f - fps * 1.6, fps, config: { damping: 12, stiffness: 120 } });
  const d = interpolate(f, [fps * 2.6, fps * 3.1], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 330, left: 0, right: 0, textAlign: "center", opacity: a, transform: `scale(${0.88 + 0.12 * a})` }}>
        <div style={{ display: "inline-block", background: "#fff", borderRadius: 48, padding: "44px 70px", boxShadow: "0 24px 70px rgba(0,0,0,0.45)" }}>
          <Img src={staticFile(logoSrc)} style={{ width: 640, display: "block" }} />
        </div>
      </div>
      <div style={{ position: "absolute", top: 700, left: 70, right: 70, textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: 66, lineHeight: 1.15, color: C.white, opacity: Math.max(b, 0), letterSpacing: -1 }}>
        Uşaq İnkişafı <Grad>Mütəxəssisliyi</Grad> Məktəbi
      </div>
      <div style={{ position: "absolute", top: 960, left: 0, right: 0, textAlign: "center", fontFamily: FONT, fontWeight: 600, fontSize: 48, color: C.mute, opacity: Math.max(b, 0) }}>
        Müraciət üçün WhatsApp-a yaz
      </div>
      <div style={{ position: "absolute", top: 1080, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${Math.max(c, 0)})` }}>
        <div
          style={{
            background: C.green,
            color: "#fff",
            fontFamily: FONT,
            fontWeight: 800,
            fontSize: 62,
            padding: "30px 64px",
            borderRadius: 100,
            boxShadow: "0 20px 50px rgba(23,122,69,0.45)",
          }}
        >
          {whatsapp}
        </div>
      </div>
      <div style={{ position: "absolute", top: 1260, left: 0, right: 0, textAlign: "center", fontFamily: FONT, fontWeight: 700, fontSize: 46, color: C.white, opacity: d }}>{site}</div>
      <div style={{ position: "absolute", top: 1350, left: 100, right: 100, textAlign: "center", fontFamily: FONT, fontWeight: 500, fontSize: 30, color: C.mute, opacity: d }}>
        Qiyməti və şərtləri müraciət zamanı deyirik.
      </div>
    </AbsoluteFill>
  );
};

export const PikmentSchoolAd: React.FC<PikmentSchoolAdProps> = ({ voiceSrc, logoSrc, cardSrc, statsSrc, whatsapp, site }) => {
  const { fps } = useVideoConfig();
  const S = (k: keyof typeof T) => ({ from: fr(T[k][0], fps), dur: fr(T[k][1] - T[k][0], fps) });
  const s = { s1: S("s1"), s2: S("s2"), s3: S("s3"), s4: S("s4"), s5: S("s5"), s6: S("s6") };
  return (
    <AbsoluteFill>
      <Bg />
      <Audio src={staticFile(voiceSrc)} />

      <Sequence from={s.s1.from} durationInFrames={s.s1.dur}>
        <Title>
          Uşaqların <Grad>inkişafı</Grad> səni maraqlandırır?
        </Title>
        <Swatches />
        <Subtitle text="Uşaqların inkişafı səni maraqlandırır?" start={0.4} end={3.1} />
      </Sequence>

      <Sequence from={s.s2.from} durationInFrames={s.s2.dur}>
        <Title top={150} size={76}>
          Pikment-də <Grad>məktəb</Grad>
        </Title>
        <Card src={cardSrc} />
        <Subtitle text="Pikment-də Uşaq İnkişafı Mütəxəssisliyi Məktəbi var." start={0.1} end={3.3} />
      </Sequence>

      <Sequence from={s.s3.from} durationInFrames={s.s3.dur}>
        <Title top={150} size={76}>
          <Grad>9 ay</Grad>
        </Title>
        <Card src={cardSrc} focus={1} ring={{ y0: 0.578, y1: 0.658 }} />
        <Chips items={["6 ay təlim", "3 ay təcrübə"]} top={1350} />
        <Subtitle text="Doqquz ay: altı ay təlim, üç ay təcrübə." start={0.1} end={3.7} />
      </Sequence>

      <Sequence from={s.s4.from} durationInFrames={s.s4.dur}>
        <Title top={260} size={76}>
          Altı ildir <Grad>təlimlər</Grad> keçiririk
        </Title>
        <Stats src={statsSrc} />
        <Subtitle text="Altı ildir Pikment adı ilə təlimlər keçiririk." start={0.1} end={3.2} />
      </Sequence>

      <Sequence from={s.s5.from} durationInFrames={s.s5.dur}>
        <Title top={260} size={76}>
          Təlimdən sonra
        </Title>
        <Cert />
        <Subtitle text="Təlimi bitirənlərə Pikment sertifikatı verilir." start={0.1} end={3.2} />
      </Sequence>

      <Sequence from={s.s6.from} durationInFrames={s.s6.dur}>
        <End logoSrc={logoSrc} whatsapp={whatsapp} site={site} />
        <Subtitle text="Qiymət və şərtlər üçün WhatsApp-a yaz." start={0.1} end={2.9} />
      </Sequence>
    </AbsoluteFill>
  );
};
