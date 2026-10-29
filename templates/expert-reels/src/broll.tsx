import React from "react";
import { OffthreadVideo, Sequence, staticFile } from "remotion";
import { E } from "./theme";

// "broll": a real stock clip while the speaker's voice continues. Clips live in public/broll.
//   layout "full"  (default) - a 9:16 clip fills the frame with a slow push-in
//   layout "split" - the speaker stays in the top half, the clip (any aspect) fills the bottom half
//   p.src = file in public/, p.from = start offset in the clip (s), p.push = push-in over the shot,
//   p.grade = CSS filter, p.speakerY / p.speakerX / p.speakerS = how the speaker sits in the top half
type SceneProps = { f: number; p: Record<string, any>; startT: number };
const FPSX = 30;
const GRADE = "saturate(1.05) sepia(0.12) contrast(1.03)";

const Clip: React.FC<{ p: Record<string, any>; f: number; w: number; h: number }> = ({ p, f, w, h }) => {
  const dur = (p.dur ?? 3) * FPSX;
  const s = 1 + ((p.push ?? 1.06) - 1) * Math.min(1, Math.max(0, f / dur));
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, transform: `scale(${s})`, transformOrigin: `50% ${p.originY ?? 45}%`, filter: p.grade ?? GRADE }}>
        <OffthreadVideo src={staticFile(p.src)} startFrom={Math.round((p.from ?? 0) * FPSX)} muted style={{ width: w, height: h, objectFit: "cover" }} />
      </div>
    </div>
  );
};

const Broll: React.FC<SceneProps> = ({ f, p, startT }) => {
  const start = Math.round(startT * FPSX);
  if (p.layout === "top") {
    // the clip keeps its own shape (16:9 = 608 px tall) across the top; the speaker fills the rest
    const H = p.clipH ?? 608;
    return (
      <div style={{ position: "absolute", inset: 0, background: "#F7E6D0" }}>
        <div style={{ position: "absolute", left: 0, top: H, width: 1080, height: 1920 - H, overflow: "hidden" }}>
          <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 1920, transform: `translate(${p.speakerX ?? (E.frame?.x ?? 0)}px, ${-(p.speakerY ?? 560)}px) scale(${p.speakerS ?? 1.0})`, transformOrigin: "50% 0%" }}>
            <OffthreadVideo src={staticFile(E.video ?? "base.mp4")} muted style={{ width: 1080, height: 1920 }} />
          </div>
        </div>
        <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: H, overflow: "hidden" }}>
          <Sequence from={start} layout="none">
            <Clip p={p} f={f} w={1080} h={H} />
          </Sequence>
        </div>
        <div style={{ position: "absolute", left: 0, right: 0, top: H - 4, height: 8, background: "#F7E6D0" }} />
      </div>
    );
  }
  if (p.layout === "split") {
    const s = p.speakerS ?? 1.0;
    return (
      <div style={{ position: "absolute", inset: 0, background: "#F7E6D0" }}>
        {/* top: the speaker, same footage and timing as the main video */}
        <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 952, overflow: "hidden" }}>
          <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 1920, transform: `translate(${p.speakerX ?? (E.frame?.x ?? 0)}px, ${-(p.speakerY ?? 330)}px) scale(${s})`, transformOrigin: "50% 0%" }}>
            <OffthreadVideo src={staticFile(E.video ?? "base.mp4")} muted style={{ width: 1080, height: 1920 }} />
          </div>
        </div>
        {/* bottom: the clip */}
        <div style={{ position: "absolute", left: 0, top: 968, width: 1080, height: 952, overflow: "hidden" }}>
          <Sequence from={start} layout="none">
            <Clip p={p} f={f} w={1080} h={952} />
          </Sequence>
        </div>
      </div>
    );
  }
  return (
    <div style={{ position: "absolute", inset: 0, background: "#000" }}>
      <Sequence from={start} layout="none">
        <Clip p={p} f={f} w={1080} h={1920} />
      </Sequence>
    </div>
  );
};

export const BROLL: Record<string, React.FC<SceneProps>> = { broll: Broll };
