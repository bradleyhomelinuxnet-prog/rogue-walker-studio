---
name: rogue-ai
description: The Rogue AI director — one pipeline from idea to finished film using ArtCraft for shots and FilmCraft for the cut. Plans beats and dialogue, writes ArtCraft shot sheets with caption-safe framing (the owner clicks Generate), collects renders, then builds a real FilmCraft timeline headless from the shell with dissolves, title, top-center speaker-coloured captions, an audio bed and a loudness-normalised export, and checks its own frames. Use whenever someone wants a flick, reel, short, chapter or episode made from ArtCraft renders, Higgsfield/Kling clips or footage on disk, says "cut this in FilmCraft", "make a flick", "Natori and Rogue", "walker", "Phoenix", "keep making flicks", or wants ArtCraft and FilmCraft used together, even if they don't name either app.
---

# Rogue AI — ArtCraft → FilmCraft director

One skill that runs the whole job: **beats → shots → collect → cut → check → deliver.** ArtCraft makes the pictures,
FilmCraft makes the film, and this skill holds the thread between them. It sits on top of the plugin's other skills
and reuses their parts instead of repeating them.

The big unlock: **FilmCraft's `filmcraft-cli` runs headless from any shell**, so in Claude Code (or any session with
a shell on the PC) you don't need the MCP server to be visible. `scripts/rogue_cut.py` turns one JSON cut sheet into a
saved `.fcproj` plus an exported MP4 in seconds, and every step lands in a project the owner can open and keep editing.

## The house rules (why they exist)
- **Audio leads video.** Lock the words (script, VO lines) before cutting picture. Captions and timing follow the words,
  so changing them later means re-cutting.
- **Captions live in the empty sky, top-center.** Shots are composed with the upper third open so the text never fights
  faces. That's a framing decision made at the shot stage, not a fix at the edit.
- **Never spend credits without a yes.** ArtCraft generations cost real money on the owner's provider accounts. Claude
  prepares everything up to the Generate button; the owner clicks it. Price first, fire one test, then batch.
- **Zero-credit first.** Before proposing new generations, check what footage already exists. A cut is free; a shoot isn't.
- **Look at your own work.** Every build renders check frames. Open them and look before telling anyone it's done.
- **Originals stay put.** Copy renders into a project; export to new files; never overwrite the owner's media.

## Stage 1 — Beats and words
Write the script first: a numbered beat list, each beat with its on-screen caption (1–2 short lines, ≤ ~42 chars each),
the speaker, and a one-line picture idea. For the Natori & Rogue series, Natori carries the evidence and Rogue lands the
cold line; a palindromic structure (axis beat in the middle, the last beat returning to the first frame) is the house
signature. Show the beat sheet and get a nod before any shots are planned, because everything downstream hangs on it.

## Stage 2 — Shots (ArtCraft, or footage you already own)
First ask: **does the footage exist?** Search the owner's folders (`hf_*.mp4`, project `src/`, `~/Artcraft/downloads`)
and existing indexes before writing a single prompt. Only beats with no usable footage need new shots.

For new shots, write an ArtCraft shot sheet. ArtCraft's edge over text-only generators is *control*: image-to-location,
3D/2D compositing, character posing, background removal. Read [references/artcraft-shots.md](references/artcraft-shots.md)
for how to use those controls and the shot-sheet format. Every shot keeps the **top third open sky / clean background**
and repeats the style and character descriptors verbatim.

Getting shots made — pick the route that works in this session:
1. **Owner fires** (always works): hand over the paste-ready sheet.
2. **Computer use on ArtCraft** (watchable): stage the prompt and settings, **stop at Generate**. If the ArtCraft window
   screenshots black (WebView2 masking in remote sessions), stop and use route 1. Details: the `artcraft-bridge` skill.
3. For pricing a mix against a credit balance, use the `gen-budget-planner` skill.

## Stage 3 — Collect
Copy renders into the project's `src/` with sortable names, never moving the originals:
```
python ../artcraft-bridge/scripts/artcraft_handoff.py --from "%USERPROFILE%\Artcraft\downloads" --to my_film/src --since 2026-10-13
```
Never read ArtCraft's `credentials\` or `settings\` folders. Footage from elsewhere (Higgsfield downloads, older reels)
can be copied in directly or referenced by absolute path in the cut sheet.

