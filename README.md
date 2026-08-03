```
 ╔══════════════════════════════════════════════════════════╗
 ║                        MyCom                            ║
 ║        Dual-Panel File Manager for the Terminal         ║
 ║                      v0.6.0                             ║
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
    Far classic theme        one palette file drives every color; renders on truecolor and
                              256-color terminals
    Dialog kit                keyboard-navigable modals: Tab/arrows/hotkeys/Enter/Esc, stackable
    Key bar                  F1-F10 labels generated from the keymap (never drifts); clickable
    Structured logging       env-configurable, file-based (never stdout — owns the terminal)
    File operations          Copy/Move (F5/F6, same-FS instant rename, cross-device verified
                              copy+delete), Mkdir (F7), Delete (F8), Rename (Shift+F6) — worker
                              thread, live progress, Cancel, a six-choice conflict dialog
    Command line & console   type to run a shell command in a real PTY (vim/htop work); cd
                              intercepted with no subprocess; Ctrl+O recalls the last output
    Viewer (F3)              instant open at any size (windowed, never loads a file whole),
                              wrap toggle, F6 hands off to the editor
    Editor (F4)              TextArea-based, undo/redo, EOL and trailing-newline preserved on
                              save, a modified-close guard, an external-change guard, binary/
                              oversized files redirect to the viewer; Alt+F4 (or config) opens
                              $EDITOR instead
    AI palette, Claude Code integration — coming in later v0 phases (see spec/roadmap.md)


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
 Ctrl+O         Recall last output     F10, Ctrl+Q     Quit

 File operations                       Selection
 ──────────────────────────────        ──────────────────────────────
 F5             Copy                   Ins, Space     Toggle cursor entry, move down
 F6             Move                   + (Alt+=)      Select by mask (e.g. *.py;*.md) —
 Shift+F6       Rename (in place)                      default "*" selects all
 F7             Mkdir                  - (Alt+-)      Deselect by mask
 F8             Delete                 * (Alt+8)      Invert selection

 Viewer (F3)                           Editor (F4)
 ──────────────────────────────        ──────────────────────────────
 ↑/↓, PgUp/PgDn Scroll by line/page    F2             Save
 Home/End       Jump to start/end      Shift+F2       Save as
 F2             Toggle wrap            F10, Esc       Quit (prompts if modified)
 F6             Open in editor         Alt+F4         Open in $EDITOR instead
 F3, F10, Esc   Quit
```

Going up restores the cursor onto the directory you just left. Pressing the active sort key
again reverses direction — the panel header shows a `▲`/`▼` glyph on the active sort column
(Full/Wide modes only; Brief has no per-file headers). An unreadable, vanished, or replaced
directory shows an error dialog instead of a silent empty panel.

### Selection

`Ins`/`Space` toggle the cursor entry and advance; `..` can never be selected. Selected rows
render in yellow. Mask select/deselect (`+`/`-`) prompt for a pattern (default `*`, so `+` then
`Enter` selects everything); `*` inverts the current selection. Selection is per-panel, survives
sort/view-mode changes and refreshes, and clears when you navigate to a different directory. If a
selected file is replaced on disk by something else under the same name between refreshes, it's
dropped from the selection rather than silently carrying over to the new file. It's the input
file operations act on: selection-else-cursor (act on the selection if there is one, else the
cursor entry).

`F1` (help) is already bound in the keymap registry but has no handler yet — it arrives with the
AI command palette (v0.7).

### File Operations

`F5` Copy and `F6` Move prompt for a target directory (pre-filled with the passive panel's
path); a plain `Shift+F6` Rename prompts in place with the name's stem pre-selected for
overtyping (`report.txt` → `report` highlighted; a leading dot doesn't count, so `.gitignore`
selects the whole name). `F7` Mkdir accepts a nested `a/b/c` path in one step. `F8` Delete asks
to confirm (skippable via `confirm_delete = false`, see Configuration), with an unskippable
second confirmation for any non-empty directory and an individual prompt for each read-only
file in the batch.

Every operation runs on a background thread — the UI stays responsive, and a real **Cancel**
button appears on any operation large enough to show progress (bytes/files done, speed, ETA).
Same-filesystem moves and renames are an instant `rename()` with no progress dialog; a
cross-device move copies then verifies before deleting the source, never the reverse. A name
collision opens a six-choice dialog (Overwrite / Skip / Rename / Overwrite All / Skip All /
Cancel) — "All" answers apply for the rest of that one operation only. Deletion is permanent;
there is no trash/recycle-bin integration yet.

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

### Command Line & Console

A prompt under the panels always shows the active panel's directory. Typing any character not
claimed by a panel keybinding goes straight there (FAR behavior) — press `Enter` to run it.

`cd <path>` (quoted paths and `~` supported, bare `cd` goes home) is intercepted and applied
directly to the active panel — no subprocess. Anything else runs in a real PTY: the app hands
over the whole terminal, so interactive programs (`vim`, `htop`, `git rebase -i`) get full
control exactly as they would in a normal shell. When the command exits, `Press any key` is shown
(skipped if it printed nothing) along with `Exit code: N` for a non-zero exit, then both panels
refresh — an external command can change either side.

`Ctrl+O` recalls the last command's output (or "No output yet") without re-running anything; any
key returns to the panels.

### Viewer

`F3` opens the cursor file read-only, instantly at any size — it's windowed (mmap-backed) and
never loads a file whole, so a multi-gigabyte log opens and jumps to `End` just as fast as a
one-line file. Arrows/`PgUp`/`PgDn`/`Home`/`End` scroll by line or page; `F2` toggles line wrap,
preserving your position exactly (tracked by file offset, not by on-screen row, so re-wrapping
never loses your place). `F6` switches to the editor on the same file, at the top. `F3`, `F10`, or
`Esc` closes back to the panels. A file modified on disk while you're viewing it keeps working — a
stale window is fine, it just won't live-update.

### Editor

`F4` opens the cursor file in a `TextArea`-based editor with full undo/redo (`Ctrl+Z`/`Ctrl+Y`).
`F2` saves, `Shift+F2` saves as (and keeps editing the new path). Line endings (LF/CRLF, including
a mixed file's dominant style) and the presence or absence of a trailing newline are detected on
open and preserved byte-for-byte on save — editing a CRLF file never turns into a wall of spurious
diff noise. Quitting with unsaved changes always asks: Save / Discard / Cancel. If the file was
changed on disk by something else since you opened it, saving warns before overwriting — declining
loses nothing on either side, in memory or on disk. A binary file, or one over 10 MB, opens in the
viewer instead (UTF-8 text only, capped size — a deliberate scope boundary, not a bug).

`Alt+F4` skips MyCom's own editor and hands the cursor file straight to `$EDITOR` (falling back to
`vi`), suspending the app exactly like running a shell command does — real full-screen control,
same as the command line. Setting `external_default = true` under `[editor]` in `config.toml`
makes plain `F4` do this too, for anyone who'd rather always use their own editor.

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
confirm_delete = true           # false skips F8's routine "Delete X?" prompt only —
                                 # the non-empty-dir/read-only-file warnings always show
default_sort = "name"           # name | extension | date | size — invalid values
default_sort_direction = "asc"  # fall back to "name" with a logged warning
                                 # "asc" | "desc"

[keybindings]
copy = "f5"
move = "f6"
delete = "f8"
quit = "f10"

[editor]
external_default = false        # true: plain F4 always opens $EDITOR instead of the built-in editor

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
