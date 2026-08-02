```
 ╔══════════════════════════════════════════════════════════╗
 ║                        MyCom                            ║
 ║        Dual-Panel File Manager for the Terminal         ║
 ║                      v0.2.0                             ║
 ╚══════════════════════════════════════════════════════════╝
```

A modern, keyboard-driven dual-panel file manager inspired by FAR Manager.
Built with Python and Textual.


## Features

    Dual-panel layout        two side-by-side directory panels, resizable (30/50/70 split)
    Keyboard-first           every current action driven by a central keymap registry
    View modes               Brief / Full / Wide (Ctrl+1/2/3)
    Sorting                  by name, extension, date, or size, with a header direction glyph
    Selection                Ins/Space toggle, mask select/deselect, invert — yellow highlight,
                              live footer count + size
    Hidden files toggle      Ctrl+H, global, cursor-preserving
    Persistence               panel paths/sort/view and hidden toggle survive a restart (SQLite,
                              WAL); a vanished saved path falls back gracefully
    Quick filter             type to filter files in real-time
    Far classic theme        one palette file drives every color; renders on truecolor and
                              256-color terminals
    Dialog kit                keyboard-navigable modals: Tab/arrows/hotkeys/Enter/Esc, stackable
    Key bar                  F1-F10 labels generated from the keymap (never drifts); clickable
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
 Tab            Switch active panel    Ctrl+U          Swap panels (paths, cursor, selection)
 Enter          Enter dir / go up      Ctrl+Left/Right Shrink / grow active panel
 Backspace      Go to parent dir       Ctrl+1 / 2 / 3  View: Brief / Full / Wide
 Ctrl+PgUp      Go to parent (alias)   Ctrl+F3 / F4    Sort: name / extension
 Ctrl+H         Toggle hidden files    Ctrl+F5 / F6    Sort: date / size
 F10, Ctrl+Q    Quit

 Selection
 ──────────────────────────────
 Ins, Space     Toggle cursor entry, move down
 + (Alt+=)      Select by mask (e.g. *.py;*.md) — default "*" selects all
 - (Alt+-)      Deselect by mask
 * (Alt+8)      Invert selection
```

Going up restores the cursor onto the directory you just left. Pressing the active sort key
again reverses direction — the panel header shows a `▲`/`▼` glyph on the active sort column
(Full/Wide modes only; Brief has no per-file headers). An unreadable, vanished, or replaced
directory shows an error dialog instead of a silent empty panel.

### Selection

`Ins`/`Space` toggle the cursor entry and advance; `..` can never be selected. Selected rows
render in yellow. Mask select/deselect (`+`/`-`) prompt for a pattern (default `*`, so `+` then
`Enter` selects everything); `*` inverts the current selection. Selection is per-panel, survives
sort/view-mode changes, and clears when you navigate to a different directory. It's the input
MyCom's file operations (copy/move/delete, v0.4) will act on once they land — no built-in
consumer of a selection exists yet.

`F1` (help), `F3` (view), `F4` (edit), `F5` (copy), `F6` (move/rename), `F7` (mkdir), and `F8`
(delete) are already bound in the keymap registry but have no handler yet — they arrive with
file operations (v0.4) and the viewer/editor (v0.6).

### Key Bar

The bottom row shows all ten F-key slots, generated from the keymap registry — a label can never
drift from its actual binding, and an unassigned slot (F2, F9 — reserved for menus, v1.8) renders
empty rather than stale. Click a slot to run the same action its key would.

### Dialogs

Every dialog (error messages, confirmations, text prompts) is built on one keyboard-navigable
engine: `Tab`/`Shift+Tab` and arrow keys cycle focus between buttons, a button's underlined
letter activates it (bare, or `Alt+letter` even while a text field has focus), `Enter` activates
the default button, and `Esc` always cancels safely. Dialogs can stack.

### View Modes

    Brief   names only, laid out in as many columns as fit the panel width
    Full    name, size, modified date (with column headers)
    Wide    name, size (with column headers)

Directories show `<DIR>` in the size column. Long names truncate with `…` in the table; the
panel footer shows the item count, the live selection count and total size (`0 selected` when
empty), and the cursor row's full name. The passive panel's footer additionally shows a
free-space placeholder (not real disk-usage data yet).

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

### Persistence

Each panel's path, sort field/direction, and view mode, plus the global hidden-files toggle and
the panel split, are saved to `~/.config/mycom/state.db` (SQLite, WAL) and restored on the next
start — separate from `config.toml`, which is user-authored and never written by the app. Saves
are debounced (~500ms after a change) and flushed on quit. A saved panel path that no longer
exists falls back to its nearest existing ancestor, then `$HOME`. Deleting `state.db` is always
safe — the next start just uses `config.toml`'s defaults.


## Development

```bash
uv sync --all-groups          # install with dev deps
uv run pytest                 # run tests
uv run ruff check mycom/      # lint
uv run mkdocs serve           # build & serve docs
```


## License

MIT
