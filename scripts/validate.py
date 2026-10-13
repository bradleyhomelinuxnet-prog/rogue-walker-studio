#!/usr/bin/env python3
"""Validate every skill: SKILL.md frontmatter (name matches folder, description present, < 1024 chars),
python scripts compile, json files parse."""
import glob, json, os, py_compile, re, sys
root = os.path.join(os.path.dirname(__file__), '..')
bad = 0
for d in sorted(glob.glob(os.path.join(root, 'skills', '*'))):
    n = os.path.basename(d)
    md = open(os.path.join(d, 'SKILL.md'), encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n', md, re.S)
    fm = m.group(1) if m else ''
    name = re.search(r'^name:\s*(.+)$', fm, re.M)
    desc = re.search(r'^description:\s*(.+)$', fm, re.M)
    errs = []
    if not name or name.group(1).strip().strip('"') != n: errs.append('name != folder')
    if not desc: errs.append('no description')
    elif len(desc.group(1)) > 1024: errs.append('description > 1024 chars')
    for p in glob.glob(os.path.join(d, '**', '*.py'), recursive=True):
        try: py_compile.compile(p, doraise=True)
        except py_compile.PyCompileError as e: errs.append(f'compile {os.path.basename(p)}: {e}')
    for j in glob.glob(os.path.join(d, '**', '*.json'), recursive=True):
        try: json.load(open(j, encoding='utf-8'))
        except Exception as e: errs.append(f'json {os.path.basename(j)}: {e}')
    print(f"{'OK ' if not errs else 'ERR'} {n}" + ('' if not errs else '  ' + '; '.join(errs)))
    bad += bool(errs)
for j in glob.glob(os.path.join(root, '.claude-plugin', '*.json')) + glob.glob(os.path.join(root, 'examples', '**', '*.json'), recursive=True):
    json.load(open(j, encoding='utf-8'))
print('plugin + example json OK')
sys.exit(1 if bad else 0)
