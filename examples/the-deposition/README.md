# Example: The Deposition (19 clips · 276 s)

A two-hander interrogation walked as a palindrome: clips 1–9 climb from "before Year One" to 1350 AD, clip 10 is
the spherical-mirror axis, and clips 11–19 walk the same nine places back, flipped, ending on clip 1's first frame.

- `reel.json`: the full config (all 19 tapes of dialogue, era plates, collar-log flashes, the mirror-reversed last line).
  Source clip names are placeholders. Drop your own nine side-scroll walks and one front-facing walk into `src/`
  and rename them to match.
- `prompt-sheet_openart.txt`: a gen-budget-planner sheet that would shoot fresh footage for all 19 tapes on a
  2,950-credit balance, spent to exactly zero.

Build it: `python3 ../../skills/walker-reel/scripts/walker_reel.py reel.json`
Voice it: put `vo/c01_1.mp3 …` (one file per spoken line) beside `reel.json` and run again. Captions re-time to the
voices and the lines are mixed over the wind. (`--clips 3 17` re-renders only those clips. `--audio-only` remixes sound only.)
