// Motion graphics səhnələri (data / IT videoları): sütun, xətt, halqa, müqayisə, proses, kod, KPI.
// Rəng: müştərinin theme-i (T). Məzmun (rəqəm, etiket) YALNIZ danışıqdan — səhnə özü heç nə uydurmur.
// Yerləşmə: əsas məzmun y≈230–1080 (aşağıda altyazı, sağ-aşağıda danışanın kiçik pəncərəsi üçün yer qalır).
// Vaxtlar (times, at) səhnənin öz başlanğıcından saniyələrdir.
import React from "react";
import { AbsoluteFill, interpolate, spring, useVideoConfig } from "remotion";
import { FONT, T, clamp01, rgba } from "./theme";

type SceneProps = { f: number; p: Record<string, any>; startT: number };
const ease = (x: number) => 1 - Math.pow(1 - x, 3);
// Azərbaycan yazılışı: minliklər boşluqla (1 200), kəsr vergüllə (4,5)
const fmt = (v: number, target: number) =>
  Number.isInteger(target) ? String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0") : v.toFixed(1).replace(".", ",");

const Head: React.FC<{ f: number; label?: string; title?: string }> = ({ f, label, title }) => {
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 14, stiffness: 150 } });
  return (
    <div style={{ position: "absolute", top: 230, left: 80, right: 80, textAlign: "left", opacity: s, transform: `translateY(${(1 - s) * 30}px)` }}>
      {label && <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 34, letterSpacing: 3, color: T.accent, textTransform: "uppercase" }}>{label}</div>}
      {title && <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 64, color: T.text, lineHeight: 1.12, marginTop: 8 }}>{title}</div>}
    </div>
  );
};

// props: label, title, unit, items [{label, value, highlight?}], stagger (s, default 0.25)
const MgBars: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const items: { label: string; value: number; highlight?: boolean }[] = p.items ?? [];
  const max = Math.max(1, ...items.map((i) => i.value));
  const top = p.title ? 470 : 380;
  const rowH = Math.min(150, 620 / Math.max(1, items.length));
  return (
    <AbsoluteFill>
      <Head f={f} label={p.label} title={p.title} />
      {items.map((it, i) => {
        const k = ease(interpolate(f, [8 + i * (p.stagger ?? 0.25) * fps, 8 + i * (p.stagger ?? 0.25) * fps + 0.8 * fps], [0, 1], clamp01));
        const w = 640 * (it.value / max) * k;
        const hi = it.highlight ?? i === items.findIndex((x) => x.value === max);
        return (
          <div key={i} style={{ position: "absolute", top: top + i * rowH, left: 80, right: 80, opacity: Math.min(1, k * 3) }}>
            <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 36, color: T.text, marginBottom: 10 }}>{it.label}</div>
            <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
              <div style={{ height: rowH * 0.36, width: Math.max(8, w), borderRadius: 14, background: hi ? T.accent : rgba(T.accentSoft, 0.55) }} />
              <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 46, color: hi ? T.accent : T.text }}>{fmt(it.value * k, it.value)}{p.unit ?? ""}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// props: label, title, unit, points [{label, value}], drawSeconds (default 1.6)
const MgLine: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const pts: { label: string; value: number }[] = p.points ?? [];
  const W = 900, H = 520, X0 = 90, Y0 = 470;
  const min = Math.min(0, ...pts.map((q) => q.value)), max = Math.max(1, ...pts.map((q) => q.value));
  const xy = pts.map((q, i) => [X0 + (W * i) / Math.max(1, pts.length - 1), Y0 + H - (H * (q.value - min)) / (max - min || 1)]);
  const k = ease(interpolate(f, [8, 8 + (p.drawSeconds ?? 1.6) * fps], [0, 1], clamp01));
  const total = xy.reduce((acc, c, i) => (i ? acc + Math.hypot(c[0] - xy[i - 1][0], c[1] - xy[i - 1][1]) : 0), 0);
  const d = xy.map((c, i) => `${i ? "L" : "M"}${c[0]},${c[1]}`).join(" ");
  const last = pts.length ? pts[pts.length - 1] : null;
  return (
    <AbsoluteFill>
      <Head f={f} label={p.label} title={p.title} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <line x1={X0} y1={Y0 + H} x2={X0 + W} y2={Y0 + H} stroke={rgba(T.text, 0.35)} strokeWidth={3} />
        <path d={d} fill="none" stroke={T.accent} strokeWidth={12} strokeLinecap="round" strokeLinejoin="round"
          strokeDasharray={total} strokeDashoffset={total * (1 - k)} />
        {xy.map((c, i) => (k >= i / Math.max(1, xy.length - 1) - 0.001 ? <circle key={i} cx={c[0]} cy={c[1]} r={14} fill={T.accent} stroke={T.primaryDeep} strokeWidth={5} /> : null))}
        {pts.map((q, i) => <text key={`l${i}`} x={xy[i][0]} y={Y0 + H + 56} textAnchor="middle" fontFamily="Montserrat" fontWeight={700} fontSize={30} fill={T.text}>{q.label}</text>)}
      </svg>
      {last && k > 0.95 && (
        <div style={{ position: "absolute", left: Math.min(760, xy[xy.length - 1][0] - 120), top: xy[xy.length - 1][1] - 110, fontFamily: FONT, fontWeight: 900, fontSize: 54, color: T.accent }}>
          {fmt(last.value, last.value)}{p.unit ?? ""}
        </div>
      )}
    </AbsoluteFill>
  );
};

