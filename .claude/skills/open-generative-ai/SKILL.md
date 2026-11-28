---
name: open-generative-ai
description: Work with the Open-Generative-AI repo (Anil-matcha/Open-Generative-AI) — a self-hosted Next.js/Electron AI image, video, audio and lip-sync studio that calls 600+ models through the muapi.ai API. Use when the user asks to run, modify, extend or add models/studios in that repo, or mentions Open Generative AI, muapi, Nano/Cinema studio.
---

# Open Generative AI

Open-source (MIT) generative media studio. Next.js app with 14 studios (Image, Video, Audio, AI Clipping, Vibe Motion, Lip Sync, Cinema, Marketing, Workflows, Agents, Design Agent, Apps, MCP & CLI). Models run through the hosted **muapi.ai** API; the user's muapi API key is required for real generations.

## Cost reality (read first)
- Cloud generation through muapi.ai **spends paid credits**. The app is free; the models it calls are not.
- Truly free paths: (a) desktop app **Local Models** (sd.cpp for SD/SDXL/Z-Image, Wan2GP for Wan/LTX/Hunyuan video) which needs a local GPU and is desktop-only; (b) OpenMontage's own free tools (Remotion/HyperFrames/ffmpeg, Piper TTS, faster-whisper, free stock via Pexels/Pixabay keys, `earshot` SFX).
- The cloud sandbox has no GPU (4 CPU, 15 GB), so local video models cannot run there. Use it for editing/composition, not generation.
- Run `scripts/zero_budget_setup.sh` in OpenMontage to install the free local tools.

## Location
- Cloned at `/home/user/anil-matcha/open-generative-ai` (read-only shallow clone via git proxy).
- If missing: `GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/Anil-matcha/open-generative-ai /home/user/anil-matcha/open-generative-ai`
- Pushing or PRs need `add_repo` with `access: "push"` (clone lands at `/home/user/open-generative-ai`).

## Layout
- `app/` — Next.js routes (`agents`, `api`, `assistant`, `studio`, `workflow`, `zh`)
- `src/components/` — studio UI components (e.g. `ImageStudio.js`, `McpCliStudio.js`)
- `src/lib/muapi.js`, `src/lib/models.js` — API client (auth, submit, poll) and model/endpoint definitions
- `packages/studio`, `Vibe-Workflow`, `Open-AI-Design-Agent`, `Open-Poe-AI` — workspace sub-packages (some are git submodules)
- `models_dump.json` — model catalog; `messages/` — i18n strings (en, zh)
- `project_knowledge.md` — architecture notes (read before big changes)

## Commands
- `npm run setup` — init submodules, install, build packages (first time)
- `npm run dev` / `build` / `start` — Next.js
- `npm test` (`node --test`), `npm run lint`
- `npm run build:packages` — rebuild workflow, agent, design, studio packages

## Conventions
1. Read `project_knowledge.md` and the target component before editing.
2. New model: add it to `src/lib/models.js` (and `models_dump.json` if used), with endpoint and input schema; keep existing shape.
3. UI strings go through `messages/<locale>/*.json`; update `en` and `zh` together.
4. Never hardcode or log the muapi API key; it is stored client-side after the user enters it.
5. Generation calls cost credits: announce model and endpoint and get approval before running paid calls.
6. Run `npm test` and `npm run lint` before reporting done.
