#!/usr/bin/env python3
"""
walker_reel.py — build a palindromic "endless walker" reel from footage you already own.

Zero generation credits: it cuts, mirrors, captions, plates, voices and mixes clips that
already exist on disk. One JSON config drives everything (see templates/reel.example.json).

THE MIRROR RIG (N clips, N odd, axis = (N+1)/2)
  clips 1 .. axis-1      walk "up"    (footage as configured in `pairs`)
  clip  axis             the axis     (front-facing clip + optional delayed reflection)
  clips axis+1 .. N      walk "down"  (clip n reuses pair N+1-n, horizontally flipped)
  clip N's last frames dissolve into clip 1's first frame, so the reel loops.

Usage
  python3 walker_reel.py reel.json                  # build everything
  python3 walker_reel.py reel.json --clips 1 10     # re-render only these clips, then re-assemble
  python3 walker_reel.py reel.json --audio-only     # remix sound (bed + voices) onto the last master

Voices (optional): put one file per spoken line at  <voices_dir>/cNN_i.(mp3|wav)
  NN = clip number, i = 1-based index of the clip's spoken lines (lines marked "mirror" are skipped).
  When every line of a clip has a file, captions time themselves to the voice.

Requires: ffmpeg + ffprobe with libass (any recent build). Python 3.8+. No pip packages.
"""
import argparse, glob, json, math, os, subprocess, sys

# ---------------------------------------------------------------- helpers

def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)

def probe_dur(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)

def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def esc(t):
    return t.replace('\\', '').replace('{', '(').replace('}', ')')

def hex_to_ass(hexrgb, alpha=0):
    """'#RRGGBB' -> ASS &HAABBGGRR"""
    h = hexrgb.lstrip('#')
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f'&H{alpha:02X}{b}{g}{r}'.upper().replace('&H', '&H')

def find_font(candidates):
    for c in candidates:
        if os.path.exists(c):
            return c
    hits = subprocess.run(['fc-match', '-f', '%{file}', candidates[-1] if candidates else 'serif'],
                          capture_output=True, text=True).stdout.strip()
    return hits or None

def atempo_chain(t):
    parts = []
    while t > 2.0:
        parts.append('atempo=2.0'); t /= 2.0
    parts.append(f'atempo={t:.4f}')
    return ','.join(parts)

# ---------------------------------------------------------------- config

DEFAULTS = {
    "fps": 24, "width": 1280, "height": 720,
    "clip_frames": 330, "plate_frames": 177,
    "sources_dir": "src", "voices_dir": "vo", "work_dir": "build",
    "grade": "eq=contrast=1.04:saturation=0.92:brightness=-0.02",
    "fade_in_out": 0.35,
    "loop_back": True,
    "caption_font": "DejaVu Serif", "label_font": "DejaVu Sans Mono",
    "speakers": {},                       # name -> "#RRGGBB" label colour
    "bed": "wind",                        # "wind" | "none" | path to an audio file (looped)
    "bed_lufs": -26, "voice_lufs": -17,
    "bell": "synth",                      # "synth" | "none" | path to a bell/sting audio file
    "axis": {"reflection": True, "delay_frames": 12},
    "output": "walker_reel",
}

def load_cfg(path):
    cfg = dict(DEFAULTS)
    user = json.load(open(path))
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k] = {**cfg[k], **v}
        else:
            cfg[k] = v
    base = os.path.dirname(os.path.abspath(path))
    for k in ('sources_dir', 'voices_dir', 'work_dir'):
        if not os.path.isabs(cfg[k]):
            cfg[k] = os.path.join(base, cfg[k])
    cfg['_base'] = base
    n = len(cfg['clips'])
    if n % 2 == 0:
        sys.exit(f'config error: the mirror rig needs an ODD number of clips (got {n}).')
    cfg['_axis'] = (n + 1) // 2
    os.makedirs(cfg['work_dir'], exist_ok=True)
    return cfg

def src_path(cfg, name):
    p = name if os.path.isabs(name) else os.path.join(cfg['sources_dir'], name)
    if os.path.exists(p):
        return p
    hits = sorted(glob.glob(os.path.join(cfg['sources_dir'], f'*{name}*')))
    if not hits:
        sys.exit(f'source not found: {name} (looked in {cfg["sources_dir"]})')
    return hits[0]