// props: label, title, value (0–100), suffix (default "%"), caption
const MgDonut: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const k = ease(interpolate(f, [8, 8 + 1.4 * fps], [0, 1], clamp01));
  const v = (p.value ?? 0) * k, R = 230, C = 2 * Math.PI * R;
  return (
    <AbsoluteFill>
      <Head f={f} label={p.label} title={p.title} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <circle cx={540} cy={770} r={R} fill="none" stroke={rgba(T.accentSoft, 0.25)} strokeWidth={56} />
        <circle cx={540} cy={770} r={R} fill="none" stroke={T.accent} strokeWidth={56} strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={C * (1 - Math.min(100, v) / 100)} transform="rotate(-90 540 770)" />
      </svg>
      <div style={{ position: "absolute", top: 690, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 150, color: T.text, lineHeight: 1 }}>
        {fmt(v, p.value ?? 0)}{p.suffix ?? "%"}
      </div>
      {p.caption && <div style={{ position: "absolute", top: 1050, left: 90, right: 90, textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: 46, color: T.text, opacity: k }}>{p.caption}</div>}
    </AbsoluteFill>
  );
};

// props: label, title, a {label, value, unit?}, b {label, value, unit?}, vs (default "vs")
const MgCompare: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const a = p.a ?? { label: "", value: 0 }, b = p.b ?? { label: "", value: 0 };
  const max = Math.max(1, a.value, b.value);
  const col = (o: any, i: number) => {
    const k = ease(interpolate(f, [8 + i * 0.35 * fps, 8 + i * 0.35 * fps + fps], [0, 1], clamp01));
    const h = 460 * (o.value / max) * k;
    const win = o.value === max;
    return (
      <div key={i} style={{ position: "absolute", left: i ? 600 : 140, width: 340, top: 470, height: 640 }}>
        <div style={{ position: "absolute", bottom: 90, width: "100%", height: h, borderRadius: 24, background: win ? T.accent : rgba(T.accentSoft, 0.5) }} />
        <div style={{ position: "absolute", bottom: 100 + h, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 64, color: win ? T.accent : T.text }}>
          {fmt(o.value * k, o.value)}{o.unit ?? p.unit ?? ""}
        </div>
        <div style={{ position: "absolute", bottom: 0, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: 40, color: T.text }}>{o.label}</div>
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <Head f={f} label={p.label} title={p.title} />
      {col(a, 0)}
      {col(b, 1)}
      <div style={{ position: "absolute", top: 760, width: "100%", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 52, color: rgba(T.text, 0.6) }}>{p.vs ?? "vs"}</div>
    </AbsoluteFill>
  );
};

