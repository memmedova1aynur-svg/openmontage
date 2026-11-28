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
import { Bg, C, FONT, GRAD, Subtitle, Swatches, clamp, fr } from "./PikmentSchoolAd";
import { Areas, End } from "./PikmentChooseAd";
import timing from "./pikmentServicesTiming.json";

/**
 * Pikment — "Məqsədinə uyğun təlim" (Reels 9:16, ~52 s), v2: dynamic motion.
 * Every course, duration and service on screen is quoted from pikment.az.
 * No prices, no outcome promises, no trainer names.
 */

export interface PikmentServicesAdProps {
  voiceSrc: string;
  logoSrc: string;
  whatsapp: string;
  site: string;
}

type Part = { t: string; hl?: boolean };
type Item = { ad: string; m: string };

const GROUPS: { title: Part[]; items: Item[] }[] = [
  {
    title: [{ t: "Bağça", hl: true }, { t: "sahəsində" }],
    items: [
      { ad: "Montessori metodu", m: "6 dərs · 1 ay" },
      { ad: "Bağça işi proqramı", m: "3 ay" },
      { ad: "Pedaqoqlar üçün oyun məktəbi", m: "10 dərs · 1 ay" },
      { ad: "Nağıl terapiyası", m: "5 dərs · 1 ay" },
    ],
  },
  {
    title: [{ t: "Bağça" }, { t: "açmaq", hl: true }, { t: "və idarəçilik" }],
    items: [
      { ad: "Bağça rəhbərləri üçün idarəçilik", m: "12 dərs · 1 ay" },
      { ad: "Bağça və erkən inkişaf mərkəzinin metodiki qurulması", m: "Xidmət" },
    ],
  },
  {
    title: [{ t: "Analar", hl: true }, { t: "üçün" }],
    items: [
      { ad: "Analar məktəbi", m: "16 dərs · 2 ay" },
      { ad: "Ana südü ilə qidalanma üzrə məsləhət", m: "Xidmət" },
    ],
  },
  {
    title: [{ t: "İnklüziv təhsil", hl: true }, { t: "və təhsil biznesi" }],
    items: [
      { ad: "İnklüziv təhsil", m: "24 dərs · 1 ay" },
      { ad: "Təhsil biznesində idarəetmə", m: "10 dərs · 1 ay" },
      { ad: "Təhsil biznesində marketinq", m: "10 dərs · 1 ay" },
      { ad: "Təhsildə satış", m: "10 dərs · 1 ay" },
    ],
  },
];

const gradText: React.CSSProperties = { background: GRAD, WebkitBackgroundClip: "text", color: "transparent" };

/** Word-by-word kinetic title. */
const KTitle: React.FC<{ parts: Part[]; top?: number; size?: number }> = ({ parts, top = 150, size = 84 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = parts.flatMap((p) => p.t.split(" ").filter(Boolean).map((w) => ({ w, hl: p.hl })));
  return (
    <div style={{ position: "absolute", top, left: 60, right: 60, textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: size, lineHeight: 1.1, letterSpacing: -2, color: C.white }}>
      {words.map((x, i) => {
        const p = Math.max(spring({ frame: f - i * 3, fps, config: { damping: 12, stiffness: 170 } }), 0);
        return (
          <span key={i} style={{ display: "inline-block", marginRight: "0.28em", opacity: Math.min(p * 1.4, 1), transform: `translateY(${(1 - p) * 60}px) scale(${0.75 + 0.25 * p})`, ...(x.hl ? gradText : {}) }}>
            {x.w}
          </span>
        );
      })}
    </div>
  );
};

/** Slow push-in on a scene's content. */
const Cam: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const z = interpolate(f, [0, dur * fps], [1, 1.045], clamp);
  return <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: "50% 45%" }}>{children}</AbsoluteFill>;
};

/** Diagonal gradient wipe; the cut happens at its midpoint. */
const Wipe: React.FC = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, 14], [0, 1], clamp);
  const left = interpolate(p, [0, 1], [-140, 110]);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: -300, bottom: -300, width: "140%", left: `${left}%`, transform: "skewX(-14deg)", background: "linear-gradient(90deg, #3B6BFF, #8B6CFF 55%, #21A0FF)", boxShadow: "0 0 120px rgba(139,108,255,0.8)" }} />
    </AbsoluteFill>
  );
};