def clip_source(cfg, n):
    """-> (path, start_seconds, hflip) for clip n under the mirror rig."""
    N, axis = len(cfg['clips']), cfg['_axis']
    if n == axis:
        a = cfg['axis']
        return src_path(cfg, a['src']), float(a.get('start', 0.5)), bool(a.get('flip', False))
    k = n if n < axis else N + 1 - n
    p = cfg['pairs'][str(k)]
    flip = bool(p.get('flip', False)) ^ (n > axis)
    return src_path(cfg, p['src']), float(p.get('start', 0.4)), flip

# ---------------------------------------------------------------- voices

def voice_files(cfg, clip):
    spoken = [l for l in clip['lines'] if not l.get('mirror')]
    files = []
    for i in range(1, len(spoken) + 1):
        hit = None
        for ext in ('mp3', 'wav', 'm4a'):
            f = os.path.join(cfg['voices_dir'], f"c{clip['n']:02d}_{i}.{ext}")
            if os.path.exists(f):
                hit = f; break
        if not hit:
            return None
        files.append(hit)
    return files

def vo_schedule(cfg, clip):
    files = voice_files(cfg, clip)
    if not files:
        return None
    durs = [probe_dur(f) for f in files]
    clip_s = cfg['clip_frames'] / cfg['fps']
    has_mirror = any(l.get('mirror') for l in clip['lines'])
    t0, gap = 0.45, 0.35
    win = (clip_s * 0.73) if has_mirror else (clip_s - 0.45)
    need = sum(durs) + gap * (len(durs) - 1)
    tempo = max(1.0, need / (win - t0))
    if tempo > 1.25:
        print(f'  ! clip {clip["n"]}: lines need x{tempo:.2f} speed-up to fit — consider trimming the script', flush=True)
    out, t = [], t0
    for f, d in zip(files, durs):
        dd = d / tempo
        out.append((t, t + dd, tempo, f)); t += dd + gap / tempo
    return out

# ---------------------------------------------------------------- captions (ASS)

def make_ass(cfg, clip, path):
    W, H = cfg['width'], cfg['height']
    dur = cfg['clip_frames'] / cfg['fps']
    cf, lf = cfg['caption_font'], cfg['label_font']
    sc = H / 720.0
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{cf},{int(34*sc)},&H00E6F0F5,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0.5,0,1,2.2,1.2,8,120,120,{int(46*sc)},1
Style: Who,{lf},{int(17*sc)},&H0080C8E8,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,3,0,1,1.4,0.6,8,120,120,{int(24*sc)},1
Style: Era,{lf},{int(18*sc)},&H00B4D8E6,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,2,0,1,1.2,0.6,7,34,34,{int(26*sc)},1
Style: Log,{lf},{int(19*sc)},&H9EC8E0EE,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,1.0,0,2,60,60,{int(40*sc)},1
Style: Ttl,{cf},{int(15*sc)},&H0080A8B8,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,4,0,1,1.0,0.5,9,34,34,{int(28*sc)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev, fad = [], r'{\fad(250,250)}'
    if clip.get('era'):
        ev.append(f"Dialogue: 0,{ass_time(0.2)},{ass_time(dur-0.3)},Era,,0,0,0,,{fad}{esc(clip['era'])}")
    if clip.get('title'):
        ev.append(f"Dialogue: 0,{ass_time(0.2)},{ass_time(dur-0.3)},Ttl,,0,0,0,,{fad}{clip['n']:02d} · {esc(clip['title'])}")
    spoken = [l for l in clip['lines'] if not l.get('mirror')]
    mirror = [l for l in clip['lines'] if l.get('mirror')]
    t0, t1 = 0.5, (dur * 0.73 if mirror else dur - 0.55)
    tot = sum(max(len(l['text']), 30) for l in spoken) or 1
    vs = vo_schedule(cfg, clip)
    t = t0
    for i, l in enumerate(spoken):
        d = (t1 - t0) * max(len(l['text']), 30) / tot
        a, b = t, t + d - 0.15
        if vs:
            a, b = vs[i][0] - 0.1, vs[i][1] + 0.25
        col = cfg['speakers'].get(l['who'])
        tag = fad + (f'{{\\c&H{col[5:7]}{col[3:5]}{col[1:3]}&}}' if col else '')
        ev.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},Who,,0,0,0,,{tag}{esc(l['who'])}")
        ev.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{fad}\\N{esc(l['text']).replace(chr(10), chr(92)+'N')}")
        t += d
    ma, mb = dur * 0.75, dur * 0.90
    for l in mirror:   # an unvoiced line rendered mirror-reversed (\fry180 flips it)
        ev.append(f"Dialogue: 1,{ass_time(ma)},{ass_time(mb)},Who,,0,0,0,,{{\\fad(200,700)}}{esc(l['who'])}  · NO AUDIO")
        ev.append(f"Dialogue: 1,{ass_time(ma)},{ass_time(mb)},Cap,,0,0,0,,{{\\fad(200,700)\\fry180}}\\N{esc(l['text'])}")
    if clip.get('log'):
        ev.append(f"Dialogue: 2,{ass_time(dur*0.29)},{ass_time(dur*0.52)},Log,,0,0,0,,{{\\fad(120,400)}}[ {esc(clip['log'])} ]")
    open(path, 'w').write(hdr + '\n'.join(ev) + '\n')

