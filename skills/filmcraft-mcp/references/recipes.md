# FilmCraft recipes

Run `command_list` with the shown filter first. Ids can shift between alpha releases, so treat the names below as
*what to look for*, confirm each one, then call it.

## A. Assemble a walker reel in FilmCraft (instead of ffmpeg)
Use this when the owner wants an editable timeline, not just an MP4.
1. Render the plates and per-clip captioned segments with `walker-reel` (`build/c01.mp4 …`, `p0.mp4`, `p1.mp4`, `mix.wav`).
2. `media_import`: the absolute paths in reel order (p0, c01…cN, p1) plus `mix.wav`.
3. `project_inspect` → note the item ids. Place each on V1 end-to-end (filter `timeline` / `place` / `insert`;
   the README shows `timeline.place`). Place `mix.wav` on A1 at 0.
4. `sequence_inspect` → confirm the clip count and that the total duration equals the reel frames.
5. `render_frame` at each plate and at the axis clip, and look at them.
6. Export: `export.queue.add` with an H.264 preset, `start=true`, `wait=true`.

## B. Captions from SRT, burned in
1. Filter `caption`: import the SRT onto a caption track (Subtitle format).
2. Style it in the Text panel or with the caption style commands.
3. Export with captions burned (export settings, or the export command's caption option).

## C. Ducked music bed under dialogue
1. Music on A2, dialogue on A1.
2. Filter `essentialSound`: tag A1 Dialogue and A2 Music, then enable ducking on the music.
3. Check the meters. Aim for an integrated −16 LUFS for web and a true peak of −1.5 dBTP (use the loudness meter or `mixer.*`).

## D. Grade a whole sequence consistently
1. Filter `lumetri`: apply Lumetri to an adjustment layer (or each clip), then set `curve_luma`, contrast and saturation.
2. `effects.setParam` example: `{"clip": <id>, "effect": "lumetri", "param": "curve_luma", "value": [[0,0],[0.25,0.21],[0.75,0.82],[1,1]]}`

## E. Headless batch export (no window)
```
filmcraft-cli --project /abs/p.fcproj export /abs/out.mp4
filmcraft-cli --project /abs/p.fcproj export /abs/out --preset "YouTube 1080p Full HD" --start 0 --end 10
filmcraft-cli export --list-presets prores
```

## F. Razor every N seconds (control channel)
```
for t in 15 30 45; do python3 scripts/fc_control.py exec sequence.addEdit "{\"seconds\": $t}"; done
```
