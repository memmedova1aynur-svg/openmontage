import React from "react";
import { Easing, interpolate, spring } from "remotion";
import { FONT, T, clamp01, rgba } from "./theme";

// "Studio" object scenes: solid, lit objects (phone, certificates, balance scale, task
// cards, a sales funnel) on a soft navy stage with one warm spotlight. Full 9:16 frame,
// everything drawn in code. Times in props are absolute and land on the spoken word.

const FPSX = 30;
const ease = Easing.out(Easing.cubic);
const prog = (t: number, at: number | undefined, d = 0.45) => (at === undefined ? 1 : ease(interpolate(t, [at, at + d], [0, 1], clamp01)));
const pop = (t: number, at: number | undefined) =>
  at === undefined ? 1 : t < at ? 0 : spring({ frame: Math.round((t - at) * FPSX), fps: FPSX, config: { damping: 12, stiffness: 190, mass: 0.6 } });
type SceneProps = { f: number; p: Record<string, any>; startT: number };
const tOf = (p: SceneProps) => p.startT + p.f / FPSX;

// The stage is never still: the light drifts and soft particles rise from the first frame,
// so a scene is alive before its first object lands on the spoken word.
// skins give each video in a batch its own world: "navy" (default), "paper" (light sheet with
// dots), "grid" (drafting grid), "split" (a wide brand-blue diagonal band sweeping behind)
let SKIN = "navy";
const Stage: React.FC<{ light?: boolean; t?: number }> = ({ light: l0, t = 0 }) => {
  const light = l0 || SKIN === "paper";
  const lx = 50 + Math.sin(t * 0.6) * 18;
  const ly = 30 + Math.cos(t * 0.45) * 10;
  if (SKIN === "grid" && !l0) {
    const off = (t * 12) % 60;
    return (
      <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: `radial-gradient(ellipse at ${lx}% ${ly}%, #22365E 0%, ${T.primaryDeep} 90%)` }}>
        <div style={{ position: "absolute", inset: -60, transform: `translate(${off}px, ${off}px)`, backgroundImage: `linear-gradient(${rgba(T.accent, 0.12)} 2px, transparent 2px), linear-gradient(90deg, ${rgba(T.accent, 0.12)} 2px, transparent 2px)`, backgroundSize: "60px 60px" }} />
        <div style={{ position: "absolute", inset: 0, background: `radial-gradient(ellipse at 50% 50%, transparent 40%, ${rgba(T.primaryDeep, 0.85)} 100%)` }} />
      </div>
    );
  }
  if (SKIN === "split" && !l0) {
    const sweep = Math.sin(t * 0.5) * 60;
    return (
      <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: T.primary }}>
        <div style={{ position: "absolute", left: -400, right: -400, top: 620 + sweep, height: 520, background: `linear-gradient(90deg, ${rgba(T.accent, 0.95)}, ${rgba(T.accentSoft, 0.95)})`, transform: "rotate(-14deg)" }} />
        <div style={{ position: "absolute", left: -400, right: -400, top: 1210 + sweep * 0.6, height: 40, background: rgba(T.accent, 0.5), transform: "rotate(-14deg)" }} />
      </div>
    );
  }
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        background: light
          ? SKIN === "paper"
            ? `radial-gradient(ellipse at ${lx}% ${ly + 5}%, #FFFFFF 0%, #F6F3EC 60%, #ECE6DA 100%)`
            : `radial-gradient(ellipse at ${lx}% ${ly + 5}%, #FFFFFF 0%, #EEF2F8 60%, #DCE4EF 100%)`
          : `radial-gradient(ellipse at ${lx}% ${ly}%, #2E4470 0%, ${T.primary} 45%, ${T.primaryDeep} 100%)`,
      }}
    >
      {Array.from({ length: 16 }).map((_, i) => {
        const sp = 40 + ((i * 53) % 70);
        const x = ((i * 137) % 1000) + 40 + Math.sin(t * 0.8 + i) * 30;
        const y = 1920 - (((t * sp + i * 211) % 2100) - 90);
        const r = 6 + (i % 4) * 4;
        return (
          <div key={i} style={{ position: "absolute", left: x, top: y, width: r * 2, height: r * 2, borderRadius: r, background: light ? rgba(T.primary, 0.08) : rgba(T.accent, 0.16 + (i % 3) * 0.06) }} />
        );
      })}
    </div>
  );
};

