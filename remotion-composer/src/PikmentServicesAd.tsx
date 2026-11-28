import React from "react";
import { AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Bg, C, FONT, GRAD, Grad, Subtitle, Swatches, Title, fr } from "./PikmentSchoolAd";
import { Areas, End } from "./PikmentChooseAd";
import timing from "./pikmentServicesTiming.json";

/**
 * Pikment — "Məqsədinə uyğun təlim" (Reels 9:16, ~45 s).
 * Every course, duration and service on screen is quoted from pikment.az.
 * No prices, no outcome promises, no trainer names.
 */

export interface PikmentServicesAdProps {
  voiceSrc: string;
  logoSrc: string;
  whatsapp: string;
  site: string;
}

type Item = { ad: string; m: string; accent?: boolean };

const GROUPS: { title: React.ReactNode; items: Item[] }[] = [
  {
    title: (
      <>
        <Grad>Bağça</Grad> sahəsində
      </>
    ),
    items: [
      { ad: "Montessori metodu", m: "6 dərs · 1 ay" },
      { ad: "Bağça işi proqramı", m: "3 ay" },
      { ad: "Pedaqoqlar üçün oyun məktəbi", m: "10 dərs · 1 ay" },
      { ad: "Nağıl terapiyası", m: "5 dərs · 1 ay" },
    ],
  },
  {
    title: (
      <>
        Bağça <Grad>açmaq</Grad> və idarəçilik
      </>
    ),
    items: [
      { ad: "Bağça rəhbərləri üçün idarəçilik", m: "12 dərs · 1 ay" },
      { ad: "Bağça və erkən inkişaf mərkəzinin metodiki qurulması", m: "Xidmət" },
    ],
  },
  {
    title: (
      <>
        <Grad>Analar</Grad> üçün
      </>
    ),
    items: [
      { ad: "Analar məktəbi", m: "16 dərs · 2 ay" },
      { ad: "Ana südü ilə qidalanma üzrə məsləhət", m: "Xidmət" },
    ],
  },
  {
    title: (
      <>
        <Grad>İnklüziv təhsil</Grad> və təhsil biznesi
      </>
    ),
    items: [
      { ad: "İnklüziv təhsil", m: "24 dərs · 1 ay" },
      { ad: "Təhsil biznesində idarəetmə", m: "10 dərs · 1 ay" },
      { ad: "Təhsil biznesində marketinq", m: "10 dərs · 1 ay" },
      { ad: "Təhsildə satış", m: "10 dərs · 1 ay" },
    ],
  },
];

