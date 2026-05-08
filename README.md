```
 ╔══════════════════════════════════════════════════════════╗
 ║                        MyCom                            ║
 ║        Dual-Panel File Manager for the Terminal         ║
 ║                      v0.1.0                             ║
 ╚══════════════════════════════════════════════════════════╝
```

A modern, keyboard-driven dual-panel file manager inspired by FAR Manager.
Built with Python and Textual.


## Features

    Dual-panel layout        two side-by-side directory panels
    Keyboard-first           all operations via F-keys and hotkeys
    Quick filter             type to filter files in real-time
    Sorting                  by name, size, date, or extension
    Pluggable viewers        extend with custom viewer/editor plugins
    Integrated terminal      switch any panel to a full terminal (planned)
    LLM chat                 context-aware Claude assistant (planned)


## Requirements

    Python 3.11+
    uv (https://docs.astral.sh/uv/)


## Installation

```bash
git clone https://github.com/ichMaster/mycom.git
cd mycom
uv sync
```


## Usage

```bash
uv run mycom
```

Launches two file browser panels showing your current directory.


## Key Bindings

```
 Navigation                          Operations
 ──────────────────────────────      ──────────────────────────────
 Tab          Switch active panel    F3           View file
 Enter        Enter dir / open file  F4           Edit file
 Backspace    Go to parent dir       F5           Copy
 Up / Down    Move cursor            F6           Move / rename
 Home         Jump to first entry    F7           Create directory
 End          Jump to last entry     F8           Delete
 PgUp / PgDn Scroll by page         F10, Ctrl+Q  Quit
                                     Ctrl+T       Toggle terminal
                                     Ctrl+L       Toggle LLM chat
```

### Quick Filter

Start typing to filter files in real-time (case-insensitive).
Press Escape to clear, Enter to navigate to the selected entry.

### Sorting

```
 Field       Description
 ──────────  ──────────────────────────
 Name        Alphabetical by filename
 Size        By file size
 Date        By last modified date
 Extension   By file extension
```

Directories are always listed before files.
Activating sort on the same field toggles ascending/descending.


## Configuration

Config file: `~/.config/mycom/config.toml`
If the file doesn't exist, defaults are used.

```toml
[general]
show_hidden = false
confirm_delete = true
default_sort = "name"
default_sort_direction = "asc"

[keybindings]
copy = "f5"
move = "f6"
delete = "f8"
quit = "f10"

[llm]
api_key_env = "ANTHROPIC_API_KEY"
model = "claude-sonnet-4-6"
max_context_files = 10
```


## Development

```bash
uv sync --all-groups          # install with dev deps
uv run pytest                 # run tests
uv run ruff check mycom/      # lint
uv run mkdocs serve           # build & serve docs
```


## License

MIT