const Title: React.FC<{ t: number; at: number; text: string; dark?: boolean; top?: number }> = ({ t, at, text, dark: d0, top = 250 }) => {
  const dark = d0 || SKIN === "paper";
  const k = prog(t, at, 0.5);
  return (
    <div style={{ position: "absolute", top, left: 70, right: 70, textAlign: "center", opacity: k, transform: `translateY(${(1 - k) * 24}px)`, fontFamily: FONT, fontWeight: 900, fontSize: 64, lineHeight: 1.1, color: dark ? T.primary : "#FFFFFF" }}>
      {text}
    </div>
  );
};

// ---------------------------------------------------------------- phone with a thin profile
const Profile: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const a = props.p.at ?? {};
  const k = pop(t, props.startT);
  const bio = prog(t, a.bio, 0.4);
  const empty = prog(t, a.empty, 0.4);
  const circle = prog(t, a.bio === undefined ? undefined : a.bio + 0.3, 0.6);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage t={t} />
      <div style={{ position: "absolute", left: 230, top: 300, width: 620, height: 1180, borderRadius: 70, background: "#0B0F17", boxShadow: "0 40px 90px rgba(0,0,0,0.55)", transform: `translateY(${(1 - k) * 200}px) rotate(${(1 - k) * -6}deg)`, opacity: Math.min(1, k * 1.5) }}>
        <div style={{ position: "absolute", inset: 18, borderRadius: 54, background: "#FFFFFF", overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 30, padding: "70px 40px 20px" }}>
            <div style={{ width: 150, height: 150, borderRadius: 75, background: `linear-gradient(135deg, ${T.accent}, ${T.accentSoft})`, flexShrink: 0 }} />
            <div style={{ display: "flex", gap: 26, fontFamily: FONT, color: T.primary, textAlign: "center" }}>
              {["0", "12", "48"].map((n, i) => (
                <div key={i}>
                  <div style={{ fontWeight: 900, fontSize: 40 }}>{n}</div>
                  <div style={{ fontWeight: 500, fontSize: 22 }}>{["paylaşım", "izləyici", "izlənir"][i]}</div>
                </div>
              ))}
            </div>
          </div>
          <div style={{ position: "relative", margin: "10px 40px 0", fontFamily: FONT, fontWeight: 800, fontSize: 46, color: T.primary, opacity: bio, display: "inline-block" }}>
            {props.p.bio ?? "Təlimçi"}
            <svg width={300} height={120} viewBox="0 0 300 120" style={{ position: "absolute", left: -40, top: -30, overflow: "visible" }}>
              <path d="M30 70 C20 10 260 0 270 55 C280 110 60 120 40 80 C30 60 70 30 140 28" fill="none" stroke="#E5484D" strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - circle} />
            </svg>
          </div>
          <div style={{ margin: "60px 0 0", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6, padding: "0 6px" }}>
            {Array.from({ length: 9 }).map((_, i) => (
              <div key={i} style={{ height: 190, background: i < 1 ? rgba(T.accent, 0.7) : "#EEF1F5", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT, fontWeight: 900, fontSize: 70, color: rgba(T.primary, 0.25) }}>
                {i >= 1 && empty > 0 ? <span style={{ opacity: empty }}>?</span> : null}
              </div>
            ))}
          </div>
        </div>
      </div>
      {a.empty !== undefined && (
        <div style={{ position: "absolute", top: 1380, left: 0, right: 0, textAlign: "center", opacity: empty }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 50, color: T.primary, background: "#FFFFFF", padding: "12px 30px", borderRadius: 18 }}>{props.p.emptyText ?? "Təlimçilik: demək olar heç nə"}</span>
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------- two big numbers
const Numbers: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const rows: { big: string; small: string; at: number }[] = props.p.rows;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage t={t} />
      <Title t={t} at={props.startT} text={props.p.title ?? ""} />
      {rows.map((r, i) => {
        const k = pop(t, r.at);
        const frame = pop(t, props.startT + 0.1 + i * 0.15);
        return (
          <React.Fragment key={i}>
          <div style={{ position: "absolute", top: 520 + i * 430, left: 90, right: 90, height: 360, borderRadius: 40, border: `4px dashed ${rgba(T.accent, 0.6)}`, transform: `scale(${0.8 + 0.2 * frame})`, opacity: frame * (1 - Math.min(1, k * 2)) }} />
          <div style={{ position: "absolute", top: 520 + i * 430, left: 90, right: 90, height: 360, borderRadius: 40, background: "#FFFFFF", boxShadow: "0 30px 70px rgba(0,0,0,0.4)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", transform: `scale(${0.7 + 0.3 * k})`, opacity: Math.min(1, k * 2) }}>
            <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 150, lineHeight: 1, color: T.primary, letterSpacing: -4 }}>{r.big}</div>
            <div style={{ marginTop: 18, fontFamily: FONT, fontWeight: 700, fontSize: 44, color: T.primary, background: T.accent, padding: "6px 24px", borderRadius: 14 }}>{r.small}</div>
          </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------- balance scale with three weights
const Balance: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const a = props.p.at ?? {};
  const words: [string, number][] = [
    [props.p.w1 ?? "Güvən", a.w1],
    [props.p.w2 ?? "Keyfiyyət", a.w2],
    [props.p.w3 ?? "Gəlir", a.w3],
  ];
  const level = prog(t, a.level, 0.9);
  const tilt = (1 - level) * 12 * (t >= (a.w1 ?? 0) ? 1 : 0) + Math.sin(t * 3) * 1.2 * level;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage t={t} />
      <Title t={t} at={props.startT} text={props.p.title ?? "Balans"} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <path d="M540 640 V1300 M400 1300 H680" stroke="#FFFFFF" strokeWidth={14} strokeLinecap="round" />
        <circle cx={540} cy={640} r={22} fill={T.accent} />
        <g transform={`rotate(${tilt} 540 660)`}>
          <path d="M170 660 H910" stroke="#FFFFFF" strokeWidth={12} strokeLinecap="round" />
          {[200, 880].map((x, i) => (
            <g key={i} transform={`rotate(${-tilt} ${x} 660)`}>
              <path d={`M${x} 660 L${x - 110} 900 M${x} 660 L${x + 110} 900`} stroke={rgba("#FFFFFF", 0.7)} strokeWidth={5} />
              <path d={`M${x - 140} 900 Q${x} 980 ${x + 140} 900 Z`} fill={T.accent} />
            </g>
          ))}
        </g>
      </svg>
      {words.map(([w, at], i) => {
        const k = pop(t, at);
        const pos = [
          { left: 60, top: 760 },
          { left: 650, top: 760 },
          { left: 340, top: 1080 },
        ][i];
        return (
          <div key={i} style={{ position: "absolute", ...pos, width: 370, textAlign: "center", transform: `scale(${k})`, opacity: Math.min(1, k * 2) }}>
            <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 52, color: T.primary, background: "#FFFFFF", padding: "10px 24px", borderRadius: 16, boxShadow: "0 14px 30px rgba(0,0,0,0.35)" }}>{w}</span>
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------- certificates pile up, then the question
const Certs: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const a = props.p.at ?? {};
  const n = props.p.count ?? 6;
  const q = pop(t, a.q);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage t={t} />
      <Title t={t} at={props.startT} text={props.p.title ?? ""} />
      {Array.from({ length: n }).map((_, i) => {
        const at = (a.pile ?? props.startT) + i * 0.22;
        const k = pop(t, at);
        const rot = [-8, 5, -3, 9, -6, 3, -1][i % 7];
        return (
          <div key={i} style={{ position: "absolute", left: 190 + (i % 2) * 30, top: 560 - i * 34 + (1 - k) * -400, width: 700, height: 480, borderRadius: 14, background: "#FFFDF7", border: `10px double ${T.accentSoft}`, boxShadow: "0 18px 40px rgba(0,0,0,0.35)", transform: `rotate(${rot}deg)`, opacity: Math.min(1, k * 2), display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 18 }}>
            <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 52, letterSpacing: 6, color: T.primary }}>SERTİFİKAT</div>
            <div style={{ width: 380, height: 10, borderRadius: 5, background: rgba(T.primary, 0.15) }} />
            <div style={{ width: 300, height: 10, borderRadius: 5, background: rgba(T.primary, 0.15) }} />
            <svg width={90} height={110} viewBox="0 0 90 110">
              <circle cx={45} cy={40} r={34} fill={T.accent} stroke={T.primary} strokeWidth={5} />
              <path d="M25 70 L18 108 L45 92 L72 108 L65 70" fill={T.accentSoft} stroke={T.primary} strokeWidth={5} strokeLinejoin="round" />
            </svg>
          </div>
        );
      })}
      {a.q !== undefined && (
        <div style={{ position: "absolute", top: 1180, left: 0, right: 0, textAlign: "center", transform: `scale(${q})` }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 64, color: T.primary, background: T.accent, padding: "16px 40px", borderRadius: 22, boxShadow: "0 18px 40px rgba(0,0,0,0.4)" }}>{props.p.question ?? "Nə dəyişib?"}</span>
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------- info that is not used fades away
const Forget: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const a = props.p.at ?? {};
  const show = prog(t, a.dots, 0.6);
  const fade = prog(t, a.fade, 1.6);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage t={t} />
      <Title t={t} at={props.startT} text={props.p.title ?? ""} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: 20 }).map((_, i) => {
          const x = 200 + (i % 5) * 170;
          const y = 560 + Math.floor(i / 5) * 170;
          const stay = i === 7 || i === 13;
          const k = interpolate(show, [i / 30, i / 30 + 0.3], [0, 1], clamp01);
          const op = stay ? 1 : 1 - 0.88 * fade;
          return (
            <g key={i} opacity={k * op} transform={`translate(0 ${stay ? 0 : fade * 30})`}>
              <rect x={x - 60} y={y - 60} width={120} height={120} rx={26} fill={stay ? T.accent : SKIN === "paper" ? rgba(T.primary, 0.1) : "#FFFFFF"} />
              <text x={x} y={y + 18} fontFamily={FONT} fontWeight={900} fontSize={50} fill={T.primary} textAnchor="middle">{i + 1}</text>
            </g>
          );
        })}
      </svg>
      <div style={{ position: "absolute", top: 1300, left: 0, right: 0, textAlign: "center", opacity: fade }}>
        <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 46, color: SKIN === "paper" ? T.primary : "#FFFFFF" }}>{props.p.fadeText ?? "tətbiq olunmayan unudulur"}</span>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- titled checklist cards (examples / questions / steps)