// props: label, title, steps [text], times [s] (default 0.5 s aralıqla)
const MgSteps: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const steps: string[] = p.steps ?? [];
  const times: number[] = p.times ?? steps.map((_, i) => 0.3 + i * 0.5);
  const gap = Math.min(150, 640 / Math.max(1, steps.length));
  return (
    <AbsoluteFill>
      <Head f={f} label={p.label} title={p.title} />
      {steps.map((s, i) => {
        const k = spring({ frame: f - Math.round(times[i] * fps), fps, config: { damping: 14, stiffness: 170 } });
        const y = (p.title ? 470 : 390) + i * gap;
        return (
          <div key={i} style={{ position: "absolute", top: y, left: 80, right: 80, display: "flex", alignItems: "center", gap: 28, opacity: Math.min(1, k * 1.5), transform: `translateX(${(1 - k) * 60}px)` }}>
            <div style={{ flex: "0 0 auto", width: 84, height: 84, borderRadius: 42, background: T.accent, color: T.onAccent, fontFamily: FONT, fontWeight: 900, fontSize: 42, display: "flex", alignItems: "center", justifyContent: "center" }}>{i + 1}</div>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 44, color: T.text, lineHeight: 1.15 }}>{s}</div>
            {i < steps.length - 1 && <div style={{ position: "absolute", left: 40, top: 88, width: 4, height: gap - 92, background: rgba(T.accent, 0.5 * Math.min(1, k)) }} />}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// props: label, title, lines [string], cps (simvol/san, default 28), prompt (default "$")
const MgCode: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const lines: string[] = p.lines ?? [];
  let budget = Math.max(0, (f - 8) / fps) * (p.cps ?? 28);
  const shown = lines.map((l) => { const n = Math.min(l.length, Math.floor(budget)); budget -= l.length + 4; return l.slice(0, Math.max(0, n)); });
  const cursor = Math.floor(f / 15) % 2 === 0;
  return (
    <AbsoluteFill>
      <Head f={f} label={p.label} title={p.title} />
      <div style={{ position: "absolute", top: p.title ? 470 : 380, left: 70, right: 70, borderRadius: 28, background: "#0F1420", boxShadow: "0 30px 80px rgba(0,0,0,0.45)", overflow: "hidden" }}>
        <div style={{ height: 64, background: "#1B2233", display: "flex", alignItems: "center", gap: 14, paddingLeft: 26 }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <div key={c} style={{ width: 22, height: 22, borderRadius: 11, background: c }} />)}
        </div>
        <div style={{ padding: "28px 34px 40px", fontFamily: "'DejaVu Sans Mono', monospace", fontSize: 36, lineHeight: 1.55, color: "#E6EDF7", whiteSpace: "pre-wrap", minHeight: 300 }}>
          {shown.map((l, i) => (l.length || i === 0 ? (
            <div key={i}><span style={{ color: T.accent }}>{p.prompt ?? "$"} </span>{l}{i === shown.findIndex((x, j) => x.length < lines[j].length) && cursor ? "▌" : ""}</div>
          ) : null))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// props: label, title, items [{value, prefix?, suffix?, label}] (2–4)
const MgKpi: React.FC<SceneProps> = ({ f, p }) => {
  const { fps } = useVideoConfig();
  const items: { value: number; prefix?: string; suffix?: string; label: string }[] = (p.items ?? []).slice(0, 4);
  return (
    <AbsoluteFill>
      <Head f={f} label={p.label} title={p.title} />
      {items.map((it, i) => {
        const k = ease(interpolate(f, [8 + i * 6, 8 + i * 6 + 1.2 * fps], [0, 1], clamp01));
        const col = items.length <= 2 ? 0 : i % 2, row = items.length <= 2 ? i : Math.floor(i / 2);
        const w = items.length <= 2 ? 920 : 440;
        return (
          <div key={i} style={{ position: "absolute", top: (p.title ? 470 : 390) + row * 300, left: 80 + col * 480, width: w, height: 260, borderRadius: 30,
            background: rgba(T.primaryDeep, 0.55), border: `3px solid ${rgba(T.accent, 0.5)}`, opacity: Math.min(1, k * 2), display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
            <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 96, color: T.accent, lineHeight: 1 }}>{it.prefix ?? ""}{fmt(it.value * k, it.value)}{it.suffix ?? ""}</div>
            <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 34, color: T.text, marginTop: 14, textAlign: "center", padding: "0 20px" }}>{it.label}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

export const MG: Record<string, React.FC<SceneProps>> = {
  mg_bar: MgBars,
  mg_line: MgLine,
  mg_donut: MgDonut,
  mg_compare: MgCompare,
  mg_steps: MgSteps,
  mg_code: MgCode,
  mg_kpi: MgKpi,
};
