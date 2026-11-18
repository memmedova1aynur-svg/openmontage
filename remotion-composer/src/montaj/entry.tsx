// Ayrıca giriş nöqtəsi: mövcud Root.tsx-ə toxunmur. Render: npx remotion render src/montaj/entry.tsx <ID> out.mov --props=...
import React from "react";
import { Composition, registerRoot } from "remotion";
import { TitleReveal, LowerThird, QuestionCard } from "./Motion";
const W = 1080, H = 1920, FPS = 30;
const Root: React.FC = () => (<>
  <Composition id="TitleReveal" component={TitleReveal as any} width={W} height={H} fps={FPS} durationInFrames={90}
    defaultProps={{ lines: ["Hər valideynin", "bilməli olduğu", "3 qayda"], italic: [2] }} />
  <Composition id="LowerThird" component={LowerThird as any} width={W} height={H} fps={FPS} durationInFrames={75}
    defaultProps={{ name: "Ad Soyad", role: "Vəzifə" }} />
  <Composition id="QuestionCard" component={QuestionCard as any} width={W} height={H} fps={FPS} durationInFrames={105}
    defaultProps={{ q: "Uşaq tez-tez ağlayırsa, bu nə deməkdir?" }} />
</>);
registerRoot(Root);
