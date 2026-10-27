import React from "react";
import { continueRender, delayRender, staticFile } from "remotion";
import edit from "../public/edit.json";

// ---------------------------------------------------------------- edit spec
// public/edit.json is produced by scripts/build_edit.py from a per-video spec.

export type Theme = {
  primary: string; // card / backdrop base (the expert's dark brand tone)
  primaryDeep: string; // backdrop gradient end
  accent: string; // highlight colour (active word, labels, bars)
  accentSoft: string; // secondary tiles
  text: string; // text on primary
  onAccent: string; // text on accent
  cardAlpha: number; // overlay card opacity
  emphasis?: string; // **highlighted** words; defaults to accent (set it when accent is close to text)
  light?: boolean; // pale backdrops: captions over cutaways turn dark instead of white + stroke
};

export type Word = { w: string; s: number; e: number };
export type Page = { start: number; end: number; words: Word[] };
export type ZoomKey = { t: number; s: number; k: "cut" | "push" | "punch" };
export type Pill = {
  id: string;
  kind: "pill" | "hook" | "cta" | "pop" | "icon" | "title" | "end" | "counter" | "strip" | "note" | "spark" | "ticket" | "marker" | "callcard" | "flash";
  label: string | null;
  pos?: "t" | "tl" | "tr" | "l" | "r"; // "pop" keyword position around the speaker
  top?: number; // pop: centred line at this y instead of pos (stack several pops as rows)
  strike?: number; // pop: time (s) at which a line crosses the text out
  side?: "l" | "r"; // pop with top: pin to the left / right edge instead of centring
  small?: boolean; // pop: compact chip (lists beside the speaker)
  hand?: boolean; // pop: handwritten (Caveat) line, drawn without a card
  size?: number; // type pop: explicit font size (keeps a list on one line per item)
  ink?: boolean; // boxless type pop in the brand colour with a light halo (for pale walls)
  icon?: string; // icon chip: name from ICONS (src/icons.tsx), drawn in with a stroke animation
  sub?: string; // icon chip: small second line
  badge?: string; // icon chip: small number / tag on the circle
  plate?: boolean; // icon chip: shown inside the caption plate, replacing the captions while it is on
  parts: [string, number][];
  in: number;
  out: number;
};
export type Panel = { kind: string; at: number; props: Record<string, any> };
export type Cutaway = {
  id: string;
  kind: "pip" | "full" | "comment" | "split" | "scene";
  in: number;
  out: number;
  panels?: Panel[];
  props?: Record<string, any>;
};
export type Style = {
  captions: "stroke" | "box" | "chip" | "plate" | "paper" | "frame" | "lower" | "marker" | "solo"; // plate: fixed light panel (also hides burned-in text / a problem area)
  pills: "top-card" | "side-tag";
  backdrop: "dots" | "grid" | "orbs" | "diagonal";
  pipShape: "circle" | "rounded";
  pipCorner: "br" | "bl";
  pops?: "dark" | "light" | "type"; // keyword pops: brand-dark card (default), white card with a marker, or boxless large type (M02)
};
export type Pip = { focus: [number, number]; radius: number; scale: number };
export type Edit = {
  duration: number;
  video?: string; // footage file in public/, default base.mp4 (e.g. base_blur.mp4)
  plate?: { y: number; h: number; x: number };
  split?: { top: number; shift: number }; // "split" cutaways: panel height and how far the speaker slides down
  retro?: { in: number; out: number }; // greyed, grainy "quoted" opening (pairs with a megaphone voice)
  videoDur?: number; // footage length; frames past it hold the last picture (end card tails)
  tabs?: { in: number; out: number; text: string; cta?: boolean }[]; // label tabs riding on the plate's top edge // "plate" captions: panel rect (y, height, side margin)
  pillTop?: number; // y of keyword cards; lower it when the speaker sits high in frame (Instagram top bar ends ~220)
  theme: Theme;
  style: Style;
  pip: Pip;
  pages: Page[];
  zoom: ZoomKey[];
  overlays: Pill[];
  cutaways: Cutaway[];
  sfx: { t: number; src: string; vol: number }[];
};

export const E = edit as unknown as Edit;
export const T = E.theme;
export const EMPH = T.emphasis ?? T.accent;
export const FPS = 30;
export const FONT = "Montserrat";
export const FONT_HAND = "Caveat"; // handwritten accents; covers ə ğ ı ş ç ö ü (checked)

export const rgba = (hex: string, a: number) => {
  const n = parseInt(hex.replace("#", ""), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

export const clamp01 = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ---------------------------------------------------------------- fonts
// Montserrat latin + latin-ext: latin-ext carries Azerbaijani ə, ğ, ş, ı, ç, ö, ü.
const LATIN =
  "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD";
const LATIN_EXT =
  "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF";

const makeFaces = () => [
  ...[300, 400, 500, 600, 700, 800, 900].flatMap((w) => [
    new FontFace(FONT, `url(${staticFile(`fonts/montserrat-latin-${w}-normal.woff2`)})`, {
      weight: String(w),
      unicodeRange: LATIN,
    }),
    new FontFace(FONT, `url(${staticFile(`fonts/montserrat-latin-ext-${w}-normal.woff2`)})`, {
      weight: String(w),
      unicodeRange: LATIN_EXT,
    }),
  ]),
  ...[400, 700].flatMap((w) => [
    new FontFace(FONT_HAND, `url(${staticFile(`fonts/caveat-latin-${w}-normal.woff2`)})`, { weight: String(w), unicodeRange: LATIN }),
    new FontFace(FONT_HAND, `url(${staticFile(`fonts/caveat-latin-ext-${w}-normal.woff2`)})`, { weight: String(w), unicodeRange: LATIN_EXT }),
  ]),
];

export const useFonts = () => {
  const [handle] = React.useState(() => delayRender("fonts", { timeoutInMilliseconds: 120000 }));
  React.useEffect(() => {
    Promise.all(makeFaces().map((f) => f.load()))
      .then((loaded) => loaded.forEach((f) => document.fonts.add(f)))
      .catch((e) => console.error(e))
      .finally(() => continueRender(handle));
  }, [handle]);
};