## Stage 4 — Cut in FilmCraft
Write a cut sheet (copy `templates/cutsheet.example.json`), then:
```
python scripts/rogue_cut.py --which              # confirms which filmcraft-cli (newest installed version wins)
python scripts/rogue_cut.py my_film/cut.json --dry-run   # shows every FilmCraft command, runs nothing
python scripts/rogue_cut.py my_film/cut.json
```
What it builds: new project + sequence at the sheet's size and fps → clips back-to-back on V1, scaled to frame →
cross dissolves and end fades → title (V2) and subtitle (V3) → caption lines (V4/V5, one colour per speaker,
centred, top or bottom) → optional SRT caption track burned in → audio beds on A2+ with gain, clip audio muted if asked →
export at the target loudness (−16 LUFS web default, −1.5 dBTP) → check frames at the title and every caption.

All cut-sheet keys are documented at the top of `scripts/rogue_cut.py`. Timing tips:
- Caption `at`/`dur` are seconds on the **finished timeline**. Read clip lengths from the build log
  (`timeline: N clips … Xs`) or `ffprobe`, and keep each caption inside its own clip.
- Give a caption ~0.5 s after a cut and end it ~0.5 s before the next, so dissolves don't smear it.
- Signature lengths (138 s, 276 s, 19 beats) are hit by trimming clips with `"duration"`, not by stretching speed.
  Dissolves overlap on the cut and don't shorten the timeline, so the sum of the durations *is* the runtime.
  Example: 19 beats at about 7.26 s each gives exactly 138.00 s (3,312 frames at 24 fps).
- Start each clip 2–3 s in (`"in": 3`), because generated clips often settle or morph in their first seconds.
- Short sources (6–7 s Cinema Studio clips) can't fill a 7.5 s slot. Give them a smaller `duration` and spread the rest
  over the longer clips.

**Picking footage by eye** is faster and more accurate than reading truncated prompt indexes. Grab one frame per clip
into a numbered contact sheet (ffmpeg: `-ss 4 … scale=320:180, drawtext` per clip, then `tile=8x5`), look at it,
and match each beat to a frame with **open sky in the top third**. Skip close-ups whose heads reach the top of
frame: the caption will sit on a face.

If a step fails, the error names the FilmCraft command. Check the param shape with
`filmcraft-cli commands <filter>` or `filmcraft-cli describe <id>` (FilmCraft is alpha and ids shift between versions),
fix the script or sheet, and re-run; a re-run rebuilds the project from scratch.

**Beyond the cut sheet** — grading, ducking, multicam, keyframes, 700 commands in all — drive FilmCraft directly:
```
filmcraft-cli --project P.fcproj --save exec <command.id> '{"json":"params"}'
filmcraft-cli --project P.fcproj inspect sequence
filmcraft-cli --project P.fcproj render --seconds 12.5 --out check.png --scale 0.5
```
Each `exec` is its own process, so state like the clip *selection* does not carry over; for select-then-act commands,
put them in one `filmcraft-cli … run -` batch (one `{"id":…,"params":{…}}` per line). If the owner wants to *watch*
the edit live, use the `filmcraft-mcp` skill's bridge mode (`filmcraft --control 9876` + `fc_control.py`).

## Stage 5 — Check, then deliver
1. Open every check frame the build printed. Confirm: title readable, captions inside the frame and not over faces,
   the right speaker colours, no black gaps. Fix the sheet and rebuild if anything's off.
2. Spot-check the export: duration matches the plan, audio present, and loudness is near target
   (`ffmpeg -i out.mp4 -af ebur128 -f null -`).
3. Deliver: the master MP4, a web copy under ~30 MB if it will be sent through chat
   (`ffmpeg -i out.mp4 -vf scale=-2:720 -c:v libx264 -crf 26 -c:a aac web.mp4`), and the `.fcproj` for further editing.
   For a vertical Short, run a second cut sheet at 1080×1920 with the same captions.
4. Tell the owner, in plain words, what was made, where it is, and what's still open (shots waiting on a Generate click,
   beats with no footage yet).

## When things don't line up
- **"filmcraft-cli not found"** → ask where FilmCraft lives, or set `FILMCRAFT_CLI`. Portable builds work fine.
- **Clips missing** → the sheet names the file. Re-run the hand-off, or point the sheet at the real folder.
- **Want ArtCraft driven without clicks** → it has no MCP/CLI yet (check the `artcraft-bridge` skill's notes for
  updates). Don't pretend it does; use the shot sheet.
- **"Access is denied (os error 5)" on save** → a sync client (OneDrive/Dropbox) locked the project for a moment.
  The script retries automatically. If it still fails, build into a non-synced folder and copy the results.
- **Pale caption colours vanishing over bright sky** → the default thin dark outline (`stroke`) handles it. Keep it on.
- **Masters are large** (FilmCraft's default is about 20 Mbps, 350 MB for 138 s). Always make the web copy for sharing.
- **Huge jobs (100+ clips)** → the cut sheet scales, but render time grows with length. Build a 3-clip test sheet first.
