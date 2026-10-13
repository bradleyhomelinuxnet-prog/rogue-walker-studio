# ArtCraft shot sheets

ArtCraft (getartcraft.com, open source) is an AI image/video studio built around **control** rather than prompting
alone. It routes to many models (Seedance 2.5, Nano Banana 2, Seedream, Kling, Veo and more) and adds tools that
text-only generators lack. Use those tools when a shot needs consistency or exact blocking. Use a plain prompt when it doesn't.

## Which control to reach for
| Need | ArtCraft tool | Why it beats a prompt |
|---|---|---|
| Several shots in the same place (the ridge, the plateau, the drowned city) | **Image to Location** | Locks one environment, so props and horizon don't drift between shots |
| Exact staging: who's left, who's right, distance to camera | **Character Posing** | Pose and camera blocking set before render; no "they swapped sides" |
| A hero object in a scene (pyramid, second sun, clock rings) | **Image to 3D Mesh** + **3D Compositing** | Place it with depth and scale, not by begging the prompt |
| Characters over a background you already like | **Background Removal** + **2D Compositing** | Re-use cutouts of Natori/Rogue across many plates |
| Mixed: cutouts + a world + a mesh | **Mixed Assets** canvas | One layout, rendered once |

Then send the composed frame to image-to-video (Seedance 2.5 or similar) for motion.

## Framing rule: the caption band
Every shot keeps the **upper third** empty: open sky, plain wall, dark void. Put the horizon or the characters' heads
below the top third, and keep nothing crossing the top-center. Say it in the prompt *and* enforce it in the
composition (place the horizon low on the canvas). Add a negative: *no text, letters, captions, watermark, logo, numerals*.
Burned captions are added in FilmCraft later, so generated text is always a defect.

## Shot sheet format
One block per shot. The owner pastes; nothing is left to guess.

```
── SHARED (paste above every shot) ──
STYLE: cinematic naturalistic 35mm, muted filmic grade, slow steady dolly, wide.
       Horizon LOW: upper third is open, uninterrupted sky. Nothing crosses top-center.
CAST:  Natori: auburn hair, faint gold throat-glyphs.  Rogue: swept silver hair, white beard, black leather jacket.
       They walk slowly in step across the lower third, left to right, never facing camera.
NEGATIVE: text, letters, captions, subtitles, title cards, watermark, logo, numerals.

── 10 · THE 138 PHOENIX ──  [beat 10 · axis]
ArtCraft: Location = "dark ridge" (reuse from shot 09) · Pose = both halted, facing away, center-low
Model: Seedance 2.5 · i2v · 15s · 16:9 · 1080p · audio off        Cost: (priced in app before firing)
Scene: one slow streak of fire crosses the far LOWER sky with a long ember trail; top sky black and clean.
END ON: the ember hanging low, both still, watching.
Caption (added in FilmCraft): NATORI "The Phoenix runs every 138 years." / ROGUE "The clock already knows your name."
```

Rules for the sheet:
- Repeat STYLE and CAST verbatim. Paraphrasing is how characters drift.
- Write an **END ON** frame for every shot, because the edit needs a clean last frame for the dissolve.
- Note which beats reuse a location or pose from an earlier shot, so the owner builds it once.
- List the cost per shot from ArtCraft's own model settings. Mark one shot **TEST FIRST** and batch the rest only after
  the owner has looked at it.
- Shots that only need an open-sky walking plate can usually reuse existing footage. Say so and skip the generation.

## Where the renders land
Windows: `%USERPROFILE%\Artcraft\downloads\` (finished renders) and `assets\`. Collect them with
`artcraft-bridge/scripts/artcraft_handoff.py`. Never open `credentials\` or `settings\`.
