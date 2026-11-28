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
 * Pikment — "Müşahidə dəftəri cibində" (Reels 9:16, 30 s).
 * Flat motion graphics, white + blue/purple palette from the Pikment logo.
 * Phone screen is a STYLIZED MOCKUP with fictional names — replace with real
 * app screenshots when the team provides them.
 */

export interface PikmentReelProps {
  /** Show the "only visible to you" privacy beat. Keep false until the team confirms it is true. */
  showPrivacyBeat: boolean;
  voiceSrc: string;
  logoSrc: string;
  whatsapp: string;
}

const C = {
  ink: "#14122B",
  blue: "#2B1FFF",
  purple: "#9B5CF6",
  orange: "#E8963A",
  soft: "#F4F2FF",
  mute: "#6B6A85",
  line: "#E4E1F5",
};
const FONT = "Inter, 'DejaVu Sans', sans-serif";

// Timeline in seconds (VO start times; see public/pikment/vo.wav)
const T = {
  s1: [0, 5.2],
  s2: [5.2, 9.0],
  s3: [9.0, 13.8],
  s4: [13.8, 16.3],
  s5: [16.3, 30],
} as const;

const fr = (s: number, fps: number) => Math.round(s * fps);

type Part = { t: string; hl?: boolean };

const Headline: React.FC<{ parts: Part[]; top?: number; size?: number }> = ({
  parts,
  top = 150,
  size = 84,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: f, fps, config: { damping: 18, stiffness: 110 } });
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
        lineHeight: 1.12,
        color: C.ink,
        opacity: p,
        transform: `translateY(${(1 - p) * 40}px)`,
        letterSpacing: -1.5,
      }}
    >
      {parts.map((x, i) => (
        <span key={i} style={{ color: x.hl ? C.blue : C.ink }}>
          {x.t}
        </span>
      ))}
    </div>
  );
};

const Subtitle: React.FC<{ text: string; start: number; end: number }> = ({ text, start, end }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = fr(start, fps);
  const b = fr(end, fps);
  const op = interpolate(f, [a, a + 6, b - 6, b], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        right: 60,
        bottom: 330, // inside Reels safe zone
        display: "flex",
        justifyContent: "center",
        opacity: op,
      }}
    >
      <div
        style={{
          background: "rgba(255,255,255,0.94)",
          borderRadius: 28,
          padding: "20px 34px",
          fontFamily: FONT,
          fontWeight: 600,
          fontSize: 44,
          lineHeight: 1.25,
          color: C.ink,
          textAlign: "center",
          boxShadow: "0 10px 40px rgba(43,31,255,0.14)",
        }}
      >
        {text}
      </div>
    </div>
  );
};

const Background: React.FC = () => {
  const f = useCurrentFrame();
  const blob = (x: number, y: number, r: number, color: string, ph: number) => (
    <div
      style={{
        position: "absolute",
        left: x + Math.sin(f / 60 + ph) * 30 - r,
        top: y + Math.cos(f / 70 + ph) * 30 - r,
        width: r * 2,
        height: r * 2,
        borderRadius: "50%",
        background: color,
        filter: "blur(90px)",
      }}
    />
  );
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#FFFFFF 0%, #F6F4FF 100%)" }}>
      {blob(180, 380, 260, "rgba(43,31,255,0.12)", 0)}
      {blob(900, 900, 300, "rgba(155,92,246,0.16)", 2)}
      {blob(300, 1600, 280, "rgba(43,31,255,0.10)", 4)}
    </AbsoluteFill>
  );
};

/* ---------- Notebook (paper) ---------- */
const Notebook: React.FC<{ lost?: number }> = ({ lost = 0 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: f, fps, config: { damping: 16, stiffness: 90 } });
  const draw = interpolate(f, [fps * 0.9, fps * 3.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const x = lost * 900;
  const y = lost * 500;
  const rot = -4 + lost * 28;
  const lines = [0, 1, 2, 3, 4, 5];
  return (
    <div
      style={{
        position: "absolute",
        left: 210,
        top: 600,
        width: 660,
        height: 760,
        opacity: enter * (1 - lost * 0.9),
        transform: `translate(${x}px, ${y + (1 - enter) * 120}px) rotate(${rot}deg)`,
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#FFFDF6",
          borderRadius: 28,
          boxShadow: "0 30px 70px rgba(20,18,43,0.18)",
          border: `3px solid ${C.line}`,
          position: "relative",
        }}
      >
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: -16,
              top: 50 + i * 85,
              width: 56,
              height: 22,
              borderRadius: 11,
              background: C.purple,
            }}
          />
        ))}
        {lines.map((i) => {
          const w = interpolate(draw, [i / lines.length, (i + 1) / lines.length], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <div key={i} style={{ position: "absolute", left: 90, top: 110 + i * 100, right: 60 }}>
              <div
                style={{
                  height: 12,
                  borderRadius: 6,
                  background: i % 3 === 0 ? C.blue : C.mute,
                  opacity: 0.55,
                  width: `${w * (i % 2 ? 70 : 92)}%`,
                }}
              />
              <div style={{ height: 3, marginTop: 24, background: C.line }} />
            </div>
          );
        })}
      </div>
    </div>
  );
};

