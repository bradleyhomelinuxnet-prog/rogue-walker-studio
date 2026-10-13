#!/usr/bin/env python3
"""
fc_control.py — drive a running FilmCraft over its JSON-lines control channel (no MCP needed).

Start the app first:  filmcraft --control 9876      (listens on 127.0.0.1 only)

  python3 fc_control.py commands [filter]            list engine command ids (optionally containing FILTER)
  python3 fc_control.py exec COMMAND_ID ['{json}']   run one engine command, e.g. exec sequence.addEdit '{"seconds":3}'
  python3 fc_control.py call METHOD ['{json}']       raw control method, e.g. call ui.inspect
  python3 fc_control.py screenshot OUT.png [panel]   screenshot the window (or one panel)
  python3 fc_control.py batch FILE.jsonl             run one {"command":..,"params":{..}} per line, stop on error

Options: --host 127.0.0.1 --port 9876 --timeout 60
Standard library only. Works on Windows, macOS and Linux.
"""
import argparse, json, socket, sys

class Control:
    def __init__(self, host='127.0.0.1', port=9876, timeout=60):
        if host not in ('127.0.0.1', 'localhost', '::1'):
            sys.exit('refusing non-loopback host: the control channel is local-only by design')
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.f = self.sock.makefile('rwb')
        self.n = 0

    def call(self, method, params=None):
        self.n += 1
        req = {'id': self.n, 'method': method, 'params': params or {}}
        self.f.write((json.dumps(req) + '\n').encode()); self.f.flush()
        line = self.f.readline()
        if not line:
            raise RuntimeError('connection closed by FilmCraft')
        rep = json.loads(line)
        if not rep.get('ok', True) or 'error' in rep:
            raise RuntimeError(f"{method} failed: {rep.get('error', rep)}")
        return rep.get('result', rep)

    def execute(self, command, params=None):
        return self.call('engine.execute', {'command': command, 'params': params or {}})

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('action', choices=['commands', 'exec', 'call', 'screenshot', 'batch'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--host', default='127.0.0.1'); ap.add_argument('--port', type=int, default=9876)
    ap.add_argument('--timeout', type=float, default=60)
    a = ap.parse_args()
    try:
        c = Control(a.host, a.port, a.timeout)
    except OSError as e:
        sys.exit(f'cannot reach FilmCraft on {a.host}:{a.port} ({e}). Start it with:  filmcraft --control {a.port}')
    if a.action == 'commands':
        res = c.call('engine.commands')
        items = res if isinstance(res, list) else res.get('commands', res)
        flt = a.args[0].lower() if a.args else ''
        for it in items:
            cid = it.get('id') if isinstance(it, dict) else str(it)
            if flt in cid.lower():
                print(cid if not isinstance(it, dict) else f"{cid}\t{it.get('title', it.get('label', ''))}")
    elif a.action == 'exec':
        params = json.loads(a.args[1]) if len(a.args) > 1 else {}
        print(json.dumps(c.execute(a.args[0], params), indent=1))
    elif a.action == 'call':
        params = json.loads(a.args[1]) if len(a.args) > 1 else {}
        print(json.dumps(c.call(a.args[0], params), indent=1))
    elif a.action == 'screenshot':
        p = {'path': a.args[0]}
        if len(a.args) > 1:
            p['panel'] = a.args[1]
        print(json.dumps(c.call('ui.screenshot', p), indent=1))
    elif a.action == 'batch':
        for i, line in enumerate(open(a.args[0], encoding='utf-8'), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            step = json.loads(line)
            res = c.execute(step['command'], step.get('params', {}))
            print(f"{i}: {step['command']} -> {json.dumps(res)[:200]}")

if __name__ == '__main__':
    main()
