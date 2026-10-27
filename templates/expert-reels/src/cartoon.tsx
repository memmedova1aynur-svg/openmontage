import React from "react";
import { interpolate, spring, useVideoConfig } from "remotion";
import { FONT, T, clamp01 } from "./theme";

// Flat cartoon world (bright sky, sun, clouds, rolling hills, round trees, kids with white outlines),
// drawn in code for the split-screen panel (1080 x 900). Nothing here is stock or generated.

const W = 1080;
const H = 900;
const GROUND = 700;
const SKIN = "#F5C6A0";
const SKIN_D = "#E7AF86";
const HAIR = "#3B2A24";

// ---------------------------------------------------------------- landscape
export const Landscape: React.FC<{ f: number; children?: React.ReactNode; night?: boolean }> = ({ f, children }) => {
  const sunRot = f * 0.4;
  const cloud = (x0: number, y: number, s: number, speed: number) => {
    const x = ((x0 + f * speed) % (W + 300)) - 150;
    return (
      <g transform={`translate(${x} ${y}) scale(${s})`} fill="#FFFFFF">
        <ellipse cx={0} cy={20} rx={70} ry={30} />
        <circle cx={-30} cy={8} r={30} />
        <circle cx={18} cy={-2} r={40} />
        <circle cx={55} cy={14} r={26} />
      </g>
    );
  };
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#7FD0EA" />
          <stop offset="1" stopColor="#D8F3EE" />
        </linearGradient>
        <radialGradient id="sunGlow">
          <stop offset="0" stopColor="#FFE58A" stopOpacity="0.9" />
          <stop offset="1" stopColor="#FFE58A" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width={W} height={H} fill="url(#sky)" />
      <g transform="translate(170 150)">
        <circle r={150} fill="url(#sunGlow)" />
        <g transform={`rotate(${sunRot})`} stroke="#FFD54F" strokeWidth={6} strokeLinecap="round" opacity={0.85}>
          {Array.from({ length: 12 }, (_, i) => {
            const a = (i * Math.PI) / 6;
            return <line key={i} x1={Math.cos(a) * 82} y1={Math.sin(a) * 82} x2={Math.cos(a) * 110} y2={Math.sin(a) * 110} />;
          })}
        </g>
        <circle r={66} fill="#FFD54F" />
      </g>
      {cloud(380, 110, 1, 0.5)}
      {cloud(780, 190, 0.8, 0.35)}
      {cloud(1100, 90, 0.9, 0.45)}
      <path d={`M0 ${GROUND - 170} Q 260 ${GROUND - 260} 560 ${GROUND - 180} T ${W} ${GROUND - 200} V ${GROUND} H 0 Z`} fill="#A8E2BF" />
      <path d={`M0 ${GROUND - 90} Q 300 ${GROUND - 170} 640 ${GROUND - 110} T ${W} ${GROUND - 120} V ${GROUND} H 0 Z`} fill="#86D3A4" />
      <Tree x={110} s={0.9} />
      <Tree x={990} s={1.05} />
      {[60, 250, 420, 700, 860, 1030].map((x, i) => (
        <Flower key={i} x={x} y={GROUND - 4} c={["#FF6B6B", "#FFD54F", "#FF9ECD"][i % 3]} f={f + i * 7} />
      ))}
      <rect y={GROUND} width={W} height={H - GROUND} fill="#5CBF86" />
      <line x1={0} y1={GROUND} x2={W} y2={GROUND} stroke="#FFFFFF" strokeWidth={4} opacity={0.9} />
      {children}
      {[[-40, 0.9], [300, 0.7], [760, 0.85], [1060, 1]].map(([x, s], i) => (
        <g key={i} transform={`translate(${x} ${H + 20}) scale(${s})`} fill="#4CAF78" opacity={0.95}>
          <circle cx={0} cy={-40} r={70} />
          <circle cx={80} cy={-20} r={60} />
          <circle cx={-70} cy={-10} r={55} />
        </g>
      ))}
    </svg>
  );
};

