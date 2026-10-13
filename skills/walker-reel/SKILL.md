---
name: walker-reel
description: Build a palindromic "endless walker" reel — two characters walking through a sequence of events, captioned, plated, optionally voiced — from video clips you already own, with zero generation credits. Use when someone wants a walker reel, a mirrored/palindromic clip sequence, a captioned dialogue reel from existing footage, or to re-voice / re-score / re-cut one.
---

# Walker Reel

Turns a folder of existing clips plus a script into a finished, loopable reel: a title plate,
N captioned clips arranged on a **mirror rig**, an end plate, a clean sound bed, and (optionally)
the dialogue voiced and synced. One JSON config drives it; `scripts/walker_reel.py` renders it with
ffmpeg alone. Nothing is generated, so it costs no credits on any platform.

## When to use
- "Make a walker reel / endless walker from my clips."
- "Cut these clips into a palindrome / mirrored sequence."
- "Put this script over my existing footage with captions."
- "Swap the music for something quieter", "voice the dialogue", "re-time the captions to the voices".

## The mirror rig (why it reads as one walk)
With N clips (N must be odd) and axis = (N+1)/2:
- clips `1 … axis-1` walk **up** (left→right), each using the footage in `pairs[k]`
- clip `axis` is the **centre**: a front-facing walk, scaled into the upper frame with a
  half-beat-late, darkened reflection below (the "mirror plain")
- clips `axis+1 … N` walk **back down**: clip `n` reuses pair `N+1-n`, **horizontally flipped**
- clip N's last 0.9 s dissolves into clip 1's first frame, so the reel loops

So you only need `(N-1)/2` side-scrolling walk clips plus one front-facing clip. Every pair reads as the
same place, walked back the other way, and the structure becomes the story. Read
[references/rig.md](references/rig.md) for picking footage and timing to signature lengths.

## Workflow
1. **Gather footage.** Put clips in the config's `sources_dir` (default `src/`). Prefer side-scroll walks for
   pairs and one walk-toward-camera for the axis. A contact sheet (one frame at 2 s and 9 s per clip)
   is the fastest way to check walking direction; set `"flip": true` on any pair facing the wrong way.
2. **Write the config.** Start from [templates/reel.example.json](templates/reel.example.json), or the full
   19-clip example in `examples/the-deposition/reel.json`. Per clip: `title`, `era` (top-left plate),
   optional `log` (a mono "collar log" flash), and `lines` (`who`, `text`; `"mirror": true` = an unvoiced line
   printed mirror-reversed, used for a final unsaid line).
3. **Pick the length.** `clip_frames` and `plate_frames` set it exactly:
   total frames = 2 × plate_frames + N × clip_frames. Example: 19 × 330 + 2 × 177 = 6,624 frames = 276.000 s @ 24.
4. **Render.** `python3 scripts/walker_reel.py reel.json`. It prints
   `DONE … frames=… OK` and writes `<output>_master.mp4` plus a `<output>_web.mp4` sized for upload caps.
5. **Check before sharing:** frame count OK, a contact sheet across the reel, and integrated loudness about −16 to −18 LUFS.
   Re-render only what changed with `--clips 3 17`, or the sound alone with `--audio-only`.

## Sound
- `"bed": "wind"` (default): soft open-air wind, pink noise high-passed at 380 Hz, slow
  decorrelated gusts, about −26 LUFS. It has **no low end**, so there's nothing to roar or hum.
- `"bed": "none"`, or a path to your own licensed audio (looped and loudness-normalised).
- `"bell": "synth"` (default) synthesises an original struck-bell sting for both plates. Set `"none"` or give a path.
- Never ship footage's original generated dialogue under new captions. The engine drops clip audio entirely.

## Voices (optional, the only step that can cost money)
Put one audio file per spoken line at `vo/cNN_i.mp3` (NN = clip, i = 1-based spoken-line index).
When a clip's files are all present, its captions re-time to the voice and the lines are laid at their
exact reel times. Any TTS works (ElevenLabs, a Higgsfield voice preset, a local model, a real actor).
- **Always price it first** and get an explicit yes before generating. Run a one-clip test before the batch.
- Spell numbers out in the TTS text ("twenty-nine twenty-nine B.C.") so engines don't truncate or misread them;
  keep numerals in the caption text.
- If a line needs more than about 1.25× speed-up to fit, the engine warns you. Trim the script; don't squash the actor.

## Guardrails
- Footage, voices and music must be the user's own or licensed. This tool doesn't clear rights.
- Don't spend generation credits on any platform without an explicit, per-spend yes.
- Deliver the web copy and keep the master. Large masters may exceed chat or upload caps (about 30 MB).
