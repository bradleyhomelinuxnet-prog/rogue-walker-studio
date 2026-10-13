# ArtCraft notes (from the public repo, October 2026)

- Desktop app: Tauri, at `crates/desktop/artcraft/`. Frontend at `frontend/apps/artcraft/` (TypeScript, Nx, React, Vite, Zustand, Three.js).
- Provider clients: `crates/api_clients/`. Task persistence: SQLite (`schema/database/sqlite_tasks/`, migrations in `_database/sql/artcraft_migrations/`).
- A vendored `tauri-plugin-http` fork with cookie access (used for website-account providers).
- Each Tauri command is its own module. Command conventions are in `crates/desktop/artcraft/src/services/storyteller/commands/AGENTS.md`.
- Builds: Windows and macOS installers. Linux builds from source (`script/artcraft/`).
- Backend services live in a separate `artcraft-services` repo.

## Automation surfaces
| Surface | Status |
|---|---|
| MCP server | none |
| CLI | none |
| Local HTTP / control port | none documented |
| Tauri commands | internal (frontend ↔ Rust), not exposed to outside processes |
| UI automation | works via OS-level computer use |

## How an agent surface could be added (for contributors)
ArtCraft is open source, so an MCP or control channel could follow FilmCraft's pattern: expose the existing Tauri
command modules over a loopback-only JSON-lines socket behind a `--control <port>` flag, then wrap that in a small MCP
server (`list_models`, `generate_image`, `generate_video`, `task_status`, `export_asset`), with every spending call
requiring a confirmation token. If you build it, contribute it upstream under the repo's license, and update this
skill to Route 0.