/** Floating dots for depth. */
const Particles: React.FC = () => {
  const f = useCurrentFrame();
  const dots = Array.from({ length: 16 }, (_, i) => {
    const sx = (i * 197) % 1080;
    const sy = (i * 331) % 1920;
    const sp = 0.35 + (i % 5) * 0.12;
    const y = (sy - f * sp * 2 + 1920 * 3) % 1920;
    const x = sx + Math.sin(f / 50 + i) * 24;
    const r = 4 + (i % 4) * 3;
    return <div key={i} style={{ position: "absolute", left: x, top: y, width: r, height: r, borderRadius: "50%", background: i % 2 ? "rgba(139,108,255,0.5)" : "rgba(33,160,255,0.45)" }} />;
  });
  return <AbsoluteFill style={{ pointerEvents: "none" }}>{dots}</AbsoluteFill>;
};

const Progress: React.FC<{ total: number }> = ({ total }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return <div style={{ position: "absolute", top: 0, left: 0, height: 8, width: `${Math.min((f / (total * fps)) * 100, 100)}%`, background: GRAD, boxShadow: "0 0 18px rgba(59,107,255,0.8)" }} />;
};

const LogoMark: React.FC<{ logoSrc: string }> = ({ logoSrc }) => (
  <div style={{ position: "absolute", top: 58, left: 56, background: "#fff", borderRadius: 22, padding: "10px 22px", boxShadow: "0 10px 30px rgba(0,0,0,0.35)" }}>
    <Img src={staticFile(logoSrc)} style={{ width: 150, display: "block" }} />
  </div>
);

const CountUp: React.FC<{ to: number; label: string; delay: number }> = ({ to, label, delay }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(f, [fps * delay, fps * (delay + 1.2)], [0, 1], clamp);
  const pop = Math.max(spring({ frame: f - fps * delay, fps, config: { damping: 11, stiffness: 140 } }), 0);
  return (
    <div style={{ textAlign: "center", transform: `scale(${0.7 + 0.3 * pop})`, opacity: Math.min(pop * 1.5, 1) }}>
      <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 150, lineHeight: 1, letterSpacing: -4, ...gradText }}>{Math.round(to * p)}</div>
      <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 40, color: C.mute, marginTop: 6 }}>{label}</div>
    </div>
  );
};

const ItemList: React.FC<{ items: Item[]; dur: number }> = ({ items, dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const span = Math.max(dur - 2.4, 1);
  return (
    <div style={{ position: "absolute", top: 400 + (4 - items.length) * 70, left: 70, width: 940 }}>
      {items.map((c, i) => {
        const at = 1.0 + (items.length > 1 ? ((i * span) / (items.length - 1)) * 0.8 : 0);
        const p = Math.max(spring({ frame: f - fps * at, fps, config: { damping: 10, stiffness: 120 } }), 0);
        const shine = interpolate(f, [fps * (at + 0.25), fps * (at + 0.85)], [-30, 130], clamp);
        return (
          <div
            key={c.ad}
            style={{
              position: "relative",
              overflow: "hidden",
              minHeight: 150,
              marginBottom: 18,
              borderRadius: 32,
              background: "#fff",
              boxShadow: "0 18px 46px rgba(0,0,0,0.4)",
              padding: "22px 30px 22px 24px",
              boxSizing: "border-box",
              display: "flex",
              alignItems: "center",
              gap: 22,
              opacity: Math.min(p * 1.6, 1),
              transform: `translateX(${(1 - p) * 160}px) rotate(${(1 - p) * 2.5}deg) scale(${0.94 + 0.06 * p})`,
            }}
          >
            <div style={{ flex: "none", width: 64, height: 64, borderRadius: "50%", background: GRAD, color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 32, textAlign: "center", lineHeight: "64px" }}>{i + 1}</div>
            <div style={{ flex: 1, fontFamily: FONT, fontWeight: 800, fontSize: c.ad.length > 34 ? 31 : 38, lineHeight: 1.15, color: C.navy, letterSpacing: -0.5 }}>{c.ad}</div>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 29, color: "#fff", background: c.m === "Xidmət" ? "#177A45" : GRAD, borderRadius: 100, padding: "12px 22px", whiteSpace: "nowrap" }}>{c.m}</div>
            <div style={{ position: "absolute", top: 0, bottom: 0, left: `${shine}%`, width: "18%", transform: "skewX(-18deg)", background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.7), transparent)" }} />
          </div>
        );
      })}
    </div>
  );
};

