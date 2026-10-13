# FilmCraft MCP setup

## 1. Binaries
Two files matter: `filmcraft-cli` (the MCP server and command line) and `filmcraft` (the app).

- **Prebuilt**: FilmCraft's GitHub releases page or getartcraft.com/apps/filmcraft. On Windows the *portable* zip keeps
  prefs, logs and recovery in a `data` folder next to `filmcraft.exe`. Delete `portable.txt` to use `%APPDATA%\FilmCraft` instead.
- **From source** (Rust ≥ 1.95):
  ```
  git clone https://github.com/storytold/filmcraft && cd filmcraft
  cargo build --release -p filmcraft-cli -p filmcraft
  # → target/release/filmcraft-cli(.exe) and filmcraft(.exe)
  ```
Write down the absolute path to `filmcraft-cli`. Every config below needs it.

## 2a. Claude Desktop
Config file:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add one entry inside `"mcpServers"`. Windows paths need **double backslashes**.

Headless (no window, best first test): `configs/claude_desktop_config.headless.json`
Bridge (drive the live app you can watch): `configs/claude_desktop_config.bridge.json`

For bridge mode, start the app first with its control port open:
- Windows: double-click `scripts/START_FilmCraft_Bridge.bat` (edit the folder path inside it first)
- macOS/Linux: `scripts/start_bridge.sh /path/to/filmcraft`

Then fully quit and reopen Claude Desktop, and approve the `filmcraft` server.

## 2b. Claude Code
```
claude mcp add filmcraft-headless -- /abs/path/filmcraft-cli mcp --demo
claude mcp add filmcraft -- /abs/path/filmcraft-cli mcp --bridge 127.0.0.1:9876
```
Or drop `configs/mcp.json` into the project as `.mcp.json`.

## 3. Test
Ask: *"List FilmCraft commands that contain 'razor'."* The reply should come from `command_list`.
Then: *"Inspect the project and render a frame at 2 seconds."* Expect `project_inspect` and `render_frame`.

## 4. Real project
Swap `--demo` for `--project /abs/path/project.fcproj`. To make a project from scratch headlessly:
```
filmcraft-cli --save-as /abs/new.fcproj import /abs/clip1.mp4 /abs/clip2.mp4
```

## 5. Without MCP: control channel
With the app running (`filmcraft --control 9876`), any script on the same machine can drive it:
```
python3 scripts/fc_control.py commands timeline        # list command ids containing "timeline"
python3 scripts/fc_control.py exec timeline.razor '{"seconds": 3}'
python3 scripts/fc_control.py screenshot out.png
```
This is the route for cloud sessions that can run a shell on the PC but don't see the MCP tools.