# ---------------------------------------------------------------- video segments

def render_clip(cfg, clip):
    W, H, FPS, CF = cfg['width'], cfg['height'], cfg['fps'], cfg['clip_frames']
    n, N, axis = clip['n'], len(cfg['clips']), cfg['_axis']
    dur = CF / FPS
    fio = cfg['fade_in_out']
    wd = cfg['work_dir']
    out, ass = os.path.join(wd, f'c{n:02d}.mp4'), os.path.join(wd, f'c{n:02d}.ass')
    make_ass(cfg, clip, ass)
    grade = cfg['grade']
    path, s0, flip = clip_source(cfg, n)
    hf = 'hflip,' if flip else ''
    ins = ['-ss', f'{s0:.3f}', '-t', f'{dur + 0.3:.3f}', '-i', path]
    ass_f = ass.replace('\\', '/').replace(':', '\\:')
    if n == axis and cfg['axis'].get('reflection', True):
        tw = int(round(W * 0.627 / 2) * 2); th = int(round(H * 0.628 / 2) * 2); rh = H - th
        dl = int(cfg['axis'].get('delay_frames', 12))
        fc = (f"[0:v]scale={tw}:{th},setsar=1,fps={FPS},{hf}split[a][b];"
              f"[a]pad={W}:{th}:(ow-iw)/2:0:black[top];"
              f"[b]tpad=start={dl}:start_mode=clone,trim=end_frame={CF},vflip,crop={tw}:{rh}:0:0,"
              f"eq=brightness=-0.08:saturation=0.75,boxblur=1.2,pad={W}:{rh}:(ow-iw)/2:0:black[ref];"
              f"[top][ref]vstack,{grade},ass='{ass_f}',fade=t=in:st=0:d={fio},fade=t=out:st={dur-fio}:d={fio}[v]")
    elif n == N and cfg.get('loop_back', True):
        p1, s1, f1 = clip_source(cfg, 1)
        still = os.path.join(wd, 'first01.png')
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{s1:.3f}', '-i', p1, '-frames:v', '1', still])
        ins += ['-loop', '1', '-t', f'{dur:.3f}', '-i', still]
        fc = (f"[0:v]scale={W}:{H},setsar=1,fps={FPS},{hf}{grade}[m];"
              f"[1:v]scale={W}:{H},setsar=1,{'hflip,' if f1 else ''}{grade},format=yuva420p,"
              f"fade=t=in:st={dur-0.9}:d=0.85:alpha=1[last];"
              f"[m][last]overlay=eof_action=pass,ass='{ass_f}',fade=t=in:st=0:d={fio}[v]")
    else:
        fc = (f"[0:v]scale={W}:{H},setsar=1,fps={FPS},{hf}{grade},ass='{ass_f}',"
              f"fade=t=in:st=0:d={fio},fade=t=out:st={dur-fio}:d={fio}[v]")
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y'] + ins +
        ['-filter_complex', fc, '-map', '[v]', '-an', '-frames:v', str(CF), '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS), out])

def render_plate(cfg, name, spec):
    W, H, FPS, PF = cfg['width'], cfg['height'], cfg['fps'], cfg['plate_frames']
    dur = PF / FPS
    serif = find_font(['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', '/Library/Fonts/Georgia.ttf',
                       'C:/Windows/Fonts/georgia.ttf', 'serif'])
    serif_b = find_font(['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', '/Library/Fonts/Georgia Bold.ttf',
                         'C:/Windows/Fonts/georgiab.ttf', 'serif:bold'])
    lines, sizes = spec['lines'], spec.get('sizes', [22, 54, 20, 18][:len(spec['lines'])])
    sc = H / 720.0
    y = H / 2 - sum(s * sc * 1.6 for s in sizes) / 2
    dt = []
    for i, (txt, s) in enumerate(zip(lines, sizes)):
        tf = os.path.join(cfg['work_dir'], f'{name}_{i}.txt')
        open(tf, 'w', encoding='utf-8').write(txt)
        f = serif_b if s >= 44 else serif
        tfe = tf.replace('\\', '/').replace(':', '\\:')
        fe = f.replace('\\', '/').replace(':', '\\:')
        dt.append(f"drawtext=fontfile='{fe}':textfile='{tfe}':fontsize={int(s*sc)}:fontcolor=0xF0E6D2:"
                  f"x=(w-text_w)/2:y={y:.0f}:alpha='if(lt(t,0.8),t/0.8,if(gt(t,{dur-0.9}),({dur}-t)/0.9,1))'")
        y += s * sc * 1.6
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:r={FPS}:d={dur}',
         '-vf', ','.join(dt), '-an', '-frames:v', str(PF), '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p',
         os.path.join(cfg['work_dir'], f'{name}.mp4')])

