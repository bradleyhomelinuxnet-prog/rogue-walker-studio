---
name: artcraft-bridge
description: Work with ArtCraft (the open-source desktop IDE for AI image and video generation) from Claude — plan and price generations, drive the app with computer use, and hand its outputs straight into FilmCraft or a walker reel. Use when someone mentions ArtCraft, wants Claude to generate in ArtCraft, or wants ArtCraft renders collected, renamed and assembled.
---

# ArtCraft bridge

**ArtCraft** (github.com/storytold/artcraft) is a free, open-source desktop app (Tauri: Rust + React/Three.js) for AI image
and video creation. It does text-to-image, image editing, image-to-video, image-to-3D, character posing, scene blocking
and compositing, and it drives many providers from one place (Nano Banana, GPT-Image, Seedance, Seedream, Flux, Veo,
Kling, Sora, Grok Imagine, Midjourney, WorldLabs Marble). FilmCraft is the same team's NLE.

**Integration reality (checked October 2026):** ArtCraft has **no MCP server, CLI or local API**. Its `AGENTS.md`
covers contributors, not automation. So Claude reaches it three ways, below. Re-check the repo for `mcp`, `cli` or
`--control` before each project, because this may change. If it ships an agent surface, prefer it and update this skill.

## Route 1: plan and price, the owner fires (always available)
Use **gen-budget-planner**: price the exact model, duration and resolution in ArtCraft's provider settings (or the provider's
own price list), solve the mix, and write a paste-ready prompt sheet sized to ArtCraft's input fields (prompt,
reference images, aspect, duration). Repeat the style sentence and character descriptors verbatim in every prompt.

## Route 2: computer use on the live app (watchable)
**Known limit (Windows):** ArtCraft is a Tauri app whose UI is drawn by Microsoft **WebView2**. Remote/cloud
computer-use sessions mask WebView2 as an unlisted process, so ArtCraft's window screenshots as a **solid black
rectangle** and clicks don't land. If that happens, stop; use Route 1 + Route 3, or run computer use from a chat in
the Claude desktop app on that PC (local sessions may not mask it). Don't keep retrying.

For sessions where the window is visible:
1. Load the computer-use guidance and request access to the **installed** ArtCraft app only. If a portable copy and
   an installed copy both exist, grant the one actually on screen.
2. Screenshot first and read the current panel. Never assume the layout, because ArtCraft is evolving fast.
3. Type prompts, set the model, aspect and duration, and attach references. **Stop before any Generate click that spends
   credits or uses a paid provider account, and get an explicit yes for that spend**, every time.
4. After each render, screenshot the result and save or export it to the output folder.
Never enter passwords, API keys or payment details into ArtCraft on the user's behalf; the owner signs in to providers.

## Route 3: hand-off pipeline (renders → edit, automatic)
`scripts/artcraft_handoff.py` finds new ArtCraft renders, copies them with clean, sortable names into a project's
`src/`, writes a manifest, and writes a FilmCraft import list (absolute paths, one per line):
```
python3 scripts/artcraft_handoff.py --from "<ArtCraft output folder>" --to my_reel/src --since 2026-10-13
python3 scripts/artcraft_handoff.py --discover          # list likely ArtCraft output folders on this machine
```
**Where ArtCraft keeps files (Windows):** `C:\Users\<you>\Artcraft\` holds `downloads\` (finished renders),
`assets\`, plus `credentials\`, `settings\`, `state\`, `temp\`. Point `--from` at `downloads` (and `assets` if needed).
**Never read or copy `credentials\` or `settings\`.** If you need folder access, ask for only those two subfolders.

Then either:
- **walker-reel**: reference the copied files in `reel.json` `pairs` / `axis` and render; or
- **filmcraft-mcp**: `media_import` with the contents of `filmcraft_import.txt`, then assemble on the timeline.

## Guardrails
- Generation spends money on the owner's provider accounts. Price first, one test render, then batch, and only with a yes.
- Originals stay where ArtCraft put them. The hand-off copies, never moves.
- This is an unofficial integration. ArtCraft and FilmCraft are the ArtCraft Team's projects and marks.
- See [references/artcraft-notes.md](references/artcraft-notes.md) for the architecture notes and how a future MCP could hook in.
