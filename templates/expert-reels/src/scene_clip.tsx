// Tək səhnəni (danışansız) ayrıca qısa video kimi render edir — montaj mühərrikində Claude-un hazırladığı B-roll.
// Səhnələr Reel-dəki ilə EYNİ komponentlərdir (kod təkrarlanmır); mövzu/rəng public/edit.json-dakı theme-dən.
// Giriş: --props='{"kind": "<səhnə>", "props": {...}, "dur": 3}'
import React from "react";
import { AbsoluteFill, Composition, getInputProps, registerRoot, useCurrentFrame } from "remotion";
import { BigNumber } from "./kid";
import { RAHIME } from "./rahime";
import { BROLL } from "./broll";
import { CARTOON } from "./cartoon";
import { SKETCH } from "./sketch";
import { PAPER } from "./paper";
import { ILLUSTRATED } from "./illustrations";
import { BLUEPRINT } from "./blueprint";
import { SHEET } from "./sheet";
import { CARDS } from "./cards";
import { ACADEMIC } from "./academic";
import { STUDIO } from "./studio";
import { Backdrop, SCENES } from "./scenes";
import { FPS, useFonts } from "./theme";

type Input = { kind: string; props?: Record<string, any>; dur?: number };
const IN = getInputProps() as Input;

export const REGISTRIES: Record<string, Record<string, React.FC<any>>> = {
  scenes: SCENES, rahime: RAHIME, broll: BROLL, blueprint: BLUEPRINT, sheet: SHEET, cards: CARDS,
  academic: ACADEMIC, studio: STUDIO, cartoon: CARTOON, sketch: SKETCH, paper: PAPER, illustrated: ILLUSTRATED,
};

const find = (kind: string): React.FC<any> | undefined => {
  if (kind === "bg_number") return BigNumber;
  for (const r of Object.values(REGISTRIES)) if (r[kind]) return r[kind];
  return undefined;
};

const Clip: React.FC = () => {
  useFonts();
  const f = useCurrentFrame();
  const Scene = find(IN.kind);
  if (!Scene) throw new Error(`Naməlum səhnə: ${IN.kind}`);
  return (
    <AbsoluteFill>
      <Backdrop p={1} />
      <Scene f={f} p={IN.props ?? {}} startT={0} />
    </AbsoluteFill>
  );
};

registerRoot(() => (
  <Composition id="SceneClip" component={Clip} durationInFrames={Math.max(1, Math.round((IN.dur ?? 3) * FPS))}
    fps={FPS} width={1080} height={1920} />
));