const ItemList: React.FC<{ items: Item[]; dur: number }> = ({ items, dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const span = Math.max(dur - 2.4, 1);
  return (
    <div style={{ position: "absolute", top: 400 + (4 - items.length) * 70, left: 70, width: 940 }}>
      {items.map((c, i) => {
        const at = 1.0 + (items.length > 1 ? (i * span) / (items.length - 1 || 1) * 0.8 : 0);
        const p = spring({ frame: f - fps * at, fps, config: { damping: 16, stiffness: 100 } });
        const o = Math.max(p, 0);
        return (
          <div
            key={c.ad}
            style={{
              minHeight: 150,
              marginBottom: 18,
              borderRadius: 32,
              background: "#fff",
              boxShadow: "0 18px 46px rgba(0,0,0,0.38)",
              padding: "22px 32px",
              boxSizing: "border-box",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 22,
              opacity: o,
              transform: `translateX(${(1 - o) * 130}px)`,
            }}
          >
            <div style={{ flex: 1, fontFamily: FONT, fontWeight: 800, fontSize: c.ad.length > 34 ? 32 : 40, lineHeight: 1.15, color: C.navy, letterSpacing: -0.5 }}>{c.ad}</div>
            <div
              style={{
                fontFamily: FONT,
                fontWeight: 800,
                fontSize: 30,
                color: "#fff",
                background: c.m === "Xidmət" ? "#177A45" : GRAD,
                borderRadius: 100,
                padding: "12px 24px",
                whiteSpace: "nowrap",
              }}
            >
              {c.m}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const Mentor: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: f - fps * 0.8, fps, config: { damping: 15, stiffness: 100 } });
  const b = spring({ frame: f - fps * 3.2, fps, config: { damping: 11, stiffness: 120 } });
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 440,
          left: 70,
          width: 940,
          borderRadius: 40,
          background: "#fff",
          padding: "44px 44px",
          boxSizing: "border-box",
          boxShadow: "0 24px 64px rgba(0,0,0,0.42)",
          opacity: Math.max(a, 0),
          transform: `translateY(${(1 - Math.max(a, 0)) * 80}px)`,
        }}
      >
        <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 26, color: "#6B6A85", background: "#EEEDFB", display: "inline-block", borderRadius: 100, padding: "6px 20px" }}>Karyera və mentorluq</div>
        <div style={{ marginTop: 18, fontFamily: FONT, fontWeight: 800, fontSize: 56, color: C.navy, letterSpacing: -1 }}>Karyera mentorluğu</div>
        <div style={{ marginTop: 14, fontFamily: FONT, fontWeight: 500, fontSize: 34, lineHeight: 1.3, color: "#4B4A66" }}>Fərdi inkişaf və peşəkar istiqamətin müəyyənləşdirilməsi.</div>
      </div>
      <div style={{ position: "absolute", top: 930, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${Math.max(b, 0)})` }}>
        <div style={{ background: C.green, color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 52, padding: "26px 56px", borderRadius: 100, boxShadow: "0 18px 46px rgba(23,122,69,0.5)" }}>Pulsuz konsultasiya</div>
      </div>
      <div style={{ position: "absolute", top: 1070, left: 0, right: 0, textAlign: "center", fontFamily: FONT, fontWeight: 500, fontSize: 32, color: C.mute, opacity: Math.max(b, 0) }}>Heç bir öhdəlik yoxdur.</div>
    </>
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
  // Scene i runs from (start_i - lead) to (start_{i+1} - lead); the first scene starts at 0.
  const bounds = starts.map((s, i) => ({
    from: i === 0 ? 0 : s - lead,
    to: i === starts.length - 1 ? total : starts[i + 1] - lead,
  }));
  const seq = (i: number) => ({ from: fr(bounds[i].from, fps), dur: Math.max(fr(bounds[i].to - bounds[i].from, fps), 1) });
  const sub = (i: number) => ({
    start: starts[i] - bounds[i].from,
    end: Math.min(starts[i] - bounds[i].from + durs[i] + 0.35, bounds[i].to - bounds[i].from),
  });
  const gi = [2, 3, 4, 5]; // beats that show item lists, in order of GROUPS

  return (
    <AbsoluteFill>
      <Bg />
      <Audio src={staticFile(voiceSrc)} />

      <Sequence from={seq(0).from} durationInFrames={seq(0).dur}>
        <Title>
          Uşaq inkişafı sahəsində daha <Grad>peşəkar</Grad> olmaq istəyirsən?
        </Title>
        <Swatches />
        <Subtitle text={LINES[0]} {...sub(0)} />
      </Sequence>

      <Sequence from={seq(1).from} durationInFrames={seq(1).dur}>
        <Title top={170} size={78}>
          Məqsədinə uyğun <Grad>təlim</Grad> proqramları
        </Title>
        <Areas />
        <Subtitle text={LINES[1]} {...sub(1)} />
      </Sequence>

      {gi.map((b, k) => (
        <Sequence key={b} from={seq(b).from} durationInFrames={seq(b).dur}>
          <Title top={130} size={64}>
            {GROUPS[k].title}
          </Title>
          <ItemList items={GROUPS[k].items} dur={bounds[b].to - bounds[b].from} />
          <Subtitle text={LINES[b]} {...sub(b)} />
        </Sequence>
      ))}

      <Sequence from={seq(6).from} durationInFrames={seq(6).dur}>
        <Title top={130} size={64}>
          <Grad>Mentorluq</Grad>
        </Title>
        <Mentor />
        <Subtitle text={LINES[6]} {...sub(6)} />
      </Sequence>

      <Sequence from={seq(7).from} durationInFrames={seq(7).dur}>
        <End logoSrc={logoSrc} whatsapp={whatsapp} site={site} />
        <Subtitle text={LINES[7]} {...sub(7)} />
      </Sequence>
    </AbsoluteFill>
  );
};
