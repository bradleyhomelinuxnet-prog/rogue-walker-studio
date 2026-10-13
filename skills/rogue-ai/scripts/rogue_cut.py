#!/usr/bin/env python3
"""
rogue_cut.py — turn a cut sheet (JSON) into a finished FilmCraft edit, headless, from the shell.

  python rogue_cut.py CUTSHEET.json            build the .fcproj, export the MP4, render check frames
  python rogue_cut.py CUTSHEET.json --dry-run  print the FilmCraft commands without running them
  python rogue_cut.py --which                  show which filmcraft-cli will be used (newest found)

Every step is one `filmcraft-cli --project P --save exec ...` call, so the project on disk is always the
current state: if a step fails, open the .fcproj in FilmCraft and carry on by hand, or fix the sheet and re-run
(a re-run starts a fresh project). Originals are never touched; output goes to new files only.

Cut sheet keys (paths relative to the sheet):
  output        "out/reel.mp4"                      required
  project       "out/reel.fcproj"                   default: output with .fcproj
  format        {"width":1920,"height":1080,"fps":24}
  clips         ["src/a.mp4", {"path":"src/b.mp4","in":2.0,"duration":6.0}, ...]
                or {"folder":"src","sort":"name"|"mtime","match":"*.mp4","limit":N}
  transition    {"type":"cross_dissolve","frames":12}   or null for hard cuts
  fade          {"in_frames":12,"out_frames":24}        fade from/to black at the ends
  title         {"text":"THE ENGINEERED SKY","sub":"Live on Time","at":0,"seconds":4}
  captions      [{"at":0.5,"dur":3.0,"text":"History didn't evolve.","speaker":"NATORI"}, ...]
  speakers      {"NATORI":"#F0C89E","ROGUE":"#9EC9F0"}
  style         {"position":"top"|"bottom","font":"Georgia","font_style":"Bold","size":52,
                 "color":"#E8D7B0","margin":110,"shadow":true,"stroke":true,"stroke_color":"#0B0B0B"}
  srt           "captions.srt"   (imported as a caption track and burned in, FilmCraft's own caption look)
  audio         [{"path":"bed.wav","track":"A2","db":-14,"at":0}]
  mute_clip_audio  true   (silence A1, the clips' own sound)
  loudness      -16      (integrated LUFS for the export; true peak -1.5 dBTP)
  checks        [2.0, 30.5]   extra seconds to render as check frames (captions/title are checked automatically)
Standard library only. Needs FilmCraft 0.6+.
"""
import argparse, fnmatch, glob, json, os, re, shutil, subprocess, sys, time

TPS = 254016000000  # FilmCraft ticks per second
# graphics.newText takes a 0-based video track index: V1 = 0 (the clips)
TRACK_TITLE, TRACK_SUB, TRACK_CAPS = 1, 2, 3


