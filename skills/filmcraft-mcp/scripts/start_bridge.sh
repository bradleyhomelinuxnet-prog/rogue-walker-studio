#!/usr/bin/env sh
# Launch FilmCraft with its JSON control channel on 127.0.0.1:9876 (loopback only).
# usage: ./start_bridge.sh /path/to/filmcraft   [port]
BIN="${1:-filmcraft}"; PORT="${2:-9876}"
echo "Starting $BIN --control $PORT (leave this running while Claude drives the app)"
exec "$BIN" --control "$PORT"
