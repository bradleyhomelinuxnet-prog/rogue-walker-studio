# Changelog

## 1.3.9-r1 — 2026-10-13
- Public portfolio release: source-available license (free use, no resale), setup & support offer, CI validate workflow
  with a synthetic walker-reel smoke test.

## 1.3.9 — 2026-10-13
- **artcraft-bridge** (new): ArtCraft integration — plan/price → computer-use on the live app with a stop before every
  paid generate → `artcraft_handoff.py` copies renders into a project and writes a FilmCraft import list. Documents
  that ArtCraft has no MCP/CLI yet and how one could be added.
- artcraft-bridge: documents ArtCraft's data root (`~/Artcraft/downloads` = renders; never touch `credentials/`),
  and the WebView2 masking limit for remote computer use (window screenshots black).

## 1.3.8 — 2026-10-13 (first release)
- **walker-reel**: config-driven palindromic walker reel engine (mirror rig, axis reflection, loop-back dissolve,
  ASS captions with speaker colours, mirror-reversed unsaid line, title/end plates, wind bed, synthesized bell,
  per-line voice sync, frame-exact output + upload-sized web copy).
- **walk-clip-captioner**: caption clips from their own dialogue (faster-whisper + pitch speaker ID + drawtext).
- **house-looks**: Ledger Walk and Proof look specs.
- **filmcraft-mcp**: FilmCraft MCP setup (Claude Desktop / Claude Code, headless + bridge), recipes,
  troubleshooting, and `fc_control.py` control-channel client for sessions without MCP.
- **gen-budget-planner**: price-first credit planning to an exact-zero spend, with a paste-ready prompt sheet.
- Example: *The Deposition* — 19-clip, 276-second reel config.
