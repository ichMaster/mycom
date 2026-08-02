```
 ╔══════════════════════════════════════════════════════════╗
 ║                        MyCom                            ║
 ║        Dual-Panel File Manager for the Terminal         ║
 ║                      v0.1.1                             ║
 ╚══════════════════════════════════════════════════════════╝
```

A modern, keyboard-driven dual-panel file manager inspired by FAR Manager.
Built with Python and Textual.


## Features

    Dual-panel layout        two side-by-side directory panels, resizable (30/50/70 split)
    Keyboard-first           every current action driven by a central keymap registry
    View modes               Brief / Full / Wide (Ctrl+1/2/3)
    Sorting                  by name, extension, date, or size, with a header direction glyph
    Quick filter             type to filter files in real-time
    Structured logging       env-configurable, file-based (never stdout — owns the terminal)
    File operations          copy/move/delete/mkdir, viewer, editor, AI palette, Claude Code
                              integration — coming in later v0 phases (see spec/roadmap.md)


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

Every binding is resolved through a central keymap registry (`mycom/keymap.py`) and can be
overridden in `config.toml` under `[keybindings]` — see Configuration below.

```
 Navigation                            Panels & view
 ──────────────────────────────        ──────────────────────────────
 Tab            Switch active panel    Ctrl+U          Swap panels (paths + cursor)
 Enter          Enter dir / go up      Ctrl+Left/Right Shrink / grow active panel
 Backspace      Go to parent dir       Ctrl+1 / 2 / 3  View: Brief / Full / Wide
 Ctrl+PgUp      Go to parent (alias)   Ctrl+F3 / F4    Sort: name / extension
                                       Ctrl+F5 / F6    Sort: date / size
 F10, Ctrl+Q    Quit
```

Going up restores the cursor onto the directory you just left. Pressing the active sort key
again reverses direction — the panel header shows a `▲`/`▼` glyph on the active sort column
(Full/Wide modes only; Brief has no per-file headers). An unreadable, vanished, or replaced
directory shows an error dialog instead of a silent empty panel.

`F1` (help), `F3` (view), `F4` (edit), `F5` (copy), `F6` (move/rename), `F7` (mkdir), and `F8`
(delete) are already bound in the keymap registry but have no handler yet — they arrive with
file operations (v0.4) and the viewer/editor (v0.6).

### View Modes

    Brief   names only, laid out in as many columns as fit the panel width
    Full    name, size, modified date (with column headers)
    Wide    name, size (with column headers)

Directories show `<DIR>` in the size column. Long names truncate with `…` in the table; the
panel footer always shows the cursor row's full name plus the item count.

### Quick Filter

Start typing to filter files in real-time (case-insensitive).
Press Escape to clear, Enter to navigate to the selected entry.

### Sorting

```
 Field       Key      Description
 ──────────  ──────   ──────────────────────────
 Name        Ctrl+F3  Alphabetical by filename
 Extension   Ctrl+F4  By file extension
 Date        Ctrl+F5  By last modified date
 Size        Ctrl+F6  By file size
```

Directories are always listed before files. Activating sort on the same field toggles
ascending/descending.


## Configuration

Config file: `~/.config/mycom/config.toml`
If the file doesn't exist, defaults are used. Edits take effect at next start.

```toml
[general]
show_hidden = false             # both panels start with hidden files shown/hidden
confirm_delete = true           # not yet wired — arrives with delete (v0.4)
default_sort = "name"           # name | extension | date | size — invalid values
default_sort_direction = "asc"  # fall back to "name" with a logged warning
                                 # "asc" | "desc"

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

`[keybindings]` overrides apply to any action name in the keymap registry (`mycom/keymap.py`),
not just the four shown above — an override for an unknown action name is ignored. `[llm]` is
not yet used (arrives with the AI command palette, v0.7).

### Logging

MyCom never logs to stdout/stderr — it owns the whole terminal screen. Logging is file-based
and off by default (`WARNING` level):

```bash
MYCOM_LOG_LEVEL=DEBUG MYCOM_LOG_FILE=/tmp/mycom.log uv run mycom
```

Defaults: level `WARNING`, file `~/.config/mycom/mycom.log`.


## Development

```bash
uv sync --all-groups          # install with dev deps
uv run pytest                 # run tests
uv run ruff check mycom/      # lint
uv run mkdocs serve           # build & serve docs
```


## License

MIT