def assemble_video(cfg):
    wd = cfg['work_dir']
    names = ['p0'] + [f"c{c['n']:02d}" for c in cfg['clips']] + ['p1']
    open(os.path.join(wd, 'list.txt'), 'w').write(''.join(f"file '{x}.mp4'\n" for x in names))
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy',
         'video_only.mp4'], cwd=wd)

# ---------------------------------------------------------------- sound

def total_seconds(cfg):
    return (2 * cfg['plate_frames'] + len(cfg['clips']) * cfg['clip_frames']) / cfg['fps']

def make_bed(cfg, T, out):
    bed = cfg['bed']
    if bed == 'none':
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=stereo', '-t', f'{T}', out]); return
    if bed == 'wind':   # soft open-air wind: pink noise, no low end, slow gusts, decorrelated L/R
        fc = (f"[0:a]highpass=f=380,highpass=f=380,lowpass=f=2600,volume='0.55+0.30*sin(2*PI*t/11)+0.15*sin(2*PI*t/4.7)':eval=frame[l];"
              f"[1:a]highpass=f=380,highpass=f=380,lowpass=f=2400,volume='0.55+0.30*sin(2*PI*t/13+1.9)+0.15*sin(2*PI*t/5.3)':eval=frame[r];"
              f"[l][r]join=inputs=2:channel_layout=stereo,loudnorm=I={cfg['bed_lufs']}:TP=-6:LRA=6,"
              f"apad=whole_dur={T},atrim=0:{T},afade=t=in:d=3,afade=t=out:st={T-4}:d=4[a]")
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anoisesrc=color=pink:amplitude=0.5:r=48000:d={T+1}:seed=19',
             '-f', 'lavfi', '-i', f'anoisesrc=color=pink:amplitude=0.5:r=48000:d={T+1}:seed=138',
             '-filter_complex', fc, '-map', '[a]', '-ar', '48000', '-ac', '2', out]); return
    p = bed if os.path.isabs(bed) else os.path.join(cfg['_base'], bed)
    run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', '-t', f'{T+1}', '-i', p, '-af',
         f"loudnorm=I={cfg['bed_lufs']}:TP=-6,apad=whole_dur={T},atrim=0:{T},afade=t=in:d=2,afade=t=out:st={T-4}:d=4",
         '-ar', '48000', '-ac', '2', out])

def bell_file(cfg):
    b = cfg['bell']
    if b == 'none':
        return None
    if b == 'synth':   # a struck bell: inharmonic partials with exponential decay (original, royalty-free)
        out = os.path.join(cfg['work_dir'], 'bell_synth.wav')
        if not os.path.exists(out):
            expr = ("0.45*sin(2*PI*220*t)*exp(-t*0.9)+0.30*sin(2*PI*440.8*t)*exp(-t*1.4)"
                    "+0.20*sin(2*PI*594*t)*exp(-t*1.9)+0.14*sin(2*PI*880*t)*exp(-t*2.6)"
                    "+0.10*sin(2*PI*1203*t)*exp(-t*3.5)")
            run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=48000:d=6",
                 '-af', 'aecho=0.8:0.6:420|900:0.25|0.15,afade=t=out:st=4.5:d=1.5,volume=0.8', '-ac', '2', out])
        return out
    return b if os.path.isabs(b) else os.path.join(cfg['_base'], b)

