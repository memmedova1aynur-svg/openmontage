import React from "react";
import { Img, staticFile } from "remotion";
import { BRAND, BODY } from "./brand";

/**
 * Photoreal-style device mockups built in CSS 3D. Screens show ONLY real artwork passed in.
 */

/** MacBook-style laptop. sw = screen width in px; scrollCss = site scroll in site CSS px (image is 1440 css px wide). */
export const LaptopPro: React.FC<{ sw?: number; src: string; scrollCss?: number; rotY?: number; rotX?: number; glare?: number; bloom?: number }> = ({ sw = 900, src, scrollCss = 0, rotY = -14, rotX = 4, glare = 0.3, bloom = 1 }) => {
  const sh = Math.round(sw * 0.625);
  const b = 15;
  const k = sw / 1440;
  return (
    <div style={{ width: sw + b * 2 + 120, perspective: 2800, perspectiveOrigin: "50% 40%" }}>
      <div style={{ transformStyle: "preserve-3d", transform: `rotateX(${rotX}deg) rotateY(${rotY}deg)`, paddingLeft: 60 }}>
        {/* lid */}
        <div style={{ position: "relative", width: sw + b * 2, height: sh + b * 2, borderRadius: 26, background: "linear-gradient(160deg,#cfd0d8 0%,#8c8d98 30%,#b9bac4 60%,#7d7e89 100%)", padding: 2.5, boxShadow: `0 90px 140px rgba(44,30,120,${0.30 * bloom}), 0 30px 60px rgba(23,20,40,0.22), 0 0 0 1px rgba(255,255,255,0.35) inset` }}>
          <div style={{ width: "100%", height: "100%", borderRadius: 24, background: "#050507", padding: b - 2.5, boxSizing: "border-box", position: "relative" }}>
            <div style={{ width: sw, height: sh, borderRadius: 9, overflow: "hidden", position: "relative", background: BRAND.dark }}>
              <Img src={staticFile(src)} style={{ position: "absolute", left: 0, top: 0, width: sw, height: "auto", transform: `translateY(${-scrollCss * k}px)` }} />
              <div style={{ position: "absolute", inset: 0, background: `linear-gradient(112deg, rgba(255,255,255,${glare * 0.55}) 0%, rgba(255,255,255,0) 34%, rgba(255,255,255,0) 70%, rgba(255,255,255,${glare * 0.12}) 100%)` }} />
            </div>
            <div style={{ position: "absolute", top: 0, left: "50%", width: 150, height: 22, marginLeft: -75, background: "#050507", borderRadius: "0 0 14px 14px" }}>
              <div style={{ position: "absolute", top: 7, left: "50%", width: 8, height: 8, marginLeft: -4, borderRadius: 8, background: "radial-gradient(circle at 35% 35%, #3a4a7a, #0a0a12)" }} />
            </div>
          </div>
        </div>
        {/* base */}
        <div style={{ position: "relative", width: sw + b * 2 + 120, marginLeft: -60, height: 20, borderRadius: "2px 2px 50px 50px / 2px 2px 26px 26px", background: "linear-gradient(180deg,#e4e4ea 0%,#b8b9c3 40%,#8f909c 100%)", boxShadow: "0 28px 50px rgba(44,30,120,0.28), 0 2px 0 rgba(255,255,255,0.5) inset" }}>
          <div style={{ position: "absolute", top: 0, left: "50%", width: 190, height: 9, marginLeft: -95, borderRadius: "0 0 12px 12px", background: "linear-gradient(180deg,#9b9ca8,#c9cad3)" }} />
        </div>
        <div style={{ width: sw * 0.92, height: 40, margin: "-4px auto 0", borderRadius: "50%", background: "radial-gradient(ellipse, rgba(44,30,120,0.35), rgba(44,30,120,0) 70%)", filter: "blur(10px)" }} />
      </div>
    </div>
  );
};