# ---------- locating filmcraft-cli ----------
def _version(exe):
    try:
        out = subprocess.run([exe, '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20).stdout
        m = re.search(r'(\d+)\.(\d+)\.(\d+)', out)
        return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)
    except Exception:
        return None


def find_cli(explicit=None):
    if explicit:
        return explicit
    if os.environ.get('FILMCRAFT_CLI'):
        return os.environ['FILMCRAFT_CLI']
    exe = 'filmcraft-cli.exe' if os.name == 'nt' else 'filmcraft-cli'
    home = os.path.expanduser('~')
    cands = []
    for root in [os.path.join(home, 'OneDrive', 'Desktop'), os.path.join(home, 'Desktop'),
                 os.path.join(home, 'Downloads'), os.path.join(home, 'Applications')]:
        for depth in ('*', '*/*', '*/*/*'):
            cands += glob.glob(os.path.join(root, depth, exe))
    cands += [r'C:\Program Files\FilmCraft\filmcraft-cli.exe', '/Applications/FilmCraft.app/Contents/MacOS/filmcraft-cli',
              '/usr/local/bin/filmcraft-cli', '/usr/bin/filmcraft-cli']
    on_path = shutil.which('filmcraft-cli')
    if on_path:
        cands.append(on_path)
    best, best_v = None, None
    for c in dict.fromkeys(cands):
        if os.path.isfile(c):
            v = _version(c)
            if v is not None and (best_v is None or v > best_v):
                best, best_v = c, v
    if not best:
        sys.exit('filmcraft-cli not found. Set FILMCRAFT_CLI or "filmcraft_cli" in the cut sheet.')
    return best


# ---------- running FilmCraft ----------
# Sync clients (OneDrive, Dropbox) briefly lock a file right after it's written. A failed save leaves the previous
# project on disk untouched, so re-running the same command is safe.
_LOCKED = ('os error 5)', 'os error 32)', 'Access is denied', 'being used by another process')


def _proc(cmd, body=None, tries=6):
    for i in range(tries):
        r = subprocess.run(cmd, input=body, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode == 0 or not any(k in (r.stderr or '') for k in _LOCKED) or i == tries - 1:
            return r
        time.sleep(0.5 * (i + 1))


class FC:
    def __init__(self, cli, project, dry=False):
        self.cli, self.project, self.dry, self.log = cli, project, dry, []

    def _run(self, args, save=True):
        cmd = [self.cli, '--compact', '--project', self.project] + (['--save'] if save else []) + args
        self.log.append(cmd)
        if self.dry:
            print('  $', ' '.join(a if ' ' not in a else f'"{a}"' for a in cmd[1:]))
            return {}
        r = _proc(cmd)
        if r.returncode != 0:
            raise RuntimeError(f"{' '.join(args[:2])} failed:\n{(r.stderr or r.stdout).strip()}")
        out = r.stdout.strip()
        try:
            return json.loads(out.splitlines()[-1]) if out else {}
        except json.JSONDecodeError:
            return {'raw': out}

    def exec(self, cid, params=None, save=True):
        return self._run(['exec', cid, json.dumps(params or {})], save)

    def run_lines(self, lines):
        """Several commands in ONE process (state such as the clip selection only lives within a process)."""
        body = '\n'.join(json.dumps({'id': i, 'params': p}) for i, p in lines) + '\n'
        cmd = [self.cli, '--compact', '--project', self.project, '--save', 'run', '-']
        self.log.append(cmd + [body])
        if self.dry:
            print('  $', 'run -  <<', body.strip().replace('\n', ' | '))
            return
        r = _proc(cmd, body)
        if r.returncode != 0:
            raise RuntimeError(f"run {[i for i, _ in lines]} failed:\n{(r.stderr or r.stdout).strip()}")

    def new_project(self, name):
        cmd = [self.cli, '--compact', 'exec', 'file.newProject', json.dumps({'name': name}), '--save-as', self.project]
        self.log.append(cmd)
        if self.dry:
            print('  $', ' '.join(cmd[1:]))
            return
        r = _proc(cmd)
        if r.returncode != 0 or not os.path.exists(self.project):
            raise RuntimeError(f'could not create project: {(r.stderr or r.stdout).strip()}')

    def import_media(self, paths):
        res = self._run(['import'] + paths)
        if res.get('errors'):
            raise RuntimeError(f"import errors: {res['errors']}")
        return res.get('items', list(range(1, len(paths) + 1)))

    def inspect(self, what='sequence'):
        return self._run(['inspect', what], save=False)

    def render(self, seconds, out, scale=0.5):
        self._run(['render', '--seconds', f'{seconds:.3f}', '--out', out, '--scale', str(scale), '--allow-offline'], save=False)

    def export(self, out, settings):
        return self._run(['export', out, '--settings', json.dumps(settings)], save=False)


# ---------- helpers ----------
def rel(base, p):
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))


def probe_seconds(path):
    if not shutil.which('ffprobe'):
        return None
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def resolve_clips(base, spec):
    if isinstance(spec, dict):
        folder = rel(base, spec['folder'])
        pat = spec.get('match', '*.mp4')
        files = [os.path.join(folder, f) for f in os.listdir(folder) if fnmatch.fnmatch(f.lower(), pat.lower())]
        files.sort(key=(os.path.getmtime if spec.get('sort') == 'mtime' else (lambda p: os.path.basename(p).lower())))
        if spec.get('reverse'):
            files.reverse()
        if spec.get('limit'):
            files = files[:spec['limit']]
        return [{'path': f} for f in files]
    return [({'path': c} if isinstance(c, str) else dict(c)) for c in spec]


def ticks(s):
    return int(round(s * TPS))


