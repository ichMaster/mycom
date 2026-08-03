# Key Bindings

Every binding is resolved through one keymap registry (`mycom/keymap.py`): a `Command`
dataclass maps `action -> key(s) -> context -> label -> slot`. `mycom/app.py` builds Textual's
runtime bindings from this registry (`App.bind`) instead of hard-coding key strings, and the key
bar (below) is generated from the same registry's `slot` field — the F9 menus (v1.8) will be
too — so labels can never drift from actual bindings.

Three actions (`switch_panel`, `open`, `go_up`) are handled in `MyComApp.on_key` instead of
`App.bind`, because they must intercept the key before Textual's own widget-level bindings see
it — the focused `DataTable` already claims `enter` for its own cursor-select action, and `Tab`
is the framework's default focus-cycling key. `on_key` also has a fourth, non-action branch
(v0.5): any key that reaches it *not* claimed by a keymap action and classified `is_printable` by
Textual routes to the command line instead of the panel — see
[Command line and console](#command-line-and-console-v05).

## Implemented

| Key | Action | Behavior |
|-----|--------|----------|
| `Tab` | `switch_panel` | Switch the active panel |
| `Enter` | `open` | Enter a directory, or go up on `..` |
| `Backspace` | `go_up` | Go to the parent directory |
| `Ctrl+PageUp` | `go_up` | Go to the parent directory (alias) |
| `Ctrl+U` | `panel_swap` | Swap both panels' paths and cursor positions |
| `Ctrl+Right` | `resize_grow` | Grow the active panel (30% → 50% → 70%) |
| `Ctrl+Left` | `resize_shrink` | Shrink the active panel (70% → 50% → 30%) |
| `Ctrl+1` | `view_brief` | Brief view mode (names only, multi-column) |
| `Ctrl+2` | `view_full` | Full view mode (name/size/modified) |
| `Ctrl+3` | `view_wide` | Wide view mode (name/size) |
| `Ctrl+F3` | `sort_name` | Sort by name |
| `Ctrl+F4` | `sort_ext` | Sort by extension |
| `Ctrl+F5` | `sort_mtime` | Sort by modified date |
| `Ctrl+F6` | `sort_size` | Sort by size |
| `Insert`, `Space` | `select_toggle` | Toggle the cursor entry's selection, move cursor down |
| `Plus` (`Alt+=`) | `select_mask` | Select by mask (prompt, default `*`) |
| `Minus` (`Alt+-`) | `deselect_mask` | Deselect by mask (prompt) |
| `Asterisk` (`Alt+8`) | `select_invert` | Invert the current selection |
| `Ctrl+H` | `toggle_hidden` | Toggle hidden-file visibility, both panels |
| `Ctrl+O` | `toggle_console` | Recall the last command's output |
| `F3` | `view` | Open the cursor file read-only in the viewer |
| `F4` | `edit` | Open the cursor file in the editor (or `$EDITOR`, see below) |
| `Alt+F4` | `edit_external` | Open the cursor file in `$EDITOR`, always |
| `F5` | `copy` | Copy selection-else-cursor to a prompted target directory |
| `F6` | `move` | Move selection-else-cursor to a prompted target directory |
| `Shift+F6` | `rename` | Rename the cursor entry in place, stem pre-selected |
| `F7` | `mkdir` | Create a directory (accepts a nested `a/b/c` path) |
| `F8` | `delete` | Delete selection-else-cursor, permanently |
| `F10`, `Ctrl+Q` | `quit` | Quit |

Notes:

- Going up (`Backspace`/`Ctrl+PageUp`) restores the cursor onto the directory you just left; if
  that entry is gone, the cursor falls back to the first row.
- `Ctrl+U` swaps paths, cursor positions, **and** each panel's selection.
- Pressing the active sort key again reverses direction. The panel header shows a `▲`/`▼` glyph
  on the sorted column in Full/Wide modes (Brief has no per-file headers, so no glyph).
- Resize, view-mode, sort, and the hidden toggle persist across restarts as of v0.3 (see
  [Configuration](configuration.md#persistence)) — no longer in-memory only.
- The registry's key identifiers for `+`/`-`/`*` are the Textual names `"plus"`/`"minus"`/
  `"asterisk"`, not the literal symbol characters — binding to the literal symbol silently never
  matches (confirmed live against a running app; a real gotcha hit while wiring these up).

## Selection

`FileBrowserPanel._selected: set[str]` (bare filenames) is per-panel: `Ins`/`Space` toggle the
cursor entry and advance (`..` is never selectable); `+`/`-` open an `InputDialog` prompting for a
`;`/`,`-separated case-insensitive glob-list (`mycom/utils/masks.py::match_any` — a minimal
subset of what v1.1's shared masks engine will generalize to) and add/remove every match; `*`
inverts. There's no dedicated select-all key — `+` with its pre-filled default pattern `*` and
`Enter` selects everything. Selection survives sort/view-mode changes and clears on a successful
directory navigation. Selected entries render in `$selected-fg` yellow (a literal hex imported
from `mycom/theme.py`, since Rich markup needs a real color, not a CSS variable) in all three view
modes. `FileBrowserPanel.get_selected_files()` returns the selection if non-empty, else the
cursor file — "selection-else-cursor", sorted (not raw `set` order, so multi-file operation
order — and thus what a mid-operation cancel leaves behind — is deterministic). File operations
(below) are its consumer.

## File operations (v0.4)

`mycom/fileops/` (`plan.py`, `policy.py`, `engine.py`) is the plan → execute engine every
operation below drives from `mycom/app.py`, on a `run_worker(thread=True)` background thread —
the UI thread is never blocked, and `OpProgress`/dialog updates are marshalled back via
`call_from_thread`.

- **`F5` Copy / `F6` Move** — `InputDialog` prompts for a target directory, pre-filled with the
  passive panel's path. `build_plan` walks the selection-else-cursor sources into a flat
  `PlanEntry` list; a copy or move onto itself, into its own subdirectory, or in place with the
  same name is refused before any I/O. Move takes the instant `os.rename()` path when every entry
  is on the same filesystem (`same_filesystem`, `st_dev`-based) — no progress dialog for what's
  effectively free; a cross-device plan copies each file in 1 MiB chunks and only unlinks the
  source once the destination's size is verified to match (`move_entry`), with the same
  progress/Cancel UI as copy.
- **`Shift+F6` Rename** — an `InputDialog` variant (`select_stem=True`) pre-selects the name's
  stem (up to the last `.`; a leading dot doesn't count, so `.gitignore` selects the whole name)
  for immediate overtyping. Always same-directory, so always the instant-rename path; a name
  collision goes through the same six-choice dialog as copy/move, never raising.
- **`F7` Mkdir** — `Path.mkdir(parents=True)` creates a nested `a/b/c` chain in one step (only the
  leaf can collide); an existing-name collision re-opens the same prompt, pre-filled, once the
  error is dismissed. Cursor lands on the new top-level segment.
- **`F8` Delete** — a confirmation ladder: the routine "Delete X?" prompt (skippable via
  `confirm_delete = false`, see [Configuration](configuration.md)), then an unskippable "not
  empty, delete anyway?" for every non-empty directory in the selection, then an individual
  "delete read-only file?" for every read-only file the walked plan touches (declining excludes
  just that file, not the whole batch). A progress dialog appears only for trees at or above 20
  files. The cursor moves to the next surviving entry, skipping past any row that's itself being
  deleted. Deletion is permanent — no trash/recycle-bin integration yet.
- **Conflicts** — a target that already exists opens `ConflictDialog`
  (`mycom/widgets/conflict_dialog.py`): Overwrite, Skip, Rename (swaps in an `Input` pre-filled
  with the conflicting name), Overwrite All, Skip All, Cancel. "All" answers are remembered for
  the rest of that one operation only (`mycom.fileops.engine._resolve_conflict`'s `sticky` state
  is local to a single `execute_plan` call) — a later, separate operation always asks again.
  Directory-over-directory merges silently (per-file conflicts inside it are asked individually);
  file-over-directory and directory-over-file are refused with a plain error, never offered the
  six-choice dialog.
- **Cancellation** — every operation's progress dialog carries a real **Cancel** button that
  signals a `CancelToken`; the worker checks it between chunks (copy/move) or before each entry
  (delete), so cancelling never leaves a source file it already fully processed in an
  inconsistent state. A cancelled cross-device move's per-file guarantee is "never lost, never
  duplicated": each file ends up exactly once, either still in the source or fully moved.
- **Crash safety** — any unexpected `OSError` during an operation (permission denied, disk full,
  a source vanishing mid-batch) shows a plain error dialog instead of propagating out of the
  worker thread — Textual's `run_worker` defaults to tearing down the whole app on an uncaught
  worker exception, so every operation's worker (and the main-thread plan-building step before
  it) catches `OSError` explicitly.

## Command line and console (v0.5)

`mycom/console/` (`cd.py`, `ring_buffer.py`, `pty_runner.py`) is a pure, Textual-free engine —
same shape as `fileops/` — that `mycom/widgets/command_line.py`'s `CommandLine` widget and
`mycom/app.py`'s wiring drive.

- **The prompt** always shows the active panel's directory (`CommandLine.set_cwd`, called at
  every navigation call site: Enter-into, Backspace-up, Tab-switch, Ctrl+U-swap, a typed `cd`).
  Any printable key `on_key` doesn't recognize as a bound action focuses the command line and
  inserts the character there instead of leaving it for the panel — real FAR behavior, not a
  quick-filter-while-browsing model (the pre-v0.5 docs briefly described an in-panel quick filter;
  that was never actually wired to a keypress, and typing now has a real, different destination).
- **`cd`** (`mycom/console/cd.py::parse_cd` — quoted paths, `~`, bare `cd` → `$HOME`; `cd -` is a
  literal target with no OLDPWD tracking, so it predictably reports "no such directory" rather
  than pretending to support history that isn't there) is intercepted and applied directly to the
  active panel. Relative targets resolve against the active panel's shown directory, never the
  MyCom process's own untouched OS-level cwd — that's the whole point of cd-sync.
- **Anything else** runs via `mycom/console/pty_runner.py::run_in_pty`: `App.suspend()` hands the
  real terminal to the command (stdlib `pty.spawn`, `cwd` applied as a `cd <dir> && <command>`
  shell wrapper — no `exec` prefix, since `exec` can't interpret shell syntax like pipes or loops,
  only launch one binary directly), so interactive programs (`vim`, `htop`, `git rebase -i`) get
  genuine full-screen control. Every chunk read from the child is teed into a `RingBuffer` (bounded
  at 100k lines, oldest evicted first) before being relayed to the real terminal unaltered.
- **On return**, a small screen shows `Press any key` (skipped if the command printed nothing) and
  `Exit code: N` for a non-zero exit; dismissing refreshes both panels (an external command can
  change either side) and returns focus to the active panel. An unexpected `OSError` or
  `SuspendNotSupported` (Textual's headless test driver can't actually suspend, confirmed by
  reading its source) shows a clean message instead of propagating.
- **`Ctrl+O`** shows the ring buffer's current text in a scrollable screen ("No output yet" if
  nothing has run this session) — pure recall, nothing re-executes.

## Viewer (v0.6)

`mycom/viewer/` (`buffer.py`, `screen.py`) — `ViewerBuffer` is a pure, mmap-backed engine (same
shape as `fileops`/`console`): it never indexes or loads a file whole, only scanning the byte
range a requested window needs, so a multi-gigabyte file opens and jumps to `End` in well under
300ms with bounded resident memory. `ViewerScreen` wires it into a real, full-screen (not modal)
`Screen`:

- **`F3`** opens the active panel's cursor file (a no-op on a directory); `F3`/`F10`/`Esc` all
  close it back to the panels.
- **Navigation** (arrows, `PgUp`/`PgDn`, `Home`/`End`) tracks position by *file offset*, never a
  line index — `F2`'s wrap toggle changes how many file-lines fit on screen, and offset-tracking
  is what lets it preserve the exact line you were looking at across the toggle.
- **`F6`** dismisses the viewer with an `"edit"` sentinel result; `MyComApp`'s callback
  interprets that and opens the same file in the editor at the top of file — the viewer never
  imports the editor module directly, avoiding a forward reference between the two.
- A file modified on disk while it's open in the viewer keeps working (a stale mmap window is
  explicitly acceptable — no live-reload in v0).

## Editor (v0.6)

`mycom/editor/` (`detect.py`, `screen.py`) — `detect.py` is pure logic: `detect_eol` (LF/CRLF,
including a mixed file's dominant direction with ties favoring LF), `has_trailing_newline`,
`apply_eol` (re-applies the detected style on save), `is_binary`/`too_large` (an 8KB-probe
heuristic and a 10MB cap), and `read_text`, which raises `NotEditableError(reason="binary"|
"too_large")` rather than ever silently mis-decoding. `EditorScreen` wraps a Textual `TextArea`
(`tab_behavior="focus"` — required for `F2`/`Shift+F2`/`F10`/`Esc` to reach the screen at all; the
`"indent"` variant's own key handling special-cases `Escape` to move focus instead of letting it
bubble):

- **`F4`** calls `read_text` first; a `NotEditableError` redirects to the viewer with a notice
  instead of ever loading the file. Undo/redo is `TextArea`'s own built-in `Ctrl+Z`/`Ctrl+Y`
  stack — no custom code needed.
- **`F2`** saves; EOL and trailing-newline state are explicitly re-applied (not left to
  incidental round-trip behavior), and the write passes `newline=""` so Python's own universal-
  newline translation can't double-convert text already converted to CRLF.
- **`Shift+F2`** saves as and continues editing the new path; the original file is untouched.
- **`F10`/`Esc`** close; a modified buffer always prompts Save/Discard/Cancel
  (`SaveDiscardCancelDialog`, a three-button `DialogKit` subclass — `ConfirmDialog`'s Yes/No is
  ambiguous between "discard" and "stay"). An unmodified buffer closes immediately.
- **The external-change guard**: the file's mtime is recorded at open and re-checked before every
  write (both `F2` and the close-guard's Save choice); a mismatch warns before overwriting —
  declining loses nothing on either side, in memory or on disk.
- **`Alt+F4`** (`edit_external`) hands the cursor file straight to `$EDITOR` (shell-word-split,
  so `EDITOR="code --wait"` works correctly; falls back to `vi`) via `App.suspend()` — the same
  mechanism the command line uses, not the PTY-tee machinery that exists to *capture* output this
  doesn't need to capture. `[editor] external_default = true` in `config.toml` makes plain `F4`
  do this too.

**Input isolation:** both `ViewerScreen` and `EditorScreen` set `self._modal = True` in
`__init__` — not to look like a dialog (they're still full-screen), but because
`Screen._modal_binding_chain` truncates Textual's key-binding resolution at the first modal node
it finds. Without it, a key neither screen recognizes (e.g. `Ctrl+O`, bound to `toggle_console` at
the panel level) bubbles past them and fires the panel-level action underneath while the
viewer/editor still looks like it's in control (code review #1, v0.6). A tempting-looking
alternative — stopping every `Key` message unconditionally in `on_key` — was tried and reverted:
it also silently broke `TextArea`'s own `Ctrl+Z`/`Ctrl+Y`/`F6`/`F7` bindings, since those resolve
via `App._on_key`'s binding check, which only runs once a key message reaches the App unstopped.

## Key bar

`mycom/widgets/status_bar.py`'s `StatusBar` renders the ten F1-F10 slots from
`Keymap.key_bar_slots(scope)` — each `Command` in the registry declares a `slot: int | None`
(FAR's F1-F10 convention; `None` for actions with no key-bar presence, e.g. `switch_panel` or the
sort/view/resize keys) **and** a `context` (`"panel"`, `"viewer"`, or `"editor"`). Each screen
constructs its own `StatusBar` with the matching `scope`, so the key bar's labels always match
what's actually open — panel labels never bleed into the viewer/editor and vice versa. A slot
with no assigned action in its context renders empty rather than a stale label. Clicking a slot
calls `App.run_action` with the same action name its key would; this only resolves for actions
`MyComApp` itself defines (every panel action, plus `F1`'s still-reserved no-op) — a viewer/editor
slot click currently has no click-target method on the App and is a silent no-op, same as any
other unmapped action name (`App.run_action` logs and returns `False` rather than raising).

## Dialogs

Every dialog (`mycom/widgets/dialog.py`) is a subclass of `DialogKit`, the one modal engine every
dialog builds on:

- `Tab`/`Shift+Tab` cycle focus through every focusable widget (Textual's default chain,
  including a text `Input` if the dialog has one).
- `Left`/`Up`/`Right`/`Down` cycle focus among the dialog's **buttons only** — they never land on
  an `Input`, so keyboard-only navigation can't get stranded there (an `Input`'s own arrow keys
  move the text cursor while it has focus, as expected).
- A button's hotkey letter (shown underlined) activates it: bare on a plain keypress when no
  `Input` is focused, or with `Alt+letter` unconditionally. Two buttons in the same dialog can't
  share a hotkey — `DialogKit` raises at construction if they do.
- `Enter` activates the dialog's default button; `Esc` always dismisses safely with a
  caller-supplied cancel value.
- Dialogs stack (Textual's native `ModalScreen` behavior) — a dialog can open another (e.g. an
  error) on top of itself.

## Overriding a binding

Any action name in the registry can be overridden in `config.toml`:

```toml
[keybindings]
copy = "ctrl+c"
quit = "ctrl+q"
```

An override for an action name that doesn't exist in the registry is silently ignored (same
behavior as the pre-registry `KeyBindings` class it replaced).