const Mentor: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = Math.max(spring({ frame: f - fps * 0.8, fps, config: { damping: 13, stiffness: 100 } }), 0);
  const b = Math.max(spring({ frame: f - fps * 3.2, fps, config: { damping: 9, stiffness: 130 } }), 0);
  const pulse = 1 + 0.035 * Math.sin(f / 6) * (b > 0.9 ? 1 : 0);
  return (
    <>
      <div style={{ position: "absolute", top: 440, left: 70, width: 940, borderRadius: 40, background: "#fff", padding: "44px", boxSizing: "border-box", boxShadow: "0 24px 64px rgba(0,0,0,0.45)", opacity: a, transform: `translateY(${(1 - a) * 90}px) scale(${0.94 + 0.06 * a})` }}>
        <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 26, color: "#6B6A85", background: "#EEEDFB", display: "inline-block", borderRadius: 100, padding: "6px 20px" }}>Karyera və mentorluq</div>
        <div style={{ marginTop: 18, fontFamily: FONT, fontWeight: 800, fontSize: 56, color: C.navy, letterSpacing: -1 }}>Karyera mentorluğu</div>
        <div style={{ marginTop: 14, fontFamily: FONT, fontWeight: 500, fontSize: 34, lineHeight: 1.3, color: "#4B4A66" }}>Fərdi inkişaf və peşəkar istiqamətin müəyyənləşdirilməsi.</div>
      </div>
      <div style={{ position: "absolute", top: 930, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${b * pulse})` }}>
        <div style={{ background: C.green, color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 52, padding: "26px 56px", borderRadius: 100, boxShadow: "0 18px 46px rgba(23,122,69,0.55)" }}>Pulsuz konsultasiya</div>
      </div>
      <div style={{ position: "absolute", top: 1070, left: 0, right: 0, textAlign: "center", fontFamily: FONT, fontWeight: 500, fontSize: 32, color: C.mute, opacity: b }}>Heç bir öhdəlik yoxdur.</div>
    </>
  );
};

/** Particle burst around the call-to-action. */
const Burst: React.FC<{ at: number; y: number }> = ({ at, y }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = (f - fps * at) / (fps * 1.0);
  if (t < 0 || t > 1) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: 22 }, (_, k) => {
        const a = (k / 22) * Math.PI * 2;
        const d = 120 + t * (260 + (k % 3) * 90);
        const s = 14 - t * 10;
        return <div key={k} style={{ position: "absolute", left: 540 + Math.cos(a) * d - s / 2, top: y + Math.sin(a) * d * 0.6 - s / 2, width: s, height: s, borderRadius: k % 2 ? "50%" : 4, background: k % 3 === 0 ? "#21A0FF" : k % 3 === 1 ? "#8B6CFF" : "#fff", opacity: 1 - t }} />;
      })}
    </AbsoluteFill>
  );
};

const LINES = [
  "Uşaq inkişafı sahəsində daha peşəkar olmaq istəyirsən?",
  "Pikment-də məqsədlərinə uyğun təlim proqramları var.",
  "Bağça sahəsində karyera qurmaq və ya inkişaf etdirmək istəyənlər üçün: Montessori metodu, bağça işi, oyun məktəbi və nağıl terapiyası təlimləri.",
  "Öz bağçasını açmaq və ya idarəçilik bacarıqlarını inkişaf etdirmək istəyənlər üçün bağça idarəçiliyi təlimləri.",
  "Gələcək və indiki analar üçün Analar məktəbi və ana südü ilə qidalanma üzrə fərdi məsləhət xidməti.",
  "İnklüziv təhsil, təhsil biznesində idarəetmə, marketinq və satış üzrə təlimlər də var.",
  "Karyerada növbəti addımı atmaq istəyənlər üçün mentorluq. Başlamazdan əvvəl mentorla pulsuz konsultasiya.",
  "Özünə uyğun olanı seç, müraciət üçün WhatsApp-a yaz.",
];

export const PikmentServicesAd: React.FC<PikmentServicesAdProps> = ({ voiceSrc, logoSrc, whatsapp, site }) => {
  const { fps } = useVideoConfig();
  const starts: number[] = timing.voiceStarts;
  const durs: number[] = timing.voiceDurs;
  const total = timing.total;
  const lead = 0.15;
  const bounds = starts.map((s, i) => ({
    from: i === 0 ? 0 : s - lead,
    to: i === starts.length - 1 ? total : starts[i + 1] - lead,
  }));
  const seq = (i: number) => ({ from: fr(bounds[i].from, fps), dur: Math.max(fr(bounds[i].to - bounds[i].from, fps), 1) });
  const len = (i: number) => bounds[i].to - bounds[i].from;
  const sub = (i: number) => ({
    start: starts[i] - bounds[i].from,
    end: Math.min(starts[i] - bounds[i].from + durs[i] + 0.35, len(i)),
  });
  const gi = [2, 3, 4, 5];

  return (
    <AbsoluteFill>
      <Bg />
      <Particles />
      <Audio src={staticFile(voiceSrc)} />

      <Sequence from={seq(0).from} durationInFrames={seq(0).dur}>
        <Cam dur={len(0)}>
          <KTitle parts={[{ t: "Uşaq inkişafı sahəsində daha" }, { t: "peşəkar", hl: true }, { t: "olmaq istəyirsən?" }]} top={200} size={86} />
          <Swatches />
        </Cam>
        <Subtitle text={LINES[0]} {...sub(0)} />
      </Sequence>

      <Sequence from={seq(1).from} durationInFrames={seq(1).dur}>
        <Cam dur={len(1)}>
          <KTitle parts={[{ t: "Məqsədinə uyğun" }, { t: "təlim", hl: true }, { t: "proqramları" }]} top={150} size={74} />
          <Areas />
          <div style={{ position: "absolute", top: 1080, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 120 }}>
            <CountUp to={25} label="təlim" delay={1.2} />
            <CountUp to={6} label="sahə" delay={1.6} />
          </div>
        </Cam>
        <Subtitle text={LINES[1]} {...sub(1)} />
      </Sequence>

      {gi.map((b, k) => (
        <Sequence key={b} from={seq(b).from} durationInFrames={seq(b).dur}>
          <Cam dur={len(b)}>
            <KTitle parts={GROUPS[k].title} top={150} size={66} />
            <ItemList items={GROUPS[k].items} dur={len(b)} />
          </Cam>
          <Subtitle text={LINES[b]} {...sub(b)} />
        </Sequence>
      ))}

      <Sequence from={seq(6).from} durationInFrames={seq(6).dur}>
        <Cam dur={len(6)}>
          <KTitle parts={[{ t: "Mentorluq", hl: true }]} top={150} size={74} />
          <Mentor />
        </Cam>
        <Subtitle text={LINES[6]} {...sub(6)} />
      </Sequence>

      <Sequence from={seq(7).from} durationInFrames={seq(7).dur}>
        <End logoSrc={logoSrc} whatsapp={whatsapp} site={site} />
        <Burst at={1.3} y={1010} />
        <Subtitle text={LINES[7]} {...sub(7)} />
      </Sequence>

      {/* Logo badge on the middle scenes only (hook and end card already carry the brand). */}
      <Sequence from={seq(1).from} durationInFrames={seq(6).from + seq(6).dur - seq(1).from}>
        <LogoMark logoSrc={logoSrc} />
      </Sequence>

      {/* Scene-change wipes (cut lands on the wipe's midpoint). */}
      {bounds.slice(1).map((b, i) => (
        <Sequence key={`w${i}`} from={fr(b.from, fps) - 7} durationInFrames={14}>
          <Wipe />
        </Sequence>
      ))}

      <Progress total={total} />
    </AbsoluteFill>
  );
};
