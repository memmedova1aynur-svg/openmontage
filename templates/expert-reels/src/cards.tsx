import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, Pill, T, clamp01, isPale, rgba } from "./theme";

// Flashcards: white index cards (thin ruled lines, a brand-blue tab) flip in on a deep navy
// stage. Scenes for study topics (open / closed book, recognise vs recall, self-quiz cards,
// a step recipe) plus a "flash" overlay card for the speaker. Everything is drawn in code.

const FPSX = 30;
const ease = Easing.out(Easing.cubic);
const prog = (t: number, at: number | undefined, d = 0.45) => (at === undefined ? 1 : ease(interpolate(t, [at, at + d], [0, 1], clamp01)));
const pop = (t: number, at: number | undefined) =>
  at === undefined ? 1 : t < at ? 0 : spring({ frame: Math.round((t - at) * FPSX), fps: FPSX, config: { damping: 12, stiffness: 190, mass: 0.6 } });

type SceneProps = { f: number; p: Record<string, any>; startT: number };

const Stage: React.FC = () => (
  <div style={{ position: "absolute", inset: 0, background: `radial-gradient(ellipse at 50% 38%, ${T.primary} 0%, ${T.primaryDeep} 85%)` }} />
);

// one index card; k = flip-in progress (0 edge-on, 1 facing)
const Card: React.FC<{ x: number; y: number; w: number; h: number; k: number; rot?: number; tab?: string; dim?: number; children?: React.ReactNode }> = ({
  x, y, w, h, k, rot = 0, tab, dim = 0, children,
}) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      height: h,
      transform: `perspective(1400px) rotateY(${(1 - k) * 80}deg) rotate(${rot}deg) translateY(${(1 - k) * 30}px)`,
      opacity: Math.min(1, k * 2) * (1 - dim),
      borderRadius: 18,
      background: `repeating-linear-gradient(180deg, #FFFFFF 0px, #FFFFFF 52px, ${rgba(T.accent, 0.45)} 52px, ${rgba(T.accent, 0.45)} 54px)`,
      backgroundPositionY: 70,
      boxShadow: "0 22px 50px rgba(0,0,0,0.45)",
      overflow: "hidden",
    }}
  >
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 64, background: "#FFFFFF", borderBottom: `4px solid ${T.accent}` }} />
    {tab && (
      <div style={{ position: "absolute", top: 14, left: 24, padding: "4px 14px", borderRadius: 8, background: T.accent, fontFamily: FONT, fontWeight: 800, fontSize: 24, letterSpacing: 3, color: T.primary }}>
        {tab}
      </div>
    )}
    <div style={{ position: "absolute", inset: "64px 0 0 0", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: "0 34px" }}>{children}</div>
  </div>
);

const Big: React.FC<{ size?: number; color?: string; weight?: number; children: React.ReactNode }> = ({ size = 64, color, weight = 900, children }) => (
  <div style={{ fontFamily: FONT, fontWeight: weight, fontSize: size, lineHeight: 1.1, color: color ?? T.primary }}>{children}</div>
);

const Head: React.FC<{ t: number; at: number; text: string }> = ({ t, at, text }) => {
  const k = prog(t, at, 0.5);
  return (
    <div style={{ position: "absolute", top: 270, left: 0, right: 0, textAlign: "center", opacity: k, transform: `translateY(${(1 - k) * 20}px)` }}>
      <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 62, color: "#FFFFFF" }}>{text}</span>
      <div style={{ margin: "14px auto 0", height: 8, width: 160 * k, borderRadius: 4, background: T.accent }} />
    </div>
  );
};

