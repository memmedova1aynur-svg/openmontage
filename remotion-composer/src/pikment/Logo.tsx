import React from "react";
import { LOGO_BASE_PATHS, LOGO_GRADIENT_PATH, LOGO_GRADIENT_STOPS, LOGO_VIEWBOX } from "./logoPaths";

/**
 * Official Pikment logo, geometry untouched (from pikment.az/logo-on-light.svg).
 * reveal: 0..1 left-to-right wipe; shift: slides the original gradient (blue→violet→orange)
 * across the mark without recolouring it; ink: colour of the base letters.
 */
export const PikmentLogo: React.FC<{
  width: number;
  reveal?: number;
  shift?: number;
  ink?: string;
  id?: string;
}> = ({ width, reveal = 1, shift = 0, ink = "#000000", id = "pk" }) => {
  const [x, y, w, h] = LOGO_VIEWBOX.split(" ").map(Number);
  const gx1 = x + shift * w;
  const gx2 = x + w + shift * w;
  const clipW = Math.max(reveal, 0) * (w + 8);
  return (
    <svg viewBox={LOGO_VIEWBOX} width={width} height={(width * h) / w} style={{ display: "block", overflow: "visible" }}>
      <defs>
        <linearGradient id={`${id}-g`} gradientUnits="userSpaceOnUse" x1={gx1} y1={638.21} x2={gx2} y2={638.21} spreadMethod="reflect">
          {LOGO_GRADIENT_STOPS.map(([o, c], i) => (
            <stop key={i} offset={o} stopColor={c} />
          ))}
        </linearGradient>
        <clipPath id={`${id}-c`}>
          <rect x={x - 4} y={y - 20} width={clipW} height={h + 40} />
        </clipPath>
      </defs>
      <g clipPath={`url(#${id}-c)`}>
        {LOGO_BASE_PATHS.map((d, i) => (
          <path key={i} d={d} fill={ink} fillRule="nonzero" />
        ))}
        <path d={LOGO_GRADIENT_PATH} fill={`url(#${id}-g)`} fillRule="nonzero" />
      </g>
    </svg>
  );
};
