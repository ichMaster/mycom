# MyCom

A modern, keyboard-driven dual-panel file manager for the terminal, inspired by FAR Commander.

## Features

- **Dual-panel layout** — two side-by-side directory panels, switch with Tab
- **Keyboard-first** — all operations via F-keys and hotkeys
- **Quick filter** — type to filter files in real-time
- **Sorting** — sort by name, size, date, or extension with direction toggle
- **Pluggable viewers/editors** — extend with custom plugins (Phase 5)
- **Integrated terminal** — switch any panel to a full terminal (Phase 6)
- **LLM chat** — context-aware Claude assistant in any panel (Phase 7)

## Quick Start

```bash
# Clone and install
git clone https://github.com/ichMaster/mycom.git
cd mycom
uv sync

# Run
uv run mycom
```

## Key Bindings

| Key | Action |
|-----|--------|
| Tab | Switch active panel |
| Enter | Open directory / file |
| Backspace | Go to parent directory |
| F3 | View file |
| F4 | Edit file |
| F5 | Copy |
| F6 | Move |
| F7 | Create directory |
| F8 | Delete |
| F10 / Ctrl+Q | Quit |
| Ctrl+T | Toggle terminal panel |
| Ctrl+L | Toggle LLM chat panel |

See [Keybindings](keybindings.md) for the full list and customization options.

## Documentation

- [Getting Started](getting-started.md) — Installation and first run
- [Configuration](configuration.md) — Config file format and options
- [Navigation](navigation.md) — Directory browsing, filtering, sorting
- [Panels](panels.md) — Panel system and modes
- [Architecture](architecture.md) — Component layout and data flow
- [Development](development.md) — Dev setup, testing, linting
- [API Reference](reference/) — Auto-generated from source
