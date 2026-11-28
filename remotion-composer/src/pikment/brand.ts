/** Pikment brand tokens — verified against pikment.az CSS and the official logo SVG. */
export const BRAND = {
  violet: "#4524F5",
  violet2: "#6d4aff", // site --accent
  violet3: "#7845F5",
  lavender: "#AD60EF",
  blue: "#3460F5",
  sky: "#21A0FF",
  orange: "#FF951F", // accent ONLY (logo's last letter)
  bg: "#F4F2FC",
  surface: "#FFFFFF",
  surface2: "#EFEEFB",
  line: "#E7E5F8",
  ink: "#171428",
  inkSoft: "#6B6A85",
  deep: "#2E2854",
  dark: "#15132B",
} as const;

export const GRADIENT = `linear-gradient(120deg, ${BRAND.violet} 0%, ${BRAND.violet3} 45%, ${BRAND.blue} 100%)`;
export const DISPLAY = "'Manrope', 'Inter', sans-serif";
export const BODY = "'Inter', 'Manrope', sans-serif";

export const W = 1080;
export const H = 1920;
export const FPS = 30;
/** Instagram Reels safe area (px): keep text between SAFE_TOP and H - SAFE_BOTTOM. */
export const SAFE_TOP = 250;
export const SAFE_BOTTOM = 420;
