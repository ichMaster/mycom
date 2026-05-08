# Architecture

## Application Layout

```
┌─────────────────────────────────────────────────┐
│                  AppHeader                       │
│                   "MyCom"                        │
├────────────────────┬────────────────────────────┤
│                    │                            │
│   Left Panel       │   Right Panel              │
│  (FileBrowser)     │  (FileBrowser)             │
│                    │                            │
│  ┌──────────────┐  │  ┌──────────────────────┐  │
│  │   PathBar    │  │  │      PathBar         │  │
│  ├──────────────┤  │  ├──────────────────────┤  │
│  │              │  │  │                      │  │
│  │   FileList   │  │  │     FileList         │  │
│  │              │  │  │                      │  │
│  └──────────────┘  │  └──────────────────────┘  │
├────────────────────┴────────────────────────────┤
│ F1 Help  F3 View  F4 Edit  F5 Copy  ...  F10   │
└─────────────────────────────────────────────────┘
```

## Component Hierarchy

```
MyComApp (textual.App)
├── AppHeader
├── Horizontal#panel-container
│   ├── FileBrowserPanel#left-panel
│   │   ├── PathBar
│   │   └── FileList
│   └── FileBrowserPanel#right-panel
│       ├── PathBar
│       └── FileList
└── StatusBar
```

## Panel System

Each panel slot can host one of three modes:
- **FILE_BROWSER** — Directory listing (default)
- **TERMINAL** — Embedded PTY terminal (Phase 6)
- **LLM_CHAT** — Claude chat interface (Phase 7)

Panel switching is done via `Tab` (toggle active panel) and mode hotkeys (`Ctrl+T`, `Ctrl+L`).

## Key Flows

### Panel Switching
1. User presses `Tab`
2. `MyComApp.action_switch_panel()` fires
3. Current panel deactivated (border dims)
4. Opposite panel activated (border highlights)
5. Focus moves to new active panel's FileList

### Directory Navigation
1. User presses `Enter` on a directory
2. `FileBrowserPanel.navigate_to()` called
3. `list_directory()` reads filesystem
4. `FileList.load_directory()` updates the table
5. `PathBar.path` updated

## Configuration

Config is loaded once at startup from `~/.config/mycom/config.toml` and passed through as frozen dataclasses. See [Configuration](configuration.md).
