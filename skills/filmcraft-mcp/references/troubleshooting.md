# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Claude says it has no FilmCraft tools | The chat isn't a Claude Desktop/Code session on that PC (e.g. a cloud session linked to it). Desktop MCP config only serves the desktop app's own chats. | Open a chat in the Claude Desktop app itself, or use `fc_control.py` / the CLI / computer use. |
| Tools missing even in Claude Desktop | App not fully restarted, a JSON syntax error, or a wrong path | Quit from the tray, validate the JSON, use an absolute path with double backslashes on Windows |
| Bridge tools time out | App not started with `--control 9876`, or a different port | Run the launcher first and keep its window open. Match the port in the config. |
| `ui_screenshot` fails after 10 s | Window hidden or the display asleep | Wake the screen and un-minimise FilmCraft |
| Import does nothing | Relative paths | Use absolute paths, one per line |
| Two FilmCraft installs (portable + installed) | Computer use grants the installed one, while the launcher opens the portable one | Point the launcher and the computer-use grant at the same build |
| Export fails on HEVC | H.265 export is hardware-only (NVENC / VideoToolbox) | Export H.264, or enable hardware encoding |
| Edits went wrong | — | `edit.undo` (repeatable). Alpha software, so save often. |