const Tree: React.FC<{ x: number; s: number }> = ({ x, s }) => (
  <g transform={`translate(${x} ${GROUND}) scale(${s})`}>
    <rect x={-8} y={-170} width={16} height={170} rx={8} fill="#8B5E3C" />
    <circle cx={0} cy={-200} r={72} fill="#4DB878" />
    <circle cx={-22} cy={-224} r={26} fill="#FFFFFF" opacity={0.18} />
  </g>
);

const Flower: React.FC<{ x: number; y: number; c: string; f: number }> = ({ x, y, c, f }) => (
  <g transform={`translate(${x} ${y}) rotate(${Math.sin(f / 18) * 6})`}>
    <line x1={0} y1={0} x2={0} y2={-26} stroke="#3E9E68" strokeWidth={4} />
    <circle cx={0} cy={-32} r={9} fill={c} />
    <circle cx={0} cy={-32} r={3.5} fill="#FFF4C2" />
  </g>
);

// Full 9:16 frame around a 1080 x 900 world: more sky above, more ground below, the world scaled up
// so the kids read on a phone. `top` is where the world box starts.
export const FullFrame: React.FC<{ f: number; children: React.ReactNode }> = ({ f, children }) => {
  const S = 1.12;
  const top = 360;
  return (
    <div style={{ position: "absolute", inset: 0, width: 1080, height: 1920, overflow: "hidden", background: "linear-gradient(180deg, #68C6E7 0%, #7FD0EA 18.75%)" }}>
      <svg viewBox="0 0 1080 1920" width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <rect y={1340} width={1080} height={580} fill="#5CBF86" />
        {[[200, 170, 0.9, 0.4], [760, 300, 1.1, 0.3], [1180, 120, 0.8, 0.5]].map(([x0, y, sc, sp], i) => {
          const x = ((x0 + f * sp) % 1400) - 160;
          return (
            <g key={i} transform={`translate(${x} ${y}) scale(${sc})`} fill="#FFFFFF" opacity={0.95}>
              <ellipse cx={0} cy={20} rx={70} ry={30} />
              <circle cx={-30} cy={8} r={30} />
              <circle cx={18} cy={-2} r={40} />
              <circle cx={55} cy={14} r={26} />
            </g>
          );
        })}
      </svg>
      <div style={{ position: "absolute", top, left: (1080 - 1080 * S) / 2, width: 1080, height: 900, transform: `scale(${S})`, transformOrigin: "0 0" }}>{children}</div>
    </div>
  );
};

// ---------------------------------------------------------------- kid rig
export type Pose = {
  ls: number; le: number; rs: number; re: number; // shoulder / elbow angles (deg, 0 = hanging down, + = towards the kid's right)
  lh: number; lk: number; rh: number; rk: number; // hip / knee
  lean?: number;
  face?: "smile" | "frown" | "scared" | "calm" | "laugh";
  eyes?: "open" | "closed" | "wide";
};
type Look = { shirt: string; pants: string; shoes: string; cap?: string; hair?: "cap" | "pony" | "short"; skirt?: boolean };

const seg = (x: number, y: number, a: number, l: number): [number, number] => [x + Math.sin((a * Math.PI) / 180) * l, y + Math.cos((a * Math.PI) / 180) * l];

