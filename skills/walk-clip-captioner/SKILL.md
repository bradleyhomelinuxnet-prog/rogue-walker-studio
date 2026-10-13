---
name: walk-clip-captioner
description: Caption AI-generated dialogue clips from their OWN audio — transcribe, identify the two speakers by pitch, and burn frame-accurate captions, speaker labels and era chyrons without muting the original track. Use when clips already contain lip-synced dialogue and need captions that match the mouths.
---

# Walk Clip Captioner

Takes a folder of short generated clips (typically 15 s) that already contain spoken dialogue, and returns
the same clips with burned captions, speaker labels and chyrons. The original audio stays intact.
`scripts/caption_clips.py` does all of it. Use **walker-reel** instead when you're putting a *new* script over
footage.

## The core rule
**Transcribe. Never estimate timing from the generation prompt.** Prompts that "put speech in the middle third"
don't. On a measured clip speech ran 3.18–11.68 s. Prompt-derived timings drift visibly against the mouths.

## Pipeline
1. **Transcribe**: `pip install faster-whisper`, then `WhisperModel('base.en', device='cpu', compute_type='int8')`,
   `vad_filter=True`, `beam_size=1`. That's about 6 s of compute per 15 s clip on 2 CPUs, so run big batches detached and poll.
2. **Speaker by pitch.** Per segment: mono 16 kHz, frame 1024 / hop 256, skip RMS < 0.01, autocorrelate, peak lag
   in 70–300 Hz with normalised correlation ≥ 0.3, median F0 over voiced frames (minimum 3). Split at a
   threshold between the two voices (135 Hz separated a warm alto from a deep baritone in the reference set).
   **Validate on one clip whose script you know, and check the batch is bimodal before rendering.** If you have
   the script, take speakers from it and use pitch only as a cross-check.
3. **Caption text.** Use the script's exact words timed to Whisper's word timestamps when a script exists.
   Whisper alone mishears names.
4. **Render.** In at `start − 0.15`, out at `end + 0.30`, clamped to clip length − 0.05. Drop segments under 0.35 s.
   Wrap at 46 characters, two lines maximum. Write every string to its own file and use `drawtext=textfile=`,
   because apostrophes and commas break inline filter strings. Escape commas inside `enable=between(t\,A\,B)`.
5. **Encode** an exact slot: `-frames:v 360 -r 24 -t 15`, `libx264 -crf 19 -pix_fmt yuv420p`, audio
   `loudnorm=I=-16:TP=-1.5:LRA=11` with 0.3 s in and 0.4 s out fades. Always pass `-nostdin` inside shell loops.
6. **Assemble** with concat `-c copy` from a list file in the working directory. Verify by frame count, not container duration.

## Layout (1920×1080; scale proportionally)
| element | position | size | colour |
|---|---|---|---|
| era number | x 70, y 66 | 56 bold | warm cream `#E8D7B0` |
| calendar year | x 74, under era | 32 | ice `#9EC9F0` |
| cycle / multiple | x 74, +42 | 23 | cream @ 62 % |
| event title | x 70, y h−96 | 32 bold | white @ 92 % |
| speaker label | centred above box | 23 | speaker A `#F0C89E`, speaker B `#9EC9F0` |
| dialogue | centred, y h−150 (h−178 wrapped) | 38 bold | white on black @ 45 %, border 15 |

All text gets `shadowcolor=black@0.85:shadowx=2:shadowy=2` minimum.

## Running it
```
python3 scripts/caption_clips.py clips_dir out_dir --threshold 135 --names "SPEAKER_A,SPEAKER_B" [--chyrons chyrons.json]
```
`chyrons.json` maps a filename stem to `{"era": "...", "year": "...", "cycle": "...", "title": "..."}`.
