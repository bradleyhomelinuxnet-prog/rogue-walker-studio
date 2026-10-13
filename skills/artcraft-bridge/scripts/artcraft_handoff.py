#!/usr/bin/env python3
"""
artcraft_handoff.py — collect ArtCraft (or any generator's) renders into an edit project.

  python3 artcraft_handoff.py --discover
  python3 artcraft_handoff.py --from DIR --to PROJECT/src [--since YYYY-MM-DD] [--kinds video,image] [--prefix ac]

Copies (never moves) new media from DIR into PROJECT/src as  <prefix>_<YYYYMMDD_HHMMSS>_<n>.<ext>  (sorted by
modification time), skips files already copied (by size + mtime fingerprint), and writes beside the destination:
  handoff_manifest.json   source path, new name, size, mtime, duration (video)
  filmcraft_import.txt    absolute paths, one per line, for FilmCraft's media_import
Standard library only (ffprobe optional, used for durations).
"""
import argparse, datetime, json, os, shutil, subprocess, sys

VIDEO = {'.mp4', '.mov', '.webm', '.mkv', '.m4v'}
IMAGE = {'.png', '.jpg', '.jpeg', '.webp'}
MODEL3D = {'.glb', '.gltf', '.obj', '.ply', '.splat'}

def candidates():
    home = os.path.expanduser('~')
    names = ['ArtCraft', 'Artcraft', 'artcraft', 'Storyteller']
    roots = [home, os.path.join(home, 'Documents'), os.path.join(home, 'Pictures'), os.path.join(home, 'Videos'),
             os.path.join(home, 'Downloads'), os.path.join(home, 'Desktop'),
             os.environ.get('APPDATA', ''), os.environ.get('LOCALAPPDATA', ''),
             os.path.join(home, 'Library', 'Application Support'), os.path.join(home, '.local', 'share')]
    hits = []
    # ArtCraft's own data root (Windows: C:\\Users\\<you>\\Artcraft) — renders land in downloads/ and assets/.
    # Never read its credentials/ or settings/ folders.
    for n in ('Artcraft', 'ArtCraft'):
        for sub in ('downloads', 'assets'):
            p = os.path.join(home, n, sub)
            if os.path.isdir(p) and p not in hits:
                hits.append(p)
    for r in roots:
        for n in names:
            p = os.path.join(r, n)
            if r and os.path.isdir(p):
                hits.append(p)
    return hits

def media_in(d, kinds):
    exts = set()
    if 'video' in kinds: exts |= VIDEO
    if 'image' in kinds: exts |= IMAGE
    if '3d' in kinds: exts |= MODEL3D
    out = []
    for root, _, files in os.walk(d):
        for f in files:
            if os.path.splitext(f)[1].lower() in exts:
                out.append(os.path.join(root, f))
    return out

def duration(p):
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                           capture_output=True, text=True, timeout=20)
        return round(float(r.stdout.strip()), 3)
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--discover', action='store_true')
    ap.add_argument('--from', dest='src'); ap.add_argument('--to', dest='dst')
    ap.add_argument('--since', help='only files modified on/after this date (YYYY-MM-DD)')
    ap.add_argument('--kinds', default='video,image')
    ap.add_argument('--prefix', default='ac')
    a = ap.parse_args()
    if a.discover:
        hits = candidates()
        if not hits:
            print('No ArtCraft folders found in the usual places. In ArtCraft, check where it saves or exports renders, '
                  'or use your browser/OS downloads folder with --from.')
        for h in hits:
            n = len(media_in(h, {'video', 'image'}))
            print(f'{h}\t{n} media files')
        return
    if not (a.src and a.dst):
        sys.exit('need --from and --to (or --discover)')
    kinds = set(a.kinds.split(','))
    since = datetime.datetime.strptime(a.since, '%Y-%m-%d').timestamp() if a.since else 0
    os.makedirs(a.dst, exist_ok=True)
    proj = os.path.dirname(os.path.abspath(a.dst))
    man_path = os.path.join(proj, 'handoff_manifest.json')
    manifest = json.load(open(man_path)) if os.path.exists(man_path) else []
    seen = {(m['size'], m['mtime']) for m in manifest}
    files = sorted((p for p in media_in(a.src, kinds) if os.path.getmtime(p) >= since), key=os.path.getmtime)
    new = 0
    for i, p in enumerate(files, 1):
        st = os.stat(p)
        fp = (st.st_size, int(st.st_mtime))
        if fp in seen:
            continue
        stamp = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y%m%d_%H%M%S')
        name = f'{a.prefix}_{stamp}_{len(manifest) + 1:03d}{os.path.splitext(p)[1].lower()}'
        dest = os.path.join(a.dst, name)
        shutil.copy2(p, dest)
        manifest.append({'source': p, 'name': name, 'size': fp[0], 'mtime': fp[1],
                         'duration': duration(dest) if os.path.splitext(p)[1].lower() in VIDEO else None})
        seen.add(fp); new += 1
    json.dump(manifest, open(man_path, 'w'), indent=1)
    with open(os.path.join(proj, 'filmcraft_import.txt'), 'w', encoding='utf-8') as f:
        for m in manifest:
            f.write(os.path.abspath(os.path.join(a.dst, m['name'])) + '\n')
    print(f'copied {new} new file(s); {len(manifest)} total in {a.dst}')
    print(f'manifest: {man_path}\nFilmCraft import list: {os.path.join(proj, "filmcraft_import.txt")}')

if __name__ == '__main__':
    main()
