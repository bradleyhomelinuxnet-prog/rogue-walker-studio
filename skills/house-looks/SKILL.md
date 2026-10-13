---
name: house-looks
description: Two proven caption-and-plate looks for designed walk films and reels — the "Ledger Walk" look (era plate, speaker-coloured captions, black title plates, bell) and the "Proof" look (rolling year counter, type-on captions, source line, clock bar). Use when someone asks for a video, teaser, reel or walk film "in the house style", or wants consistent plates and captions across a series.
---

# House looks

Two looks that already won approval in production. Use one of them, and don't invent a third unless asked.
Colours and sizes are for 1920×1080, so scale proportionally. Swap the palette for your own brand by editing the
hex values in one place (the walker-reel config's `speakers`, or your template's palette).

## 1. Ledger Walk (the default)
Real walk clips of two characters passing through events, with burned captions, black title plates and a bell.

**On every clip**
- **Era plate**, top-left: the era number (56 bold, `#E8D7B0`), the calendar year (32, `#9EC9F0`), and a cycle line such as
  `CYCLE k · DOCUMENTED / TRANSIT` (23, cream @ 62 %).
- **Event title**, bottom-left (32 bold, white @ 92 %).
- **Speaker label and caption**, centred: dialogue 38 bold white on black @ 45 %, with one label colour per speaker
  (warm `#F0C89E` / ice `#9EC9F0`).

**Optional**
- **Ledger column** on the right: dated entries tick in with a 0.35 s fade, colour-tagged by source.
  Only dated, checkable entries. Never invent dates.
- **Drifting glyph layer**: invented marks (never real scripts), screen-blended at about 0.4.

**Plates**: black, a small grey kicker (22), the title (66 bold cream), a subtitle (24 ice) and a small grey line, fading in over 0.6 s.
A bell on both plates (walker-reel can synthesise an original one).

**Rules**
- Caption text = the script's exact words, timed to word timestamps or to the voice files.
- Speakers come from the script. Pitch is a cross-check only.
- Land on signature lengths. Plates absorb the remainder. If speech is long, speed every clip by one shared factor with
  pitch-preserving `atempo`, and never drop a clip or a line.
- Verify by frame count (frames = seconds × fps). Pin re-encodes with `-r 24 -frames:v N`.

**Engines**: `walker-reel` (new script over footage) and `walk-clip-captioner` (clips' own dialogue).

## 2. Proof (designed frame)
A designed frame over a previz or clip background:
- a rolling year counter (large serif, about 118 px)
- a serif title block in a lane colour
- two-speaker captions typed on word by word
- a "CHECK" source line under any claim
- a clock bar and a station ribbon

Palette: ember and ice on warm obsidian. **15-second clock:** hook 1.9 s, voices 2.4–7.8 and 8.6–13.6, speech done 13.8, exit 14.5.
Build it in Remotion (or any motion engine) from a fill-in sheet → JSON → render.

## Working rules for both
- Hand back MP4s. Don't hand non-technical owners scripts to run.
- Deliver a web copy under about 30 MB for chat or upload caps, and keep the master.
- Run long renders detached and poll. Cap every looped ffmpeg input with `-t`.
- Audio leads video: lock the script and voice first, then cut picture to it.