const FloatingQuestions: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const items = [
    { x: 150, y: 520, d: 0 },
    { x: 880, y: 640, d: 8 },
    { x: 760, y: 1420, d: 16 },
  ];
  return (
    <>
      {items.map((q, i) => {
        const p = spring({ frame: f - q.d, fps, config: { damping: 10, stiffness: 120 } });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: q.x,
              top: q.y + Math.sin((f + q.d * 6) / 18) * 12,
              width: 110,
              height: 110,
              borderRadius: "50%",
              background: "#fff",
              boxShadow: "0 12px 30px rgba(43,31,255,0.18)",
              color: C.blue,
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 70,
              textAlign: "center",
              lineHeight: "110px",
              transform: `scale(${Math.max(p, 0)})`,
            }}
          >
            ?
          </div>
        );
      })}
    </>
  );
};

/* ---------- Phone with notes list ---------- */
const NOTES = [
  { n: "Nərmin", d: "12 noy", c: C.blue, w: [86, 58] },
  { n: "Elvin", d: "11 noy", c: C.purple, w: [74, 46] },
  { n: "Aysel", d: "09 noy", c: C.orange, w: [92, 64] },
  { n: "Rauf", d: "07 noy", c: C.blue, w: [66, 40] },
];

const Phone: React.FC<{ showLock: boolean; lockStart: number }> = ({ showLock, lockStart }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const up = spring({ frame: f, fps, config: { damping: 17, stiffness: 80 } });
  const lock = showLock ? spring({ frame: f - lockStart, fps, config: { damping: 9, stiffness: 140 } }) : 0;
  return (
    <div
      style={{
        position: "absolute",
        left: 290,
        top: 340,
        width: 500,
        height: 1020,
        transform: `translateY(${(1 - up) * 900}px)`,
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: 78,
          background: C.ink,
          padding: 16,
          boxShadow: "0 40px 90px rgba(43,31,255,0.28)",
          boxSizing: "border-box",
        }}
      >
        <div style={{ position: "relative", width: "100%", height: "100%", borderRadius: 64, background: "#fff", overflow: "hidden" }}>
          <div style={{ position: "absolute", top: 14, left: "50%", marginLeft: -62, width: 124, height: 34, borderRadius: 17, background: C.ink, zIndex: 3 }} />
          <div style={{ height: 190, background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`, padding: "92px 40px 0", boxSizing: "border-box" }}>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 42, color: "#fff" }}>Müşahidə qeydləri</div>
          </div>
          <div style={{ padding: "26px 28px" }}>
            {NOTES.map((r, i) => {
              const p = spring({ frame: f - fps * (0.7 + i * 0.35), fps, config: { damping: 16, stiffness: 120 } });
              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 20,
                    padding: "20px 22px",
                    marginBottom: 20,
                    borderRadius: 28,
                    background: C.soft,
                    opacity: Math.max(p, 0),
                    transform: `translateX(${(1 - Math.max(p, 0)) * 80}px)`,
                  }}
                >
                  <div
                    style={{
                      width: 76,
                      height: 76,
                      borderRadius: "50%",
                      background: r.c,
                      color: "#fff",
                      fontFamily: FONT,
                      fontWeight: 800,
                      fontSize: 34,
                      textAlign: "center",
                      lineHeight: "76px",
                      flex: "none",
                    }}
                  >
                    {r.n[0]}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontFamily: FONT, fontSize: 30, fontWeight: 700, color: C.ink }}>
                      <span>{r.n}</span>
                      <span style={{ color: C.mute, fontWeight: 500, fontSize: 26 }}>{r.d}</span>
                    </div>
                    <div style={{ marginTop: 14, height: 11, borderRadius: 6, background: C.line, width: `${r.w[0]}%` }} />
                    <div style={{ marginTop: 10, height: 11, borderRadius: 6, background: C.line, width: `${r.w[1]}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      {showLock && (
        <div
          style={{
            position: "absolute",
            right: -50,
            bottom: 90,
            width: 190,
            height: 190,
            borderRadius: "50%",
            background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`,
            boxShadow: "0 20px 50px rgba(43,31,255,0.35)",
            transform: `scale(${Math.max(lock, 0)})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg width="96" height="96" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="4" y="10.5" width="16" height="10.5" rx="3" fill="#fff" stroke="none" />
            <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" />
          </svg>
        </div>
      )}
    </div>
  );
};

/* ---------- End card ---------- */
const EndCard: React.FC<{ logoSrc: string; whatsapp: string }> = ({ logoSrc, whatsapp }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logo = spring({ frame: f, fps, config: { damping: 15, stiffness: 100 } });
  const t2 = spring({ frame: f - fps * 0.7, fps, config: { damping: 16, stiffness: 100 } });
  const t3 = spring({ frame: f - fps * 2.4, fps, config: { damping: 16, stiffness: 100 } });
  const pill = spring({ frame: f - fps * 3.6, fps, config: { damping: 12, stiffness: 120 } });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 420, left: 0, right: 0, textAlign: "center", opacity: logo, transform: `scale(${0.85 + 0.15 * logo})` }}>
        <div style={{ display: "inline-block", background: "#fff", borderRadius: 48, padding: "44px 64px", boxShadow: "0 24px 60px rgba(43,31,255,0.16)" }}>
          <Img src={staticFile(logoSrc)} style={{ width: 660, display: "block" }} />
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          top: 760,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: FONT,
          fontWeight: 800,
          fontSize: 70,
          lineHeight: 1.15,
          color: C.ink,
          opacity: Math.max(t2, 0),
          transform: `translateY(${(1 - Math.max(t2, 0)) * 40}px)`,
        }}
      >
        Tətbiq <span style={{ color: C.blue }}>tezliklə</span> Google Play-də
      </div>
      <div
        style={{
          position: "absolute",
          top: 980,
          left: 100,
          right: 100,
          textAlign: "center",
          fontFamily: FONT,
          fontWeight: 600,
          fontSize: 48,
          lineHeight: 1.3,
          color: C.mute,
          opacity: Math.max(t3, 0),
        }}
      >
        İlk istifadəçilərdən olmaq üçün WhatsApp-a yaz
      </div>
      <div style={{ position: "absolute", top: 1180, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${Math.max(pill, 0)})` }}>
        <div
          style={{
            background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`,
            color: "#fff",
            fontFamily: FONT,
            fontWeight: 800,
            fontSize: 62,
            padding: "30px 64px",
            borderRadius: 100,
            boxShadow: "0 20px 50px rgba(43,31,255,0.32)",
          }}
        >
          {whatsapp}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const PikmentReel: React.FC<PikmentReelProps> = ({ showPrivacyBeat, voiceSrc, logoSrc, whatsapp }) => {
  const { fps } = useVideoConfig();
  const S = (k: keyof typeof T) => ({ from: fr(T[k][0], fps), dur: fr(T[k][1] - T[k][0], fps) });
  const s1 = S("s1");
  const s2 = S("s2");
  const s3 = S("s3");
  // With the privacy beat the end card starts at 16.3 s (30 s total);
  // without it the end card starts at 13.9 s (27 s total).
  const endStart = showPrivacyBeat ? T.s5[0] : 13.9;
  const endTotal = showPrivacyBeat ? 30 : 27;
  const phoneDur = fr(endStart, fps) - s3.from;
  const s5 = { from: fr(endStart, fps), dur: fr(endTotal - endStart, fps) };

  return (
    <AbsoluteFill>
      <Background />
      <Audio src={staticFile(voiceSrc)} />

      <Sequence from={s1.from} durationInFrames={s1.dur}>
        <Headline parts={[{ t: "Uşaq haqqında " }, { t: "vacib bir şey", hl: true }, { t: " gördün?" }]} />
        <Notebook />
        <Subtitle text="Uşaq haqqında vacib bir şey gördün. Harada qeyd edirsən?" start={0.3} end={4.9} />
      </Sequence>

      <Sequence from={s2.from} durationInFrames={s2.dur}>
        <Headline parts={[{ t: "Kağız dəftər " }, { t: "itir", hl: true }]} />
        <LostNotebook />
        <FloatingQuestions />
        <Subtitle text="Kağız dəftər itir, yadda saxlamaq çətindir." start={0.1} end={3.6} />
      </Sequence>

      <Sequence from={s3.from} durationInFrames={phoneDur}>
        <Headline parts={[{ t: "Tarixli " }, { t: "müşahidə qeydləri", hl: true }]} top={130} size={78} />
        <Phone showLock={showPrivacyBeat} lockStart={fr(T.s4[0] - T.s3[0], fps)} />
        <Subtitle text="Pikment-də hər uşaq üçün tarixli müşahidə qeydi apar." start={0.2} end={4.5} />
        {showPrivacyBeat && <PrivacySubtitle offset={fr(T.s4[0] - T.s3[0], fps)} />}
      </Sequence>

      <Sequence from={s5.from} durationInFrames={s5.dur}>
        <EndCard logoSrc={logoSrc} whatsapp={whatsapp} />
      </Sequence>
    </AbsoluteFill>
  );
};

const LostNotebook: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lost = interpolate(f, [fps * 0.3, fps * 3.0], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <Notebook lost={lost} />;
};

const PrivacySubtitle: React.FC<{ offset: number }> = ({ offset }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = interpolate(f, [offset, offset + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 60, right: 60, bottom: 330, display: "flex", justifyContent: "center", opacity: op }}>
      <div
        style={{
          background: "rgba(255,255,255,0.94)",
          borderRadius: 28,
          padding: "20px 34px",
          fontFamily: FONT,
          fontWeight: 600,
          fontSize: 44,
          color: C.ink,
          boxShadow: "0 10px 40px rgba(43,31,255,0.14)",
        }}
      >
        Qeydlərini yalnız sən görürsən.
      </div>
    </div>
  );
};
