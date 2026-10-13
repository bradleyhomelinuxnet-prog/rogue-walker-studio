#!/usr/bin/env python3
"""
caption_clips.py — burn captions onto clips from their OWN dialogue (audio kept).

  python3 caption_clips.py CLIPS_DIR OUT_DIR [--threshold 135] [--names "A,B"]
                           [--chyrons chyrons.json] [--seconds 15] [--fps 24]

Steps per clip: faster-whisper transcript -> pitch-based speaker (>= threshold Hz = first name)
-> drawtext captions + speaker label + optional chyron -> exact-length encode.
A transcript cache (OUT_DIR/transcripts.json) makes re-runs instant.

Requires: ffmpeg/ffprobe, Python 3.8+, numpy, faster-whisper  (pip install numpy faster-whisper)
"""
import argparse, glob, json, os, subprocess, textwrap

def pcm(path, start, end, sr=16000):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{start:.3f}', '-to', f'{end:.3f}', '-i', path,
                          '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def median_f0(x, sr=16000, lo=70, hi=300):
    import numpy as np
    f0s = []
    for i in range(0, max(0, len(x) - 1024), 256):
        fr = x[i:i + 1024]
        if np.sqrt(np.mean(fr ** 2)) < 0.01:
            continue
        fr = fr - fr.mean()
        ac = np.correlate(fr, fr, 'full')[1023:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        a, b = int(sr / hi), int(sr / lo)
        lag = a + int(np.argmax(ac[a:b]))
        if ac[lag] >= 0.3:
            f0s.append(sr / lag)
    return float(np.median(f0s)) if len(f0s) >= 3 else None

def transcribe(paths, cache):
    data = json.load(open(cache)) if os.path.exists(cache) else {}
    todo = [p for p in paths if os.path.basename(p) not in data]
    if todo:
        from faster_whisper import WhisperModel
        model = WhisperModel('base.en', device='cpu', compute_type='int8')
        for p in todo:
            segs, _ = model.transcribe(p, vad_filter=True, beam_size=1)
            data[os.path.basename(p)] = [{'start': s.start, 'end': s.end, 'text': s.text.strip()} for s in segs]
            json.dump(data, open(cache, 'w'), indent=1)
            print('transcribed', os.path.basename(p), flush=True)
    return data

def typo(t):
    return t.replace("'", '’').replace('...', '…').replace(' - ', ' — ')

def ff(p):
    return p.replace('\\', '/').replace(':', '\\:')

def render(path, out, segs, names, thr, chy, secs, fps, tmp):
    from_h = lambda h: h  # noqa
    W = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width',
                            '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip() or 1920)
    sc = W / 1920.0
    shadow = 'shadowcolor=black@0.85:shadowx=2:shadowy=2'
    filt, k = [], 0
    def tf(text):
        nonlocal k
        f = os.path.join(tmp, f't{k}.txt'); k += 1
        open(f, 'w', encoding='utf-8').write(text)
        return ff(f)
    if chy:
        for key, y, size, col in (('era', 66, 56, '0xE8D7B0'), ('year', 128, 32, '0x9EC9F0'), ('cycle', 170, 23, '0xE8D7B0@0.62')):
            if chy.get(key):
                filt.append(f"drawtext=textfile='{tf(chy[key])}':x={int(70*sc)}:y={int(y*sc)}:fontsize={int(size*sc)}:fontcolor={col}:{shadow}")
        if chy.get('title'):
            filt.append(f"drawtext=textfile='{tf(chy['title'])}':x={int(70*sc)}:y=h-{int(96*sc)}:fontsize={int(32*sc)}:fontcolor=white@0.92:{shadow}")
    cols = {names[0]: '0xF0C89E@0.85', names[1]: '0x9EC9F0@0.85'}
    for s in segs:
        if s['end'] - s['start'] < 0.35:
            continue
        a, b = max(0, s['start'] - 0.15), min(secs - 0.05, s['end'] + 0.30)
        f0 = median_f0(pcm(path, s['start'], s['end']))
        who = names[0] if (f0 or thr) >= thr else names[1]
        lines = textwrap.wrap(typo(s['text']), 46)[:2]
        y = f"h-{int((178 if len(lines) > 1 else 150) * sc)}"
        en = f"enable='between(t\\,{a:.2f}\\,{b:.2f})'"
        filt.append(f"drawtext=textfile='{tf(chr(10).join(lines))}':x=(w-text_w)/2:y={y}:fontsize={int(38*sc)}:fontcolor=white:"
                    f"box=1:boxcolor=black@0.45:boxborderw={int(15*sc)}:line_spacing={int(8*sc)}:{shadow}:{en}")
        filt.append(f"drawtext=textfile='{tf(who)}':x=(w-text_w)/2:y={y}-{int(44*sc)}:fontsize={int(23*sc)}:fontcolor={cols[who]}:{shadow}:{en}")
    vf = ','.join(filt) or 'null'
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', path, '-vf', vf,
                    '-af', f'loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.3,afade=t=out:st={secs-0.4}:d=0.4',
                    '-frames:v', str(int(secs * fps)), '-r', str(fps), '-t', str(secs),
                    '-c:v', 'libx264', '-crf', '19', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '160k', out], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clips'); ap.add_argument('out')
    ap.add_argument('--threshold', type=float, default=135.0)
    ap.add_argument('--names', default='SPEAKER_A,SPEAKER_B', help='higher voice first, then lower voice')
    ap.add_argument('--chyrons', help='json: {stem: {era, year, cycle, title}}')
    ap.add_argument('--seconds', type=float, default=15.0)
    ap.add_argument('--fps', type=int, default=24)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, '_txt'); os.makedirs(tmp, exist_ok=True)
    names = [n.strip() for n in a.names.split(',')][:2]
    chy = json.load(open(a.chyrons)) if a.chyrons else {}
    paths = sorted(glob.glob(os.path.join(a.clips, '*.mp4')))
    tr = transcribe(paths, os.path.join(a.out, 'transcripts.json'))
    for p in paths:
        stem = os.path.splitext(os.path.basename(p))[0]
        render(p, os.path.join(a.out, stem + '_cap.mp4'), tr[os.path.basename(p)], names, a.threshold,
               chy.get(stem), a.seconds, a.fps, tmp)
        print('captioned', stem, flush=True)

if __name__ == '__main__':
    main()