const StatusBar: React.FC<{ w: number }> = ({ w }) => (
  <div style={{ position: "absolute", top: 0, left: 0, width: w, height: 58, zIndex: 4, fontFamily: BODY, color: BRAND.ink }}>
    <div style={{ position: "absolute", left: w * 0.1, top: 19, fontWeight: 700, fontSize: 17, letterSpacing: -0.3 }}>9:41</div>
    <svg style={{ position: "absolute", right: w * 0.09, top: 21 }} width="68" height="14" viewBox="0 0 68 14" fill={BRAND.ink}>
      <rect x="0" y="9" width="3.4" height="5" rx="1" /><rect x="5" y="6" width="3.4" height="8" rx="1" /><rect x="10" y="3" width="3.4" height="11" rx="1" /><rect x="15" y="0" width="3.4" height="14" rx="1" />
      <path d="M31 3.2c2.6 0 5 1 6.8 2.7l-1.3 1.4A7.6 7.6 0 0 0 31 5.2c-2 0-3.9.8-5.4 2.1l-1.3-1.4A10.2 10.2 0 0 1 31 3.2zm0 4c1.4 0 2.8.5 3.8 1.5l-1.4 1.4a3.6 3.6 0 0 0-4.8 0l-1.4-1.4A5.6 5.6 0 0 1 31 7.2zm0 3.6l1.8 1.9H29.2z" />
      <rect x="43" y="1" width="21" height="11" rx="3.4" fill="none" stroke={BRAND.ink} strokeOpacity="0.4" /><rect x="44.8" y="2.8" width="15" height="7.4" rx="2" /><rect x="65.2" y="4.6" width="1.8" height="3.8" rx="0.9" fillOpacity="0.4" />
    </svg>
  </div>
);

/** Titanium-frame smartphone. Screen is exactly the real app's aspect ratio (643:1194). */
export const PhonePro: React.FC<{ sw?: number; children: React.ReactNode; rotY?: number; rotX?: number; glare?: number; bloom?: number }> = ({ sw = 440, children, rotY = 0, rotX = 0, glare = 0.3, bloom = 1 }) => {
  const sh = Math.round(sw * (1194 / 643));
  const bz = 11, edge = 7;
  const R = sw * 0.17;
  const btn = (side: "l" | "r", top: number, h: number): React.CSSProperties => ({ position: "absolute", [side === "l" ? "left" : "right"]: -4, top, width: 5, height: h, borderRadius: 3, background: "linear-gradient(90deg,#4a4a54,#9b9aa6 50%,#53525d)", boxShadow: "0 0 0 0.5px rgba(0,0,0,0.5)" });
  return (
    <div style={{ width: sw + (bz + edge) * 2, perspective: 2600 }}>
      <div style={{ position: "relative", width: sw + (bz + edge) * 2, height: sh + (bz + edge) * 2, borderRadius: R + bz + edge, transform: `rotateX(${rotX}deg) rotateY(${rotY}deg)`, background: "linear-gradient(145deg,#aeadb9 0%,#4a4953 16%,#8d8c98 38%,#34343c 60%,#9b9aa6 82%,#55545f 100%)", padding: edge, boxSizing: "border-box", boxShadow: `0 90px 150px rgba(44,30,120,${0.36 * bloom}), 0 28px 60px rgba(23,20,40,0.26), 0 0 0 1px rgba(255,255,255,0.28) inset` }}>
        <div style={btn("l", 150, 40)} /><div style={btn("l", 215, 74)} /><div style={btn("l", 305, 74)} /><div style={btn("r", 250, 112)} />
        <div style={{ width: "100%", height: "100%", borderRadius: R + bz, background: "#040406", padding: bz, boxSizing: "border-box" }}>
          <div style={{ position: "relative", width: sw, height: sh, borderRadius: R, overflow: "hidden", background: BRAND.bg }}>
            {children}
            <StatusBar w={sw} />
            <div style={{ position: "absolute", top: 14, left: "50%", width: sw * 0.29, height: 32, marginLeft: -sw * 0.145, borderRadius: 20, background: "#030305", zIndex: 6 }}>
              <div style={{ position: "absolute", right: 11, top: 10, width: 11, height: 11, borderRadius: 11, background: "radial-gradient(circle at 35% 35%, #2c3a63, #07070c)" }} />
            </div>
            <div style={{ position: "absolute", bottom: 9, left: "50%", width: sw * 0.3, height: 5, marginLeft: -sw * 0.15, borderRadius: 5, background: BRAND.ink, opacity: 0.8, zIndex: 6 }} />
            <div style={{ position: "absolute", inset: 0, zIndex: 7, pointerEvents: "none", background: `linear-gradient(118deg, rgba(255,255,255,${glare * 0.55}) 0%, rgba(255,255,255,0) 30%, rgba(255,255,255,0) 72%, rgba(255,255,255,${glare * 0.12}) 100%)` }} />
          </div>
        </div>
      </div>
    </div>
  );
};