def mix_audio(cfg):
    wd, FPS = cfg['work_dir'], cfg['fps']
    T = total_seconds(cfg)
    bed = os.path.join(wd, 'bed.wav'); make_bed(cfg, T, bed)
    ins, parts, k = ['-i', bed], [], 1
    bell = bell_file(cfg)
    if bell:
        for t in (0.3, T - cfg['plate_frames'] / FPS + 0.1):
            ins += ['-i', bell]; ms = int(t * 1000)
            parts.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.9,adelay={ms}|{ms}[s{k}]"); k += 1
    nb = k - 1
    nv = 0
    for c in cfg['clips']:
        vs = vo_schedule(cfg, c)
        if not vs:
            continue
        off = cfg['plate_frames'] / FPS + (c['n'] - 1) * cfg['clip_frames'] / FPS
        for (a, b, tempo, f) in vs:
            ins += ['-i', f]; ms = int((off + a) * 1000)
            parts.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,{atempo_chain(tempo)},"
                         f"highpass=f=70,adelay={ms}|{ms}[v{k}]"); k += 1; nv += 1
    chain = ';'.join(parts)
    sting = ''.join(f'[s{j}]' for j in range(1, nb + 1))
    voices = ''.join(f'[v{j}]' for j in range(nb + 1, k))
    if nv:
        chain += f";{voices}amix=inputs={nv}:normalize=0,loudnorm=I={cfg['voice_lufs']}:TP=-1.5:LRA=9[vo]"
    mixins = '[0:a]' + sting + ('[vo]' if nv else '')
    m = 1 + nb + (1 if nv else 0)
    chain += (';' if chain else '') + f"{mixins}amix=inputs={m}:normalize=0,apad=whole_dur={T},atrim=0:{T}[a]"
    run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', chain, '-map', '[a]', '-ar', '48000', '-ac', '2',
         os.path.join(wd, 'mix.wav')])
    print(f'  sound: bed={cfg["bed"]}, bell={"yes" if bell else "no"}, voiced lines={nv}', flush=True)

def finalize(cfg):
    wd, T = cfg['work_dir'], total_seconds(cfg)
    base = os.path.join(cfg['_base'], cfg['output'])
    run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(wd, 'video_only.mp4'), '-i', os.path.join(wd, 'mix.wav'),
         '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-t', f'{T}', base + '_master.mp4'])
    # web copy that fits most chat / upload caps (~30 MB for a 4–5 min reel at 720p)
    run(['ffmpeg', '-v', 'error', '-y', '-i', base + '_master.mp4', '-c:v', 'libx264', '-preset', 'medium', '-crf', '24',
         '-maxrate', '760k', '-bufsize', '1520k', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-t', f'{T}',
         base + '_web.mp4'])
    frames = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries',
                             'stream=nb_read_frames', '-of', 'csv=p=0', base + '_web.mp4'], capture_output=True, text=True).stdout.strip()
    want = 2 * cfg['plate_frames'] + len(cfg['clips']) * cfg['clip_frames']
    ok = 'OK' if frames == str(want) else f'MISMATCH (expected {want})'
    print(f'DONE  {base}_web.mp4  {T:.3f}s  frames={frames} {ok}', flush=True)

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('config')
    ap.add_argument('--clips', nargs='*', type=int, help='re-render only these clip numbers')
    ap.add_argument('--audio-only', action='store_true', help='remix sound only (keeps the rendered video)')
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    T = total_seconds(cfg)
    print(f'{cfg.get("title", "walker reel")}: {len(cfg["clips"])} clips, axis {cfg["_axis"]}, {T:.3f}s', flush=True)
    if not a.audio_only:
        render_plate(cfg, 'p0', cfg['open_plate'])
        render_plate(cfg, 'p1', cfg['end_plate'])
        for c in cfg['clips']:
            seg = os.path.join(cfg['work_dir'], f"c{c['n']:02d}.mp4")
            if a.clips and c['n'] not in a.clips and os.path.exists(seg):
                continue
            render_clip(cfg, c); print(f'  clip {c["n"]:02d} rendered', flush=True)
        assemble_video(cfg)
    mix_audio(cfg)
    finalize(cfg)

if __name__ == '__main__':
    main()