const Limb: React.FC<{ pts: [number, number][]; c: string; w: number; tip?: string; tipR?: number }> = ({ pts, c, w, tip, tipR }) => {
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0]} ${p[1]}`).join(" ");
  const end = pts[pts.length - 1];
  return (
    <g>
      <path d={d} stroke="#FFFFFF" strokeWidth={w + 8} strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <path d={d} stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" fill="none" />
      {tip && <circle cx={end[0]} cy={end[1]} r={tipR ?? w * 0.6} fill={tip} stroke="#FFFFFF" strokeWidth={3} />}
    </g>
  );
};

// Kid standing on (0, 0); about 300 units tall.
export const Kid: React.FC<{ pose: Pose; look: Look; x: number; y: number; s?: number; flip?: boolean; rot?: number }> = ({ pose, look, x, y, s = 1, flip, rot = 0 }) => {
  const hip: [number, number] = [0, -130];
  const sh: [number, number] = [0, -228];
  const leg = (h: number, k: number, side: number) => {
    const hp: [number, number] = [hip[0] + side * 14, hip[1]];
    const kn = seg(hp[0], hp[1], h, 64);
    const ft = seg(kn[0], kn[1], h + k, 62);
    return { hp, kn, ft };
  };
  const arm = (a: number, e: number, side: number) => {
    const sp: [number, number] = [sh[0] + side * 30, sh[1] + 6];
    const el = seg(sp[0], sp[1], a, 54);
    const hd = seg(el[0], el[1], a + e, 50);
    return { sp, el, hd };
  };
  const L = leg(pose.lh, pose.lk, -1);
  const R = leg(pose.rh, pose.rk, 1);
  const LA = arm(pose.ls, pose.le, -1);
  const RA = arm(pose.rs, pose.re, 1);
  const face = pose.face ?? "smile";
  const eyes = pose.eyes ?? "open";
  const mouth =
    face === "smile" ? "M-14 -262 Q0 -248 14 -262" : face === "laugh" ? "M-15 -264 Q0 -240 15 -264 Z" : face === "frown" ? "M-13 -254 Q0 -266 13 -254" : face === "scared" ? "M-7 -258 a7 9 0 1 0 14 0 a7 9 0 1 0 -14 0" : "M-11 -258 L11 -258";
  const shoe = (p: { kn: [number, number]; ft: [number, number] }, side: number) => (
    <g>
      <ellipse cx={p.ft[0] + side * 6} cy={p.ft[1]} rx={22} ry={11} fill={look.shoes} stroke="#FFFFFF" strokeWidth={4} />
      <rect x={p.ft[0] + side * 6 - 20} y={p.ft[1] + 4} width={40} height={6} rx={3} fill="#FFFFFF" />
    </g>
  );
  return (
    <g transform={`translate(${x} ${y}) scale(${(flip ? -1 : 1) * s} ${s}) rotate(${(pose.lean ?? 0) + rot})`}>
      <ellipse cx={0} cy={4} rx={60} ry={10} fill="#000" opacity={0.12} />
      {/* back limbs */}
      <Limb pts={[LA.sp, LA.el, LA.hd]} c={SKIN_D} w={20} tip={SKIN_D} tipR={11} />
      <Limb pts={[L.hp, L.kn, L.ft]} c={look.skirt ? SKIN_D : look.pants} w={24} />
      {shoe(L, -1)}
      {/* torso */}
      <path d="M-34 -236 Q-40 -150 -30 -122 L30 -122 Q40 -150 34 -236 Q0 -246 -34 -236 Z" fill={look.shirt} stroke="#FFFFFF" strokeWidth={5} />
      {look.skirt ? (
        <path d="M-32 -132 L32 -132 L46 -92 L-46 -92 Z" fill={look.pants} stroke="#FFFFFF" strokeWidth={4} />
      ) : (
        <rect x={-31} y={-134} width={62} height={26} rx={10} fill={look.pants} stroke="#FFFFFF" strokeWidth={4} />
      )}
      {/* front limbs */}
      <Limb pts={[R.hp, R.kn, R.ft]} c={look.skirt ? SKIN : look.pants} w={24} />
      {shoe(R, 1)}
      <Limb pts={[RA.sp, RA.el]} c={look.shirt} w={22} />
      <Limb pts={[RA.el, RA.hd]} c={SKIN} w={20} tip={SKIN} tipR={11} />
      <Limb pts={[LA.sp, [(LA.sp[0] + LA.el[0]) / 2, (LA.sp[1] + LA.el[1]) / 2]]} c={look.shirt} w={22} />
      {/* head */}
      <rect x={-9} y={-252} width={18} height={20} fill={SKIN_D} />
      <circle cx={0} cy={-272} r={44} fill={SKIN} stroke="#FFFFFF" strokeWidth={5} />
      {look.hair === "pony" ? (
        <g fill={HAIR}>
          <path d="M-44 -276 Q-42 -320 0 -320 Q42 -320 44 -276 Q30 -298 0 -298 Q-28 -298 -44 -276 Z" />
          <ellipse cx={46} cy={-292} rx={14} ry={24} transform="rotate(25 46 -292)" />
          <circle cx={38} cy={-306} r={7} fill="#FF6B9A" />
        </g>
      ) : look.hair === "short" ? (
        <path d="M-44 -272 Q-44 -318 0 -318 Q44 -318 44 -272 Q34 -296 0 -294 Q-30 -296 -44 -272 Z" fill={HAIR} />
      ) : (
        <g>
          <path d="M-46 -282 Q-44 -324 0 -324 Q44 -324 46 -282 Z" fill={look.cap ?? "#E84855"} stroke="#FFFFFF" strokeWidth={4} />
          <path d="M20 -286 Q60 -290 72 -280 Q50 -274 22 -276 Z" fill={look.cap ?? "#E84855"} stroke="#FFFFFF" strokeWidth={3} />
          <circle cx={0} cy={-324} r={6} fill={look.cap ?? "#E84855"} />
        </g>
      )}
      {eyes === "closed" ? (
        <g stroke={HAIR} strokeWidth={4} strokeLinecap="round" fill="none">
          <path d="M-22 -274 q7 6 14 0" />
          <path d="M8 -274 q7 6 14 0" />
        </g>
      ) : (
        <g fill={HAIR}>
          <ellipse cx={-15} cy={-276} rx={eyes === "wide" ? 6 : 4.5} ry={eyes === "wide" ? 8 : 6} />
          <ellipse cx={15} cy={-276} rx={eyes === "wide" ? 6 : 4.5} ry={eyes === "wide" ? 8 : 6} />
          {eyes === "wide" && <path d="M-26 -292 l12 4 M26 -292 l-12 4" stroke={HAIR} strokeWidth={3} strokeLinecap="round" />}
        </g>
      )}
      <path d={mouth} stroke={HAIR} strokeWidth={4} fill={face === "laugh" || face === "scared" ? "#B5413F" : "none"} strokeLinecap="round" />
      {(face === "smile" || face === "laugh") && (
        <g fill="#FF8A8A" opacity={0.5}>
          <circle cx={-26} cy={-258} r={7} />
          <circle cx={26} cy={-258} r={7} />
        </g>
      )}
      {/* front hand (left arm) above the body */}
      <Limb pts={[[(LA.sp[0] + LA.el[0]) / 2, (LA.sp[1] + LA.el[1]) / 2], LA.el]} c={look.shirt} w={22} />
    </g>
  );
};

export const LOOKS: Record<string, Look> = {
  a: { shirt: "#FFC93C", pants: "#3E7CB1", shoes: "#E84855", cap: "#E84855", hair: "cap" },
  b: { shirt: "#2EC4B6", pants: "#9B5DE5", shoes: "#3E7CB1", hair: "pony", skirt: true },
  c: { shirt: "#FF8C69", pants: "#2F4858", shoes: "#FFC93C", hair: "short" },
};

// ---------------------------------------------------------------- props
const SwingSet: React.FC<{ x: number; a: number; children?: React.ReactNode }> = ({ x, a, children }) => (
  <g transform={`translate(${x} 0)`}>
    <path d={`M-150 ${GROUND} L-110 330 L110 330 L150 ${GROUND}`} stroke="#E84855" strokeWidth={14} fill="none" strokeLinejoin="round" />
    <path d={`M-150 ${GROUND} L-110 330 M150 ${GROUND} L110 330`} stroke="#FFFFFF" strokeWidth={3} opacity={0.4} />
    <g transform={`rotate(${a} 0 334)`}>
      <line x1={-42} y1={334} x2={-42} y2={580} stroke="#5B5B5B" strokeWidth={4} />
      <line x1={42} y1={334} x2={42} y2={580} stroke="#5B5B5B" strokeWidth={4} />
      <rect x={-56} y={576} width={112} height={14} rx={7} fill="#8B5E3C" />
      {children}
    </g>
  </g>
);

const Sandbox: React.FC<{ x: number; w: number }> = ({ x, w }) => (
  <g transform={`translate(${x} ${GROUND})`}>
    <path d={`M${-w / 2} -10 Q0 -40 ${w / 2} -10 L${w / 2} 30 L${-w / 2} 30 Z`} fill="#F3D99B" />
    <rect x={-w / 2 - 14} y={-14} width={w + 28} height={18} rx={6} fill="#C98B4F" stroke="#FFFFFF" strokeWidth={3} />
    <path d={`M${w / 2 - 70} -30 l14 -44 h30 l12 44 z`} fill="#4FA3E3" stroke="#FFFFFF" strokeWidth={3} />
  </g>
);

const Speaker: React.FC<{ x: number; f: number }> = ({ x, f }) => {
  const pulse = 1 + 0.06 * Math.abs(Math.sin(f / 3));
  return (
    <g transform={`translate(${x} ${GROUND})`}>
      <g transform={`scale(${pulse}) translate(0 0)`}>
        <rect x={-46} y={-170} width={92} height={170} rx={14} fill="#2F4858" stroke="#FFFFFF" strokeWidth={4} />
        <circle cx={0} cy={-58} r={30} fill="#5B7083" />
        <circle cx={0} cy={-58} r={12} fill="#1E2F3B" />
        <circle cx={0} cy={-130} r={16} fill="#5B7083" />
      </g>
      {[0, 1, 2].map((i) => {
        const k = ((f / 2 + i * 10) % 30) / 30;
        return (
          <g key={i} opacity={1 - k} stroke="#FF6B6B" strokeWidth={5} fill="none" strokeLinecap="round">
            <path d={`M${-60 - k * 90} -150 q -18 50 0 100`} />
            <path d={`M${60 + k * 90} -150 q 18 50 0 100`} />
          </g>
        );
      })}
    </g>
  );
};

// ---------------------------------------------------------------- poses over time
const P = (o: Partial<Pose>): Pose => ({ ls: -10, le: 8, rs: 10, re: -8, lh: 4, lk: 0, rh: -4, rk: 0, face: "smile", ...o });
const walk = (f: number, sp = 6): Partial<Pose> => {
  const a = Math.sin(f / sp) * 26;
  return { lh: a, lk: Math.max(0, -a) * 0.9, rh: -a, rk: Math.max(0, a) * 0.9, ls: -a * 0.8, rs: a * 0.8, le: -20, re: 20 };
};

// ---------------------------------------------------------------- pair scenes
const Tag: React.FC<{ x: number; text: string; k: number; tone?: "a" | "b" }> = ({ x, text, k, tone }) => (
  <g transform={`translate(${x} ${GROUND + 70}) scale(${k})`} opacity={Math.min(1, k * 1.5)}>
    <rect x={text.length > 18 ? -230 : -190} y={-40} width={text.length > 18 ? 460 : 380} height={80} rx={40} fill="#FFFFFF" stroke={tone === "b" ? "#FF8A65" : T.accent} strokeWidth={5} />
    <text x={0} y={14} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={text.length > 18 ? 30 : 38} fill={T.primary}>
      {text}
    </text>
  </g>
);

export const CartoonPair: React.FC<{ f: number; p: Record<string, any>; startT: number }> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const t = startT + f / fps;
  const fb = Math.round((t - p.bAt) * fps);
  const kA = spring({ frame: f, fps, config: { damping: 12, stiffness: 170 } });
  const kB = fb >= 0 ? spring({ frame: fb, fps, config: { damping: 11, stiffness: 180 } }) : 0;
  const scene: string = p.scene;
  let body: React.ReactNode = null;
  if (scene === "swing") {
    const a = Math.sin(f / 9) * 22;
    const shake = Math.sin(fb / 1.6) * 3;
    body = (
      <>
        <SwingSet x={300} a={a}>
          <g transform={`translate(0 ${-kA * 0 + 0})`} opacity={kA}>
            <Kid x={0} y={600} s={0.78} look={LOOKS.a} pose={P({ ls: -170, le: 8, rs: 170, re: -8, lh: -82, lk: 82, rh: -88, rk: 88, face: "laugh" })} />
          </g>
        </SwingSet>
        <SwingSet x={720} a={Math.sin(f / 30) * 3} />
        {kB > 0 && (
          <g opacity={Math.min(1, kB * 1.5)}>
            <Kid x={900 + shake} y={GROUND} s={0.95 * kB} look={LOOKS.b} pose={P({ ls: 150, le: 40, rs: -150, re: -40, lh: 8, rh: -8, lean: 8, face: "scared", eyes: "wide" })} />
            {[0, 1].map((i) => (
              <path key={i} d={`M${990 + i * 22} ${340 + i * 30} q 10 14 0 24 q -10 -10 0 -24 Z`} fill="#7FC8F8" opacity={0.5 + 0.5 * Math.sin(fb / 4 + i)} />
            ))}
          </g>
        )}
        <Tag x={300} text={p.aLabel} k={kA} />
        {kB > 0 && <Tag x={800} text={p.bLabel} k={kB} tone="b" />}
      </>
    );
  } else if (scene === "sand") {
    const dig = Math.sin(f / 5) * 30;
    body = (
      <>
        <Sandbox x={300} w={420} />
        <g opacity={kA}>
          <Kid x={290} y={GROUND - 10} s={0.95} look={LOOKS.a} pose={P({ ls: 40, le: 20, rs: -60 + dig, re: -40, lh: -70, lk: 140, rh: -75, rk: 145, face: "laugh" })} />
          {[0, 1, 2, 3, 4].map((i) => {
            const k = ((f / 2 + i * 6) % 24) / 24;
            return <circle key={i} cx={220 - i * 12 - k * 50} cy={GROUND - 30 - Math.sin(k * Math.PI) * 90} r={7} fill="#E8C27A" opacity={1 - k} />;
          })}
        </g>
        <Sandbox x={810} w={300} />
        {kB > 0 && (
          <g opacity={Math.min(1, kB * 1.5)}>
            <Kid x={820} y={GROUND} s={0.95 * kB} look={LOOKS.c} pose={P({ ls: -155, le: -10, rs: 155, re: 10, lean: -10, face: "frown", lh: 6, rh: -10, rk: 10 })} />
            <g stroke="#E84855" strokeWidth={6} strokeLinecap="round" opacity={0.6 + 0.4 * Math.sin(fb / 3)}>
              <path d="M680 330 l26 26 M706 330 l-26 26" />
            </g>
          </g>
        )}
        <Tag x={300} text={p.aLabel} k={kA} />
        {kB > 0 && <Tag x={800} text={p.bLabel} k={kB} tone="b" />}
      </>
    );
  } else if (scene === "noise") {
    const bob = Math.abs(Math.sin(f / 5)) * 16;
    const away = fb > 0 ? Math.min(140, fb * 2.2) : 0;
    body = (
      <>
        <Speaker x={560} f={f} />
        <g opacity={kA}>
          <Kid x={250} y={GROUND - bob} s={0.95} look={LOOKS.a} pose={P({ ls: -140 - Math.sin(f / 5) * 25, le: -20, rs: 140 + Math.sin(f / 5) * 25, re: 20, lh: 10, rh: -10, face: "laugh" })} />
          {[0, 1].map((i) => {
            const k = ((f / 3 + i * 14) % 28) / 28;
            return (
              <text key={i} x={180 + i * 180} y={400 - k * 120} fontSize={54} fill={T.primary} opacity={1 - k} fontFamily={FONT}>
                ♪
              </text>
            );
          })}
        </g>
        {kB > 0 && (
          <g opacity={Math.min(1, kB * 1.5)}>
            <Kid x={820 + away * 0.5} y={GROUND} s={0.95 * kB} look={LOOKS.b} pose={P({ ...walk(fb, 4), ls: -150, le: -60, rs: 150, re: 60, face: "frown", eyes: "closed", lean: 6 })} />
            {[0, 1, 2].map((i) => (
              <path key={i} d={`M${700 + away * 0.5 - i * 26} ${330 + i * 6} l -14 16 l 14 16 l -14 16`} stroke="#E84855" strokeWidth={5} fill="none" strokeLinecap="round" opacity={0.4 + 0.6 * Math.abs(Math.sin(fb / 3 + i))} />
            ))}
          </g>
        )}
        <Tag x={300} text={p.aLabel} k={kA} />
        {kB > 0 && <Tag x={800} text={p.bLabel} k={kB} tone="b" />}
      </>
    );
  }
  const world = (
    <div style={{ position: "absolute", inset: 0, width: W, height: H }}>
      <Landscape f={f + startT * 30}>{body}</Landscape>
    </div>
  );
  return p.full ? <FullFrame f={f}>{world}</FullFrame> : world;
};

// ---------------------------------------------------------------- senses
const SENSE_ICONS: { label: string; d: string[] }[] = [
  { label: "Görmə", d: ["M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z", "c:12,12,3"] },
  { label: "Eşitmə", d: ["M7 9a5 5 0 1 1 10 0c0 3.5-3.5 4.5-3.5 8a3 3 0 0 1-6 0", "M10 9a2 2 0 1 1 4 0"] },
  { label: "İybilmə", d: ["M12 3c-1 4-4 8-4 12a3 3 0 0 0 3 3", "M12 18a3 3 0 0 0 4-1", "M9 18c-2 0-3-1-3-2"] },
  { label: "Dad", d: ["M4 11c3-3 13-3 16 0-3 6-13 6-16 0z", "M4 11c3 2 13 2 16 0", "M12 13v4"] },
  { label: "Toxunma", d: ["M8 13V5a2 2 0 0 1 4 0v6", "M12 10a2 2 0 0 1 4 0v2", "M16 11a2 2 0 0 1 4 0v4a7 7 0 0 1-7 7h-1a7 7 0 0 1-6-4l-2-4a2 2 0 0 1 3-2l1 2"] },
];
const SENSE_COLORS = ["#4FA3E3", "#9B5DE5", "#FF8C69", "#E84855", "#2EC4B6"];

export const CartoonSenses: React.FC<{ f: number; p: Record<string, any>; startT: number }> = ({ f, p, startT }) => {
  const { fps } = useVideoConfig();
  const t = startT + f / fps;
  const feats: { kind: string; label: string; at: number }[] = p.features ?? [];
  const cur = [...feats].reverse().find((x) => t >= x.at);
  const shrink = feats.length ? interpolate(t, [feats[0].at - 0.2, feats[0].at + 0.35], [1, 0.6], clamp01) : 1;
  const fc = cur ? Math.round((t - cur.at) * fps) : 0;
  const kc = cur ? spring({ frame: fc, fps, config: { damping: 10, stiffness: 150, mass: 0.8 } }) : 0;
  let kid: React.ReactNode = null;
  if (cur?.kind === "balance") {
    const tilt = Math.sin(fc / 9) * 8;
    kid = (
      <g>
        <rect x={340} y={GROUND - 40} width={400} height={36} rx={18} fill="#C98B4F" stroke="#FFFFFF" strokeWidth={4} />
        <Kid x={540} y={GROUND - 40} s={1.05 * kc} rot={tilt} look={LOOKS.a} pose={P({ ls: -92, le: -6, rs: 92, re: 6, lh: 0, rh: -40, rk: 60, face: "smile" })} />
      </g>
    );
  } else if (cur?.kind === "body") {
    const j = (Math.sin(fc / 5) + 1) / 2;
    kid = (
      <g>
        <Kid x={540} y={GROUND - j * 24} s={0.92 * kc} look={LOOKS.c} pose={P({ ls: -30 - j * 130, le: 0, rs: 30 + j * 130, re: 0, lh: 6 + j * 22, rh: -6 - j * 22, face: "laugh" })} />
        {[0, 1].map((i) => (
          <path key={i} d={i ? "M720 330 a160 160 0 0 1 0 240" : "M360 330 a160 160 0 0 0 0 240"} stroke="#FFFFFF" strokeWidth={6} strokeDasharray="4 16" strokeLinecap="round" fill="none" opacity={0.9} />
        ))}
      </g>
    );
  } else if (cur?.kind === "inner") {
    const beat = 1 + 0.18 * Math.max(0, Math.sin(fc / 4)) ** 4;
    kid = (
      <g>
        <Kid x={540} y={GROUND} s={1.05 * kc} look={LOOKS.b} pose={P({ ls: -30, le: -80, rs: 30, re: 80, face: "calm", eyes: "closed" })} />
        <g transform={`translate(540 ${GROUND - 170 * 1.05}) scale(${beat * kc * 1.2})`}>
          <path d="M0 22 C-34 0 -26 -26 -12 -26 C-5 -26 0 -18 0 -18 C0 -18 5 -26 12 -26 C26 -26 34 0 0 22 Z" fill="#E84855" stroke="#FFFFFF" strokeWidth={4} />
        </g>
        {[0, 1, 2].map((i) => {
          const k = ((fc / 3 + i * 10) % 30) / 30;
          return <circle key={i} cx={540} cy={GROUND - 150} r={40 + k * 150} fill="none" stroke="#FFFFFF" strokeWidth={5} opacity={(1 - k) * 0.9} />;
        })}
      </g>
    );
  }
  const world = (
    <div style={{ position: "absolute", inset: 0, width: W, height: H }}>
      <Landscape f={f + startT * 30}>{kid}</Landscape>
      <div style={{ position: "absolute", top: 40, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 20, transform: `scale(${shrink})`, transformOrigin: "50% 0%" }}>
        {SENSE_ICONS.map((s, i) => {
          const at = (p.times ?? [])[i] ?? startT + i * 0.15;
          const k = spring({ frame: Math.round((t - at) * fps), fps, config: { damping: 10, stiffness: 210, mass: 0.6 } });
          const draw = interpolate(t - at, [0.05, 0.45], [0, 1], clamp01);
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: t >= at ? 1 : 0, transform: `scale(${k}) translateY(${(1 - k) * 30}px)` }}>
              <div style={{ width: 160, height: 160, borderRadius: 80, background: "#FFFFFF", boxShadow: "0 10px 26px rgba(0,0,0,0.15)", border: `7px solid ${SENSE_COLORS[i]}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width={90} height={90} viewBox="0 0 24 24" fill="none" stroke={SENSE_COLORS[i]} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                  {s.d.map((d, j) => {
                    const c = { key: j, pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - draw };
                    if (d.startsWith("c:")) {
                      const [cx, cy, r] = d.slice(2).split(",").map(Number);
                      return <circle {...c} cx={cx} cy={cy} r={r} />;
                    }
                    return <path {...c} d={d} />;
                  })}
                </svg>
              </div>
              <div style={{ marginTop: 10, padding: "4px 14px", borderRadius: 16, background: "rgba(255,255,255,0.9)", fontFamily: FONT, fontWeight: 800, fontSize: 30, color: T.primary }}>{s.label}</div>
            </div>
          );
        })}
      </div>
      {cur && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 190, display: "flex", justifyContent: "center" }}>
          <div style={{ padding: "14px 40px", borderRadius: 50, background: "#FFFFFF", border: `6px solid ${T.accent}`, boxShadow: "0 12px 30px rgba(0,0,0,0.18)", fontFamily: FONT, fontWeight: 900, fontSize: 54, color: T.primary, transform: `scale(${kc})` }}>
            {cur.label}
          </div>
        </div>
      )}
    </div>
  );
  return p.full ? <FullFrame f={f}>{world}</FullFrame> : world;
};

export const CARTOON: Record<string, React.FC<{ f: number; p: Record<string, any>; startT: number }>> = {
  "cartoon-pair": CartoonPair,
  "cartoon-senses": CartoonSenses,
};