const Checks: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const blocks: { head: string; at: number; items: { text: string; at: number }[] }[] = props.p.blocks;
  const mark = props.p.mark ?? "?";
  let y = props.p.top ?? 420;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage light={props.p.light} t={t} />
      {props.p.title && <Title t={t} at={props.startT} text={props.p.title} dark={props.p.light} />}
      {blocks.map((b, bi) => {
        const hk = prog(t, b.at, 0.4);
        const top = y;
        y += 110 + b.items.length * 120 + 40;
        return (
          <div key={bi} style={{ position: "absolute", top, left: 80, right: 80, opacity: hk, transform: `translateY(${(1 - hk) * 30}px)` }}>
            <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 52, color: props.p.light || SKIN === "paper" ? T.primary : "#FFFFFF", marginBottom: 18 }}>{b.head}</div>
            {b.items.map((it, ii) => {
              const k = pop(t, it.at);
              return (
                <div key={ii} style={{ display: "flex", alignItems: "center", gap: 24, height: 100, marginBottom: 20, padding: "0 30px", borderRadius: 24, background: "#FFFFFF", boxShadow: "0 12px 28px rgba(0,0,0,0.22)", transform: `scale(${0.85 + 0.15 * k})`, opacity: Math.min(1, k * 2), transformOrigin: "0% 50%" }}>
                  <div style={{ width: 58, height: 58, borderRadius: 29, background: T.accent, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT, fontWeight: 900, fontSize: 36, color: T.primary, flexShrink: 0 }}>{mark}</div>
                  <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: it.text.length > 26 ? 40 : 46, color: T.primary }}>{it.text}</div>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------- too many goals: cards scatter in, then all but one are struck off
const Juggle: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const items: { text: string; at: number }[] = props.p.items;
  const keep = props.p.keep ?? 0;
  const strike = props.p.strikeAt === undefined ? 0 : prog(t, props.p.strikeAt, 0.5);
  const focus = props.p.focusAt === undefined ? 0 : prog(t, props.p.focusAt, 0.6);
  const spots = [
    { x: 90, y: 420, r: -6 },
    { x: 520, y: 560, r: 5 },
    { x: 130, y: 760, r: 4 },
    { x: 500, y: 930, r: -5 },
    { x: 150, y: 1120, r: -3 },
  ];
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage t={t} />
      {props.p.title && <Title t={t} at={props.startT} text={props.p.title} top={240} />}
      {items.map((it, i) => {
        const s = spots[i % spots.length];
        const k = pop(t, it.at);
        const kept = i === keep;
        const st = kept ? 0 : strike;
        const fx = kept ? focus : 0;
        const x = s.x + (kept ? (270 - s.x) * fx : 0);
        const y = s.y + (kept ? (740 - s.y) * fx : 0);
        return (
          <div key={i} style={{ position: "absolute", left: x, top: y, width: 480, height: 150, borderRadius: 26, background: kept && fx > 0.5 ? T.accent : "#FFFFFF", boxShadow: "0 18px 40px rgba(0,0,0,0.4)", transform: `rotate(${s.r * (1 - fx)}deg) scale(${(0.6 + 0.4 * k) * (1 + 0.25 * fx)})`, opacity: Math.min(1, k * 2) * (1 - 0.7 * st), display: "flex", alignItems: "center", justifyContent: "center", zIndex: kept ? 2 : 1 }}>
            <span style={{ position: "relative", fontFamily: FONT, fontWeight: 900, fontSize: it.text.length > 14 ? 44 : 52, color: T.primary }}>
              {it.text}
              <span style={{ position: "absolute", left: -10, right: -10, top: "50%", height: 9, background: "#E5484D", borderRadius: 5, transform: `scaleX(${st})`, transformOrigin: "0 50%" }} />
            </span>
          </div>
        );
      })}
      {props.p.focusText && (
        <div style={{ position: "absolute", top: 1010, left: 0, right: 0, textAlign: "center", opacity: focus }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 60, color: "#FFFFFF" }}>{props.p.focusText}</span>
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------- leaking funnel: potential customers drop out
const Funnel: React.FC<SceneProps> = (props) => {
  const t = tOf(props);
  const a = props.p.at ?? {};
  const pour = prog(t, a.pour, 0.8);
  const leak = Math.max(0, t - (a.leak ?? 1e9));
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Stage t={t} />
      <Title t={t} at={props.startT} text={props.p.title ?? ""} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <path d="M200 520 H880 L640 920 V1180 H440 V920 Z" fill={rgba("#FFFFFF", 0.1)} stroke="#FFFFFF" strokeWidth={10} strokeLinejoin="round" opacity={pour} />
        {/* holes on the sides */}
        <circle cx={300} cy={690} r={16} fill={T.primaryDeep} stroke="#E5484D" strokeWidth={5} opacity={leak > 0 ? 1 : 0} />
        <circle cx={770} cy={720} r={16} fill={T.primaryDeep} stroke="#E5484D" strokeWidth={5} opacity={leak > 0 ? 1 : 0} />
        {Array.from({ length: 26 }).map((_, i) => {
          const seed = (i * 37) % 26;
          const x0 = 260 + ((seed * 23) % 560);
          const appear = (a.pour ?? props.startT) + (i % 13) * 0.08;
          if (t < appear) return null;
          const fall = Math.min(1, (t - appear) / 0.6);
          const y0 = 460 + fall * (180 + (seed % 5) * 30);
          const leaks = i % 3 !== 0;
          const lt = leaks ? Math.max(0, leak - (i % 9) * 0.18) : 0;
          const side = x0 < 540 ? -1 : 1;
          const x = x0 + side * lt * 260;
          const y = y0 + lt * lt * 700;
          const op = leaks ? Math.max(0, 1 - lt * 0.8) : 1;
          return <circle key={i} cx={x} cy={y} r={20} fill={leaks && lt > 0 ? "#E5484D" : T.accent} opacity={op} />;
        })}
      </svg>
      {props.p.leakText && (
        <div style={{ position: "absolute", top: 1250, left: 0, right: 0, textAlign: "center", opacity: Math.min(1, leak * 1.5) }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 50, color: "#FFFFFF" }}>{props.p.leakText}</span>
        </div>
      )}
    </div>
  );
};

// slow push-in and sway on the whole scene (camera move), on from the first frame
const live = (S: React.FC<SceneProps>): React.FC<SceneProps> => (props) => {
  SKIN = props.p.skin ?? "navy";
  const local = props.f / FPSX;
  const z = 1 + Math.min(0.07, local * 0.012);
  const sway = Math.sin(local * 0.9) * 0.6;
  const enter = ease(interpolate(local, [0, 0.45], [0, 1], clamp01));
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, transform: `scale(${z * (1.06 - 0.06 * enter)}) rotate(${sway}deg)` }}>
        <S {...props} />
      </div>
    </div>
  );
};

export const STUDIO: Record<string, React.FC<SceneProps>> = {
  st_profile: live(Profile),
  st_numbers: live(Numbers),
  st_balance: live(Balance),
  st_certs: live(Certs),
  st_forget: live(Forget),
  st_checks: live(Checks),
  st_juggle: live(Juggle),
  st_funnel: live(Funnel),
};