// ---------------------------------------------------------------- open book -> closed book -> few memories
const Book: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const open = prog(t, startT, 0.5);
  const close = prog(t, a.close, 0.6);
  const tan = pop(t, a.tanis);
  const think = pop(t, a.think);
  const ask = pop(t, a.ask);
  const few = prog(t, a.few, 0.5);
  const lines = (x: number) => Array.from({ length: 7 }).map((_, i) => <rect key={i} x={x} y={-150 + i * 42} width={i % 3 === 2 ? 150 : 230} height={12} rx={6} fill={i === 2 || i === 4 ? T.accent : rgba(T.primary, 0.25)} />);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <g transform={`translate(540 ${close > 0 ? 760 - 120 * close : 760}) scale(${0.85 + 0.15 * open})`} opacity={open}>
          {/* open spread, the right page folds over as the book closes */}
          <g opacity={1 - close}>
            <path d="M-20 -200 Q-170 -230 -330 -200 V200 Q-170 170 -20 200 Z" fill="#FFFFFF" />
            <g transform={`translate(20 0) scale(${1 - close} 1)`}>
              <path d="M0 -200 Q150 -230 310 -200 V200 Q150 170 0 200 Z" fill="#FFFFFF" />
              {lines(40)}
            </g>
            {lines(-300)}
            <path d="M-20 -200 V200 M20 -200 V200" stroke={rgba(T.primary, 0.25)} strokeWidth={4} />
          </g>
          {/* closed cover */}
          <g opacity={close}>
            <rect x={-170} y={-210} width={340} height={420} rx={18} fill={T.accent} stroke="#FFFFFF" strokeWidth={8} />
            <rect x={-110} y={-120} width={220} height={60} rx={10} fill="#FFFFFF" />
            <rect x={-170} y={-210} width={34} height={420} fill={rgba(T.primary, 0.25)} />
          </g>
        </g>
        {/* memory meter */}
        <g opacity={few} transform={`translate(0 ${(1 - few) * 30})`}>
          {Array.from({ length: 10 }).map((_, i) => (
            <circle key={i} cx={225 + i * 70} cy={1240} r={24} fill={i < 2 ? T.accent : "none"} stroke={i < 2 ? T.accent : rgba(T.accent, 0.45)} strokeWidth={4} />
          ))}
        </g>
      </svg>
      {a.tanis !== undefined && close < 0.5 && (
        <div style={{ position: "absolute", top: 1030, left: 0, right: 0, textAlign: "center", transform: `scale(${tan})`, opacity: Math.min(1, tan * 2) * (1 - close * 2) }}>
          <span style={{ background: T.accent, color: T.primary, fontFamily: FONT, fontWeight: 900, fontSize: 52, padding: "10px 28px", borderRadius: 16 }}>Tanış gəlir ✓</span>
        </div>
      )}
      {a.think !== undefined && close < 0.5 && (
        <div style={{ position: "absolute", top: 330, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${think})`, opacity: Math.min(1, think * 2) * (1 - close * 2) }}>
          <div style={{ position: "relative", background: "#FFFFFF", borderRadius: 60, padding: "22px 46px", fontFamily: FONT, fontWeight: 800, fontSize: 56, color: T.primary }}>
            “Bunu bilirəm”
            <div style={{ position: "absolute", bottom: -34, left: "46%", width: 30, height: 30, borderRadius: 15, background: "#FFFFFF" }} />
            <div style={{ position: "absolute", bottom: -64, left: "50%", width: 16, height: 16, borderRadius: 8, background: "#FFFFFF" }} />
          </div>
        </div>
      )}
      {a.ask !== undefined && (
        <div style={{ position: "absolute", top: 320, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `scale(${ask})`, opacity: Math.min(1, ask * 2) }}>
          <div style={{ background: "#FFFFFF", borderRadius: 24, padding: "20px 40px", fontFamily: FONT, fontWeight: 800, fontSize: 52, color: T.primary, boxShadow: "0 18px 40px rgba(0,0,0,0.4)" }}>
            İzah edə bilərəm<span style={{ color: T.accentSoft }}>?</span>
          </div>
        </div>
      )}
      {a.few !== undefined && (
        <div style={{ position: "absolute", top: 1300, left: 0, right: 0, textAlign: "center", opacity: few, fontFamily: FONT, fontWeight: 800, fontSize: 46, color: "#FFFFFF" }}>
          Çox az şey xatırlayırıq
        </div>
      )}
    </div>
  );
};

// a big cross or tick in a brand circle (Versus cards given as props)
const Mark: React.FC<{ kind: string }> = ({ kind }) => (
  <svg width={130} height={130} viewBox="0 0 130 130">
    <circle cx={65} cy={65} r={58} fill={kind === "x" ? rgba(T.primary, 0.08) : T.accent} stroke={T.primary} strokeWidth={6} />
    <path d={kind === "x" ? "M42 42 L88 88 M88 42 L42 88" : "M36 66 L56 86 L94 44"} fill="none" stroke={T.primary} strokeWidth={11} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// ---------------------------------------------------------------- two cards side by side (default: recognise vs recall)
const Versus: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const a = p.at ?? {};
  const A = prog(t, a.a, 0.5);
  const B = prog(t, a.b, 0.5);
  const ne = pop(t, a.b);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Head t={t} at={startT} text={p.title ?? ""} />
      {/* the cards never stand still: a slow float and sway, and the whole pair drifts closer */}
      <Card x={70 + Math.sin(t * 1.3) * 10} y={520 + Math.sin(t * 1.7) * 14} w={430} h={620} k={A} rot={-4 + Math.sin(t * 1.1) * 1.8} tab="1">
        {p.left ? <Mark kind={p.left.icon ?? "x"} /> : (
        <svg width={170} height={110} viewBox="0 0 170 110">
          <path d="M10 55 Q85 -10 160 55 Q85 120 10 55 Z" fill="none" stroke={T.primary} strokeWidth={8} />
          <circle cx={85} cy={55} r={24} fill={T.accent} stroke={T.primary} strokeWidth={6} />
        </svg>)}
        <Big size={p.left?.size ?? 58}>{p.left?.title ?? "Tanımaq"}</Big>
        <div style={{ fontFamily: FONT, fontWeight: 600, fontSize: 36, color: T.primary, marginTop: 16, lineHeight: 1.2 }}>{p.left?.sub ?? <>görəndə<br />“tanış gəlir”</>}</div>
      </Card>
      <Card x={580 + Math.sin(t * 1.2 + 2) * 10} y={540 + Math.sin(t * 1.6 + 1) * 14 - 30 * pop(t, a.c ?? 1e9)} w={430} h={620} k={B} rot={4 + Math.sin(t * 1.0 + 1) * 1.8} tab="2">
        {p.right ? <Mark kind={p.right.icon ?? "check"} /> : (
        <svg width={150} height={130} viewBox="0 0 150 130">
          <path d="M75 120 V20 M75 20 Q30 0 22 40 Q0 50 15 80 Q10 115 55 115 M75 20 Q120 0 128 40 Q150 50 135 80 Q140 115 95 115" fill={rgba(T.accent, 0.5)} stroke={T.primary} strokeWidth={7} strokeLinejoin="round" />
        </svg>)}
        <Big size={p.right?.size ?? 52}>{p.right?.title ?? "Xatırlamaq"}</Big>
        <div style={{ fontFamily: FONT, fontWeight: 600, fontSize: 36, color: T.primary, marginTop: 16, lineHeight: 1.2 }}>{p.right?.sub ?? <>baxmadan<br />özün deyirsən</>}</div>
      </Card>
      <div style={{ position: "absolute", top: 1190, left: 0, right: 0, textAlign: "center", transform: `scale(${ne})`, fontFamily: FONT, fontWeight: 900, fontSize: 130, color: T.accent }}>≠</div>
    </div>
  );
};

// ---------------------------------------------------------------- self-quiz cards
const Questions: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const qs: { text: string; at: number }[] = p.cards;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Head t={t} at={p.headAt ?? startT} text={p.title ?? ""} />
      {qs.map((q, i) => {
        const k = prog(t, q.at, 0.5);
        const later = qs.filter((x) => t >= x.at).length - 1 - i;
        return (
          <Card key={i} x={110} y={480 + i * 300} w={860} h={250} k={k} rot={i % 2 ? 2.5 : -2.5} tab={`SUAL ${i + 1}`} dim={later > 0 ? 0.0 : 0}>
            <Big size={q.text.length > 24 ? 50 : 60}>{q.text}</Big>
          </Card>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------- numbered recipe; the first step can be struck out
const Recipe: React.FC<SceneProps> = ({ f, p, startT }) => {
  const t = startT + f / FPSX;
  const steps: { text: string; at: number; strike?: number; n?: string }[] = p.steps;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Head t={t} at={startT} text={p.title ?? ""} />
      {steps.map((s, i) => {
        const k = prog(t, s.at, 0.5);
        const st = s.strike === undefined ? 0 : prog(t, s.strike, 0.3);
        return (
          <Card key={i} x={130} y={460 + i * 245} w={820} h={200} k={k} rot={i % 2 ? 1.5 : -1.5} tab={s.n} dim={0.45 * st}>
            <div style={{ position: "relative" }}>
              <Big size={60}>{s.text}</Big>
              {s.strike !== undefined && <div style={{ position: "absolute", left: -10, top: "50%", height: 10, width: `calc(${st} * (100% + 20px))`, background: T.primary, borderRadius: 5 }} />}
            </div>
          </Card>
        );
      })}
    </div>
  );
};

const wrap = (S: React.FC<SceneProps>): React.FC<SceneProps> => (props) => (
  <div style={{ position: "absolute", inset: 0 }}>
    <Stage />
    <S {...props} />
  </div>
);

export const CARDS: Record<string, React.FC<SceneProps>> = {
  fc_book: wrap(Book),
  fc_versus: wrap(Versus),
  fc_questions: wrap(Questions),
  fc_recipe: wrap(Recipe),
};

// ---------------------------------------------------------------- "flash": an index card over the speaker
export const Flash: React.FC<{ o: Pill & { rot?: number } }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (o.out - o.in) * fps;
  const k = ease(interpolate(frame, [0, 12], [0, 1], clamp01));
  const exit = interpolate(frame, [dur - 7, dur], [1, 0], clamp01);
  const chars = o.parts.map(([s]) => s).join("").length;
  const strikeF = o.strike !== undefined ? Math.round((o.strike - o.in) * fps) : null;
  const strike = strikeF === null ? 0 : interpolate(frame, [strikeF, strikeF + 8], [0, 1], clamp01);
  const rot = o.rot ?? (o.side === "r" ? 3 : -3);
  const box: React.CSSProperties =
    o.side === "l" ? { position: "absolute", top: o.top ?? 300, left: 50 } : o.side === "r" ? { position: "absolute", top: o.top ?? 300, right: 50 } : { position: "absolute", top: o.top ?? 300, left: 0, right: 0, display: "flex", justifyContent: "center" };
  return (
    <div style={{ position: "absolute", inset: 0, opacity: exit }}>
      <div style={box}>
        <div
          style={{
            position: "relative",
            maxWidth: o.side ? 540 : 900,
            padding: o.label ? "56px 40px 26px" : "24px 40px 28px",
            borderRadius: 16,
            background: "#FFFFFF",
            borderTop: `10px solid ${T.accent}`,
            boxShadow: "0 18px 40px rgba(0,0,0,0.35)",
            transform: `perspective(1200px) rotateX(${(1 - k) * -80}deg) rotate(${rot}deg)`,
            transformOrigin: "50% 0%",
            opacity: Math.min(1, k * 2),
            textAlign: "center",
          }}
        >
          {o.label && (
            <div style={{ position: "absolute", top: 12, left: 0, right: 0, fontFamily: FONT, fontWeight: 800, fontSize: 24, letterSpacing: 4, color: T.accentSoft }}>{o.label}</div>
          )}
          <div style={{ position: "relative", display: "inline-block", fontFamily: FONT, fontWeight: 900, fontSize: o.size ?? (chars > 26 ? 50 : chars > 14 ? 62 : 76), lineHeight: 1.1, color: T.primary, opacity: 1 - 0.45 * strike }}>
            {o.parts.map(([s, hl], i) => (
              // a pale accent (yellow) is unreadable on the white card: keep the word dark and mark it underneath
              <span key={i} style={{ color: hl && !isPale(T.accentSoft) ? T.accentSoft : T.primary, textDecoration: hl && !isPale(T.accentSoft) ? `underline 7px ${T.accent}` : undefined, textUnderlineOffset: 8, backgroundImage: hl && isPale(T.accentSoft) ? `linear-gradient(${T.accent}, ${T.accent})` : undefined, backgroundSize: "100% 38%", backgroundPosition: "0 88%", backgroundRepeat: "no-repeat" }}>{s}</span>
            ))}
            {strikeF !== null && <div style={{ position: "absolute", left: -10, top: "50%", height: 10, width: `calc(${strike} * (100% + 20px))`, background: T.primary, borderRadius: 5 }} />}
          </div>
        </div>
      </div>
    </div>
  );
};
