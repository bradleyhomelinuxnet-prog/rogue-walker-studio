# Rogue Walker Studio

[![validate](https://github.com/bradleyhomelinuxnet-prog/rogue-walker-studio/actions/workflows/validate.yml/badge.svg)](https://github.com/bradleyhomelinuxnet-prog/rogue-walker-studio/actions/workflows/validate.yml)

**Six Claude skills for making finished video from footage you already own, plus working bridges to FilmCraft and ArtCraft.**

Generated clips pile up. Most of them never get cut into anything because captioning, timing, mixing and assembly
are slow. This kit lets Claude do that work: it turns a folder of clips and a script into a captioned, voiced,
loopable reel with exact timing, on your machine, without spending a single generation credit.

| Skill | What it does |
|---|---|
| **walker-reel** | Builds a palindromic "endless walker" reel from existing clips: a mirror rig (walk up, axis, walk back down), a reflected centre shot, a loop-back dissolve, captions with speaker colours, title and end plates, a soft wind bed, a synthesized bell, and optional per-line voice sync. One JSON config, one command, frame-exact output. |
| **walk-clip-captioner** | Captions clips from their *own* dialogue: Whisper transcript, pitch-based speaker ID, burned captions and era chyrons, original audio kept. |
| **house-looks** | Two production-tested caption and plate looks (Ledger Walk, Proof) so a series stays consistent. |
| **filmcraft-mcp** | Connects Claude to [FilmCraft](https://getartcraft.com/apps/filmcraft), the free open-source NLE: MCP setup for Claude Desktop and Claude Code, headless and live-bridge modes, editing recipes, troubleshooting, and a control-channel client for sessions where the MCP tools aren't visible. |
| **artcraft-bridge** | Works with [ArtCraft](https://github.com/storytold/artcraft), the open-source AI image and video IDE. Plan and price generations, drive the live app with computer use (stopping before every paid click), and auto-collect its renders into FilmCraft or a walker reel. |
| **gen-budget-planner** | Prices every generation option first (free cost checks), solves a mix that spends a credit balance to exactly zero, and writes the paste-ready prompt sheet. Never spends without a yes. |

> *The Deposition*, the included example, is a 19-clip, 276-second (138 × 2) reel: nine walks up, a mirrored axis
> on clip 10, the same nine walked back flipped, then the last frame dissolving into the first. Two characters are
> voiced over a wind bed, and the whole reel cost about 7 credits of voice lines and no video credits at all.

---

## Install

**Claude Code (plugin)**
```
/plugin marketplace add bradleyhomelinuxnet-prog/rogue-walker-studio
/plugin install rogue-walker-studio@rogue-walker-studio
```

**Claude app (claude.ai / Desktop): upload skills**
Download the `.skill` files from [`dist/`](dist) (or rebuild them with `scripts/package.sh`) and upload each in
**Settings → Capabilities → Skills**. Tagging `v*` also publishes them as a GitHub Release via `.github/workflows/release.yml`.

**Manual**
Copy any folder in `skills/` into `~/.claude/skills/`.

## Requirements
- **ffmpeg + ffprobe** with libass (any recent build). That's all walker-reel needs.
- **Python 3.8+**, standard library only, except the captioner, which needs `numpy` and `faster-whisper`.
- **FilmCraft 0.6+** for the FilmCraft skill (free; MIT / Apache-2.0).
- Footage, voices and music you own or license.

## Quick start: a walker reel
```
cp skills/walker-reel/templates/reel.example.json my_reel/reel.json
# put clips in my_reel/src/, edit reel.json (pairs, axis, clips, lines)
python3 skills/walker-reel/scripts/walker_reel.py my_reel/reel.json
# → my_reel/my_reel_master.mp4 and my_reel_web.mp4, frame count verified
```
Or just ask Claude: *"Make a walker reel from the clips in src/ using this script."*

## Quick start: FilmCraft
1. Download FilmCraft. Point `skills/filmcraft-mcp/configs/claude_desktop_config.bridge.json` at your `filmcraft-cli`.
2. Merge it into your Claude Desktop config, start FilmCraft with `--control 9876`, and restart Claude Desktop.
3. Ask: *"List FilmCraft commands about razor, then inspect my project."*

## Repo layout
```
.claude-plugin/        plugin + marketplace manifests
skills/<name>/         SKILL.md + scripts/ references/ templates/ configs/
examples/the-deposition/   a full 19-clip reel config + its prompt sheet
scripts/package.sh     builds dist/<skill>.skill zips
scripts/validate.py    checks every skill's frontmatter and that the scripts compile
```

## Setup & support
Free to use. If you want it working on your machine without the fiddling, I offer:
- **Setup session**: installed, connected to FilmCraft and ArtCraft, with a first reel cut from your own clips.
- **Custom look**: your brand's plates, captions and sound bed built into the engine.
- **Done-for-you reels**: send clips and a script, get a finished reel back.

Book through **[Rogue-Ventures-Portfolio.com](https://rogue-ventures-portfolio.com/)**.

## License
Source-available, see [LICENSE](LICENSE). Use it and modify it freely for your own work, and own everything you make.
Redistributing or reselling the kit itself isn't permitted. FilmCraft and ArtCraft are trademarks of the ArtCraft Team,
and this is an independent, unofficial integration.

© 2026 Hollywood Rogue Ventures LLC · 19138 · 83191
