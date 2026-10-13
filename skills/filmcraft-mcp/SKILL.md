---
name: filmcraft-mcp
description: Connect Claude to FilmCraft (ArtCraft's free open-source NLE) and drive real edits — import, timeline, trims, transitions, grade, mix, captions, export — over its MCP server, its JSON control channel, or the CLI. Use when someone wants Claude to edit in FilmCraft, set up the FilmCraft MCP server in Claude Desktop or Claude Code, run FilmCraft headless for batch renders, or troubleshoot why the FilmCraft tools don't appear.
---

# FilmCraft × Claude (MCP / control channel / CLI)

FilmCraft is a Premiere-style non-linear editor written in Rust, with its own codecs and no FFmpeg. It's free,
dual MIT / Apache-2.0, from the ArtCraft team. **Every action in the app is a command** (650+), and the same
commands are reachable from four front ends: the UI, `filmcraft-cli`, a JSON-lines control channel, and an
**MCP server**. This skill wires Claude to them. It's an unofficial integration guide, not affiliated with ArtCraft.

> Status: FilmCraft is alpha (v0.6.x). Save often. Every edit is undoable with `edit.undo`.

## Pick the route (decide this first)
| You are in… | Route | Why |
|---|---|---|
| **Claude Desktop** chat on the same PC | **MCP** (headless or bridge), registered in `claude_desktop_config.json` | Native tools: `command_run`, `sequence_inspect`, … |
| **Claude Code** in a terminal on the PC | **MCP** via `claude mcp add` or the repo's `.mcp.json` | Same tools, scriptable |
| A **cloud / remote** session linked to the PC (no FilmCraft tools visible) | **Control channel** via `scripts/fc_control.py` run *on the PC*, or **computer use** on the live app | A desktop app's MCP config only serves that app's own local chats. It doesn't cross into a cloud session. |
| Unattended batch render | **CLI**: `filmcraft-cli --project p.fcproj export out.mp4` | No window, waits for the job |

If someone asks "do you see the FilmCraft tools?" and you don't: say so plainly, explain the row above, and offer
the control-channel or CLI route. Don't keep retrying.

## Setup
Full steps for Windows, macOS and Linux are in [references/setup.md](references/setup.md). The short version:
1. Get the binaries: the release package (portable or installer) from FilmCraft's GitHub releases or getartcraft.com,
   or build with `cargo build --release -p filmcraft-cli -p filmcraft` (Rust ≥ 1.95).
2. Register the server, using an absolute path to `filmcraft-cli`:
   - headless: `["mcp", "--demo"]` or `["mcp", "--project", "/abs/p.fcproj"]`
   - bridge (drive the live window): start the app with `filmcraft --control 9876`, then `["mcp", "--bridge", "127.0.0.1:9876"]`
   Ready-made configs are in `configs/`. The Windows launcher is `scripts/START_FilmCraft_Bridge.bat`, and macOS/Linux use `scripts/start_bridge.sh`.
3. Fully quit and reopen Claude Desktop, then approve the server.
4. Test: "list FilmCraft commands matching 'razor'" should call `command_list`.

## MCP tools
| Tool | Mode | Use |
|---|---|---|
| `command_list` | both | discover command ids (`filter`, `enabled_only`) |
| `command_run` / `command_batch` | both | run `{id, params}`. Edits are undoable. |
| `project_inspect` | both | bins, items, ids, durations, active sequence |
| `sequence_inspect` | both | tracks, clips, effects, transitions, markers, playhead |
| `media_import` | both | absolute paths, one per line |
| `render_frame` / `render_preview` | both | PNG of the program frame at `seconds`. **Check your work with this.** |
| `doc_inspect` | both | document state |
| `ui_inspect`, `ui_elements`, `ui_click`, `ui_drag`, `ui_key`, `ui_type`, `ui_screenshot`, `ui_control` | bridge | drive the window like a person |

Resources: `filmcraft://document`, `filmcraft://commands`.

## How to edit well with it
1. **Inspect before acting.** Run `project_inspect` and `sequence_inspect`, then act on ids, never on guesses.
2. **Discover, don't assume.** Command ids evolve between versions. Run `command_list` with a filter (`timeline`, `trim`,
   `lumetri`, `mixer`, `caption`, `export`) and read the params before calling. Known-stable examples:
   `sequence.addEdit`, `timeline.razor`, `effects.apply` `{effect}`, `effects.setParam`, `playhead.set`,
   `export.queue.add`, `edit.undo`, `file.newBin` `{name}`.
3. **Time** can be given as `seconds`, `frame` or `timecode` (internally ticks at 254,016,000,000 per second).
4. **Verify visually** after each structural change with `render_frame` at the cut points.
5. **Export:** use `export.queue.add` (preset, path, `start=true`, `wait=true`), or the CLI for a headless render.
6. **Save:** in headless mode use `--save` / `--save-as` on the CLI, or the file commands in-session.

Recipes (walker-reel assembly in FilmCraft, caption import, a ducked music bed, a batch export) are in
[references/recipes.md](references/recipes.md). Troubleshooting is in [references/troubleshooting.md](references/troubleshooting.md).

## Guardrails
- The control channel listens on **127.0.0.1 only**. Never expose it on a network interface.
- Bridge-mode UI tools click real buttons. Confirm before anything destructive (delete, overwrite on export).
- Media paths must be absolute. Keep the user's originals untouched and export to a new file.
