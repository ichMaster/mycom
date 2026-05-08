# Panel System

MyCom's UI is organized around a flexible panel system. The main area is split into two panels, each of which can independently operate in one of three modes.

## Panel Modes

| Mode | Description |
|------|-------------|
| File Browser | Directory listing with navigation and file operations |
| Terminal | Full interactive terminal (PTY-backed) |
| LLM Chat | Context-aware Claude chat interface |

## File Browser Panel

The default panel mode. Composes a **PathBar** (showing current directory) and a **FileList** (directory contents table).

Features:
- Displays current directory with type icons, names, sizes, dates, and permissions
- Directories listed before files
- Active/inactive visual state (border color)
- Exposes `current_path` and `selected_files` for use by other components

## Switching Modes

Each panel can switch modes independently:
- **Ctrl+T** — Toggle terminal mode
- **Ctrl+L** — Toggle LLM chat mode

The inactive mode's state is preserved when switching back.

## Base Panel Interface

All panel modes implement `BasePanel`:

- `activate()` / `deactivate()` — Toggle visual focus state
- `get_current_path()` — Current working directory (if applicable)
- `get_selected_files()` — Selected file paths