def add_text(fc, text, at, dur, track, y, width, style, color, size=None, dry=False):
    """Text clip on a video track, horizontally centred, baseline at y."""
    res = fc.exec('graphics.newText', {'text': text, 'size': size or style.get('size', 52),
                                       'position': [width // 2, y], 'seconds': dur, 'track': track,
                                       'time': ticks(at), 'newClip': True})
    clip = res.get('clip')
    if dry or clip is None:
        return clip
    props = {'fill_color': color, 'shadow': style.get('shadow', True)}
    if style.get('font'):
        props['font'] = style['font']
    if style.get('font_style'):
        props['font_style'] = style['font_style']
    if style.get('stroke'):  # a thin dark outline keeps pale colours readable over bright sky
        props.update({'stroke': True, 'stroke_width': style.get('stroke_width', 3),
                      'stroke_color': style.get('stroke_color', '#0B0B0B')})
    fc.exec('graphics.set', {'clip': clip, 'layer': 0, 'props': props})
    fc.exec('graphics.alignFrame.hcenter', {'clip': clip, 'layers': [0]})
    return clip


# ---------- the build ----------
def build(sheet_path, cli_override=None, dry=False):
    base = os.path.dirname(os.path.abspath(sheet_path))
    with open(sheet_path, encoding='utf-8') as f:
        S = json.load(f)
    out = rel(base, S['output'])
    project = rel(base, S.get('project') or os.path.splitext(S['output'])[0] + '.fcproj')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fmt = {'width': 1920, 'height': 1080, 'fps': 24, **S.get('format', {})}
    W, H, fps = fmt['width'], fmt['height'], fmt['fps']
    style = {'position': 'top', 'font': 'Georgia', 'font_style': 'Bold', 'size': round(52 * H / 1080),
             'color': '#E8D7B0', 'margin': round(110 * H / 1080), 'shadow': True, 'stroke': True,
             'stroke_width': max(2, round(3 * H / 1080)), **S.get('style', {})}
    speakers = S.get('speakers', {})

    cli = find_cli(cli_override or S.get('filmcraft_cli'))
    print(f'filmcraft-cli: {cli}')
    fc = FC(cli, project, dry)

    clips = resolve_clips(base, S['clips'])
    for c in clips:
        c['path'] = rel(base, c['path'])
        if not dry and not os.path.isfile(c['path']):
            sys.exit(f"missing clip: {c['path']}")
    if not clips:
        sys.exit('no clips matched')
    print(f'{len(clips)} clips → {out}')

    if os.path.exists(project) and not dry:
        os.remove(project)  # a re-run is a clean rebuild of OUR project file, never the user's media
    fc.new_project(S.get('name') or os.path.splitext(os.path.basename(out))[0])
    fc.exec('file.newSequence', {'name': S.get('name', 'Reel'), 'width': W, 'height': H, 'fps': fps,
                                 'video': 6, 'audio': 3})

    # media
    items = fc.import_media([c['path'] for c in clips])
    video_ids = []
    t = 0.0
    for c, item in zip(clips, items):
        p = {'item': item, 'track': 'V1', 'seconds': round(t, 6), 'insert': False}
        if c.get('in') is not None:
            p['sourceIn'] = ticks(c['in'])
        if c.get('duration') is not None:
            p['duration'] = ticks(c['duration'])
        res = fc.exec('timeline.place', p)
        placed = res.get('placed') or [[(res.get('clips') or [None])[0]]]
        video_ids.append(placed[0][0])
        d = c.get('duration') or (probe_seconds(c['path']) if os.path.isfile(c['path']) else None) or 0
        c['seconds'] = d
        t += d
    if not dry and video_ids and video_ids[0] is not None:
        fc.run_lines([('timeline.select', {'clips': [v for v in video_ids if v is not None], 'add': False,
                                           'toggle': False}),
                      ('clip.scaleToFrameSize', {})])

    # transitions between clips, fades at the ends
    tr = S.get('transition', {'type': 'cross_dissolve', 'frames': 12})
    if tr:
        for vid in video_ids[:-1]:
            if vid is not None:
                fc.exec('sequence.applyVideoTransition', {'clip': vid, 'effect': tr.get('type', 'cross_dissolve'),
                                                          'frames': tr.get('frames', 12), 'edge': 'out'})
    fade = S.get('fade')
    if fade and video_ids:
        if fade.get('in_frames'):
            fc.exec('sequence.applyVideoTransition', {'clip': video_ids[0], 'effect': 'cross_dissolve',
                                                      'frames': fade['in_frames'], 'edge': 'in'})
        if fade.get('out_frames'):
            fc.exec('sequence.applyVideoTransition', {'clip': video_ids[-1], 'effect': 'cross_dissolve',
                                                      'frames': fade['out_frames'], 'edge': 'out'})

    checks = list(S.get('checks', []))
    top = style['position'] == 'top'

    # title (V2), subtitle (V3), caption lines (V4, V5)
    ttl = S.get('title')
    if ttl:
        at, secs = ttl.get('at', 0), ttl.get('seconds', 4)
        y = round(H * 0.42) if ttl.get('center') else (style['margin'] + style['size'] if top else H - style['margin'])
        add_text(fc, ttl['text'], at, secs, TRACK_TITLE, y, W, style, ttl.get('color', style['color']),
                 size=ttl.get('size', round(style['size'] * 1.5)), dry=dry)
        if ttl.get('sub'):
            add_text(fc, ttl['sub'], at, secs, TRACK_SUB, y + round(style['size'] * 1.3), W,
                     {**style, 'font_style': 'Regular'}, ttl.get('sub_color', '#9EC9F0'),
                     size=round(style['size'] * 0.7), dry=dry)
        checks.append(at + secs / 2)

    for cap in S.get('captions', []):
        lines = cap['text'].split('\n')
        color = speakers.get(cap.get('speaker', ''), cap.get('color', style['color']))
        for i, line in enumerate(lines):
            if top:
                y = style['margin'] + style['size'] + i * round(style['size'] * 1.25)
            else:
                y = H - style['margin'] - (len(lines) - 1 - i) * round(style['size'] * 1.25)
            add_text(fc, line, cap['at'], cap.get('dur', 3), TRACK_CAPS + i, y, W, style, color, dry=dry)
        checks.append(cap['at'] + cap.get('dur', 3) / 2)

    if S.get('srt'):
        fc.exec('captions.import', {'path': rel(base, S['srt'])})

    # audio
    if S.get('mute_clip_audio'):
        fc.exec('mixer.setStrip', {'strip': 'A1', 'muted': True})
    for a in S.get('audio', []):
        aid = fc.import_media([rel(base, a['path'])])[0]
        trk = a.get('track', 'A2')
        fc.exec('timeline.place', {'item': aid, 'track': trk, 'seconds': a.get('at', 0), 'insert': False,
                                   'video': False})
        if a.get('db') is not None:
            fc.exec('mixer.setStrip', {'strip': trk, 'volumeDb': a['db']})

    # verify the timeline before spending render time
    if not dry:
        seq = fc.inspect('sequence')
        v1 = next((tk for tk in seq.get('video', []) if tk.get('name', '').endswith('1')), None)
        n = len(v1['items']) if v1 else '?'
        end = max((it['end'] for tk in seq.get('video', []) for it in tk.get('items', [])), default=0) / TPS
        print(f'timeline: {n} clips on V1, {end:.2f}s ({round(end * fps)} frames @ {fps})')

    # export
    settings = {'burnCaptions': bool(S.get('srt'))}
    if S.get('loudness') is not None:
        settings['effects'] = {'loudness': {'enabled': True, 'target_lufs': S['loudness'], 'true_peak_dbtp': -1.5}}
    res = fc.export(out, settings)
    if not dry:
        r = res.get('result', res)
        print(f"exported {out}  ({r.get('frames', '?')} frames, {round((r.get('bytes') or 0) / 1e6, 1)} MB)")

    # check frames for Claude to look at
    frames_dir = os.path.join(os.path.dirname(out), 'check_frames')
    os.makedirs(frames_dir, exist_ok=True)
    written = []
    # Sheet-listed checks always render; title/caption checks are thinned evenly across the whole timeline.
    explicit = [round(x, 2) for x in S.get('checks', [])]
    auto = sorted(set(round(x, 2) for x in checks) - set(explicit))
    room = max(0, 16 - len(explicit))
    if len(auto) > room:
        auto = [auto[round(i * (len(auto) - 1) / max(1, room - 1))] for i in range(room)] if room else []
    for s in sorted(set(explicit + auto)):
        p = os.path.join(frames_dir, f'f_{s:07.2f}.png')
        try:
            fc.render(s, p)
            written.append(p)
        except RuntimeError as e:
            print(f'  (check frame at {s}s failed: {e})')
    if written:
        print('check frames:\n  ' + '\n  '.join(written))
    print(f'project: {project}  (open in FilmCraft to keep editing)')


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('sheet', nargs='?')
    ap.add_argument('--cli', help='path to filmcraft-cli (default: newest found)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--which', action='store_true')
    a = ap.parse_args()
    if a.which:
        c = find_cli(a.cli)
        print(c, _version(c))
        return
    if not a.sheet:
        ap.error('give a cut sheet, or --which')
    try:
        build(a.sheet, a.cli, a.dry_run)
    except RuntimeError as e:
        sys.exit(f'FilmCraft step failed: {e}')


if __name__ == '__main__':
    main()
