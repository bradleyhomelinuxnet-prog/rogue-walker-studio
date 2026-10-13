# The mirror rig: picking footage and timing

## Footage
| Slot | What works | Notes |
|---|---|---|
| Pairs `1…axis-1` | Side-scrolling walks, both characters in profile, horizon low, open sky in the top third | The top third carries captions. Busy skies fight the text. |
| Axis | One walk *toward* camera on a flat, reflective or open ground | It's scaled to about 63 % and reflected, so wide shots read best. Close-ups cut faces in half. |
| Climb or descent shots | Usable in a pair if the place matters more than the camera grammar | Flipping a climb still reads as "coming back". |

**Direction check.** Pull one frame at 2 s and 9 s from each candidate and tile them. Set `"flip": true` on
any pair whose walkers face left on the way up. The down half flips automatically.

**Generated clips often drift into a talking close-up mid-clip.** That's fine under captions. Mouths moving
out of sync with new lines read as "they're talking", not as an error.

## Timing to signature lengths
total frames = 2·P + N·C (fps 24)

| Target | N | C (clip) | P (plate) | Check |
|---|---|---|---|---|
| 276 s (138 × 2) | 19 | 330 | 177 | 6,270 + 354 = 6,624 |
| 138 s | 9 | 344 | 108 | 3,096 + 216 = 3,312 |
| 69 s | 5 | 312 | 48 | 1,560 + 96 = 1,656 |
| 8:31 (511 s) | 33 | 360 | 192 | 11,880 + 384 = 12,264 |

*Plates must be whole frames. When the math lands on a half frame, nudge C by one frame instead.

## Caption safety
- Speech should end by about 0.96 × clip length. The engine fits lines between 0.45 s and the end of the clip.
- A clip carrying a `mirror` line reserves its last quarter for that line.
- Keep each line under about 90 characters, or use `\n` to break it into two caption lines.

## Common failures
| Symptom | Cause | Fix |
|---|---|---|
| End plate clipped by about 1 s | Audio track shorter than video | The engine pads audio to the full length (`apad=whole_dur`). Don't remux with `-shortest`. |
| Two-pass encode segfaults | Frame-count mismatch between passes | Use the capped single pass (crf 24, maxrate 760k). |
| A glyph shows as a box | Font lacks the codepoint | Use plain text in plates, or a font that has it. |
| Mirror caption invisible | `\fscx-100` isn't supported | The engine uses `\fry180`. |
