import { cancelRender, continueRender, delayRender } from "remotion";
import manropeLatin from "../fonts/manrope-latin.woff2";
import manropeExt from "../fonts/manrope-latin-ext.woff2";
import interLatin from "../fonts/inter-latin.woff2";
import interExt from "../fonts/inter-latin-ext.woff2";

/** Bundled Manrope (display) + Inter (body), latin + latin-ext (ə Ə ğ ş ç ö ü İ ı). No network at render. */
const LATIN =
  "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD";
const EXT =
  "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF";

let done = false;
export const loadPikmentFonts = () => {
  if (done || typeof FontFace === "undefined") return;
  done = true;
  const defs: [string, string, string, string][] = [
    ["Manrope", manropeLatin, LATIN, "200 800"],
    ["Manrope", manropeExt, EXT, "200 800"],
    ["Inter", interLatin, LATIN, "100 900"],
    ["Inter", interExt, EXT, "100 900"],
  ];
  for (const [family, url, range, weight] of defs) {
    queueMicrotask(() => {
      const h = delayRender(`font ${family}`);
      const face = new FontFace(family, `url(${url}) format('woff2')`, { weight, style: "normal", unicodeRange: range });
      face
        .load()
        .then(() => {
          document.fonts.add(face);
          continueRender(h);
        })
        .catch((e) => cancelRender(new Error(`font ${family} failed: ${e}`)));
    });
  }
};
