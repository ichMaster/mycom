# Phase 0 (MVP) — Feature Specifications

Companion to [PYTHON_TUI_PRODUCT_SCOPE.md](PYTHON_TUI_PRODUCT_SCOPE.md). Details every Phase 0 feature: expected functionality, UI, and acceptance criteria. Phase 2 is specified in [PYTHON_TUI_PHASE2_SPEC.md](PYTHON_TUI_PHASE2_SPEC.md).

**Conventions**
- Key notation: `F5`, `Ctrl+U`, `Shift+F6`, `Alt+F4`. Defaults deliberately mirror Far Manager for muscle-memory compatibility.
- "Active panel" = panel with the cursor; "passive panel" = the other one.
- Target platforms for MVP: macOS + Linux first-class; Windows best-effort (conpty).
- UI framework: Textual; async event loop owns all UI mutation (single-writer rule).

**Global MVP acceptance criteria (apply to every feature)**
- [ ] Every function is reachable with keyboard only; mouse is optional everywhere.
- [ ] No user data is ever lost by a failed or cancelled operation (source files untouched until the operation completes).
- [ ] UI never freezes: any operation > 100 ms runs async with visible progress or spinner.
- [ ] Works in 80×24 minimum terminal; truecolor with 256-color fallback.
- [ ] Cold start < 500 ms to interactive panels on a warm FS cache.

---

## Main screen reference layout

```
┌ /home/user/projects ──────────────┐┌ /home/user/downloads ─────────────┐
│ Name              Size    Date    ││ Name              Size    Date    │
│ ..                                ││ ..                                │
│▌src               <DIR>  02.08.26▐││ image.png        1.2 MB  01.08.26 │
│ tests             <DIR>  30.07.26 ││ notes.md         3.4 KB  29.07.26 │
│ README.md         2.1 KB 28.07.26 ││                                   │
│                                   ││                                   │
│ src                               ││ 2 files, 1.2 MB                   │
└ 3 items, 1 selected (2.1 KB) ─────┘└───────────────────────────────────┘
/home/user/projects $ █
 1Help  2Menu  3View  4Edit  5Copy  6RenMov 7MkDir 8Delete 9Menu  10Quit
```

---

## F0.1 Dual-panel layout & navigation

**Expected functionality**
- Two vertical panels, 50/50 split, each showing an independent directory.
- `Tab` switches active panel; `Ctrl+U` swaps panel contents; `Ctrl+O` temporarily hides panels to show the underlying command/console screen (toggle).
- `Enter` on a directory enters it; `Enter` on `..` (always first entry) goes up; `Ctrl+PgUp` also goes up. Cursor lands on the directory you came from when going up.
- Panel title shows current path, middle-truncated when too long.
- Both panels refresh their listing on regaining focus after an external command.

**UI**
- Active panel: bright frame + visible cursor bar; passive panel: dim frame, no cursor bar.
- Cursor bar = inverse-video full row. `..` row rendered like a normal dir.
- Footer line inside each panel: item count, selection summary.

**Acceptance criteria**
- [ ] App starts with both panels on CWD; `Tab` moves focus, visually unambiguous which panel is active.
- [ ] Entering and leaving a directory always restores cursor position on the child dir when going up.
- [ ] A directory with 10,000 entries lists and scrolls with no perceptible lag (< 100 ms per navigation action).
- [ ] `Ctrl+U` swaps paths, cursor positions and selections of both panels.
- [ ] Unreadable directory (EACCES) shows an error dialog and stays in the previous directory.

## F0.2 File list & column views

**Expected functionality**
- Three view modes per panel: **Brief** (names in 2–3 columns), **Full** (name / size / mtime), **Wide** (name / size). `Ctrl+1`=Brief, `Ctrl+2`=Full, `Ctrl+3`=Wide; persisted per panel.
- Directories show `<DIR>` in the size column; sizes human-readable (KB/MB/GB, one decimal).
- Symlinks marked (arrow suffix or color); broken symlinks visually distinct.
- Long names truncated with `…`; full name visible in panel footer for the cursor row.

**UI**
- Column headers rendered in Full/Wide modes; header of the active sort column highlighted with sort direction glyph (`▲`/`▼`).

**Acceptance criteria**
- [ ] Each of the three modes renders correctly at 80 and at 200 columns width.
- [ ] View mode survives restart (persistence, F0.16).
- [ ] mtime shown in local time, `DD.MM.YY HH:MM` (format constant for MVP).
- [ ] Broken symlink neither crashes listing nor stat-fails the whole directory.

## F0.3 Sorting

**Expected functionality**
- Modes: name (default), extension, size, mtime. Keys: `Ctrl+F3` name, `Ctrl+F4` ext, `Ctrl+F6` size, `Ctrl+F5` mtime (Far defaults). Pressing the active mode's key again toggles ascending/descending.
- Directories always group before files (both honoring sort direction within their group). `..` always first.
- Sort is stable and locale-independent (casefold + codepoint tiebreak) for MVP.

**Acceptance criteria**
- [ ] Each mode orders a mixed fixture directory exactly as specified in unit tests (incl. unicode names).
- [ ] Toggling direction inverts file order but keeps dirs-first grouping and `..` on top.
- [ ] Active sort mode + direction visible in the panel (header glyph) and persisted per panel.

## F0.4 Selection model

**Expected functionality**
- `Ins` toggles selection of cursor row and moves cursor down. `Gray +` / `Gray -` (with fallback `Alt+=` / `Alt+-` for keyboards without a numpad) open select/deselect-by-mask dialogs (`*.py;*.md` glob list). `Gray *` (fallback `Alt+8`) inverts selection.
- `..` can never be selected.
- All file operations (F5/F6/F8) act on the selection when non-empty, otherwise on the cursor file. After a successful operation the processed entries are deselected.

**UI**
- Selected rows in yellow (Far classic); panel footer: `N selected (X MB)`.
- Mask dialogs: single input field, `Enter`=apply, `Esc`=cancel.

**Acceptance criteria**
- [ ] Select 3 files with `Ins`, press `F8` — confirmation names "3 files", all 3 deleted, selection cleared.
- [ ] `+` with `*.py` selects exactly the matching files (case-insensitive on all platforms for MVP).
- [ ] Invert never selects `..`.
- [ ] Selection is per-panel and survives sort/view-mode changes, but resets on directory change.

## F0.5 Hidden files toggle

**Expected functionality**
- `Ctrl+H` toggles visibility of hidden entries: dotfiles on POSIX; hidden attribute on Windows. Global (both panels), persisted.

**Acceptance criteria**
- [ ] Toggle updates both panels immediately; state survives restart.
- [ ] Cursor stays on the same file after toggle if it is still visible, otherwise moves to nearest neighbor.

## F0.6 Copy / Move (F5 / F6)

**Expected functionality**
- `F5` copies selection/cursor to a target path pre-filled with the passive panel's directory (editable). `F6` moves. Recursive for directories. `shutil.copystat`-level metadata preservation (mtime, permissions).
- Symlinks are copied as symlinks (not followed) in MVP.
- Move within one filesystem = `rename()` (instant); cross-device move = copy + verified delete of source (source deleted only after its copy fully succeeded).
- Progress dialog with per-file and total progress, bytes copied, speed, ETA; `Esc` cancels after finishing the current chunk. Cancel leaves already-copied files in place, never corrupts source.
- Conflicts delegate to F0.10.

**UI**
```
┌─ Copy ────────────────────────────────────────────┐
│ Copying "video.mp4"                               │
│ to /mnt/backup/video.mp4                          │
│ [██████████████░░░░░░░░░░░░░░]  47%               │
│ Total: 3 of 12 files, 1.4 GB of 3.0 GB            │
│ [████████░░░░░░░░░░░░░░░░░░░░]  46%               │
│ Speed 112 MB/s   Elapsed 00:13   ETA 00:15        │
│                    [ Cancel ]                     │
└───────────────────────────────────────────────────┘
```
- Initial dialog: one input (target path) + `[ Copy ] [ Cancel ]`; title says `Copy "name"` or `Copy 5 files`.

**Acceptance criteria**
- [ ] Copying a 1 GB tree completes with byte-identical content and preserved mtimes; totals in the dialog match `du`.
- [ ] UI remains responsive (panel redraw, cancel reachable) throughout a large copy.
- [ ] Same-FS `F6` of a large directory is instantaneous (rename), no progress dialog flicker.
- [ ] Cancelled cross-device move: source fully intact; partial target reported.
- [ ] Copy onto itself / into its own subdirectory is detected and refused with a clear error.
- [ ] Passive panel refreshes and shows new files when the operation completes.

## F0.7 Mkdir (F7)

**Expected functionality**
- `F7` opens a name dialog; supports nested creation (`a/b/c` creates all levels). On success the active panel refreshes and the cursor lands on the new (top-level) directory.

**Acceptance criteria**
- [ ] Nested path creates the full chain; existing directory → clear error, dialog stays open for correction.
- [ ] Cursor is on the newly created directory afterwards.
- [ ] Invalid characters / permission errors reported without crashing.

## F0.8 Delete (F8)

**Expected functionality**
- `F8` deletes selection/cursor **permanently** after confirmation (trash integration is Phase 1; the dialog says "Delete" and MVP release notes state this). Recursive for directories with a second, stronger confirmation ("Directory is not empty").
- Progress dialog with cancel for large trees (same shell as F0.6).

**UI**
- Confirmation: `Delete "name"?` or `Delete 5 files?`, buttons `[ Delete ] [ Cancel ]`, `Delete` focused, red accent title.

**Acceptance criteria**
- [ ] Single file, multiple selection, and non-empty directory paths all behave per spec, with the extra confirmation for non-empty dirs.
- [ ] `Esc`/Cancel anywhere aborts with files not yet processed left intact.
- [ ] Read-only file prompts (`Delete read-only file?`) instead of failing silently.
- [ ] Cursor moves to the next surviving entry after deletion.

## F0.9 Rename (Shift+F6)

**Expected functionality**
- `Shift+F6` renames the cursor file in place: dialog pre-filled with current name, name stem pre-selected. `F6` with an edited same-directory target achieves the same via the move path.

**Acceptance criteria**
- [ ] Rename to existing name triggers the conflict dialog (F0.10), not an exception.
- [ ] Cursor follows the renamed entry (in its new sort position).
- [ ] Works on directories.

## F0.10 Conflict resolution dialog

**Expected functionality**
- Raised by copy/move/rename when the target exists. Shows both files' size and mtime, marks the newer one. Choices: **Overwrite**, **Skip**, **Rename** (input for a new target name), **Overwrite All**, **Skip All**, **Cancel**. "All" answers persist for the rest of the operation.

**UI**
```
┌─ File exists ─────────────────────────────────────┐
│ Target "report.pdf" already exists                │
│   new:      1.2 MB  02.08.2026 14:11              │
│   existing: 1.1 MB  30.07.2026 09:02              │
│ [Overwrite] [Skip] [Rename] [Overw.All] [Skip All]│
│                  [ Cancel ]                       │
└───────────────────────────────────────────────────┘
```

**Acceptance criteria**
- [ ] Each of the six choices behaves per spec in a scripted 10-conflict copy.
- [ ] Directory-over-directory conflict merges contents (per-file conflicts surface individually); file-over-directory and directory-over-file are refused with explanation.
- [ ] "All" choices are scoped to the current operation only.

## F0.11 Command line, execution & cd-sync

**Expected functionality**
- Single-line prompt under the panels showing active panel's CWD. Printable characters always type into the command line (Far behavior); panel keeps navigation keys.
- `Enter` executes via the user's shell (`$SHELL -c` / `cmd /c`) in a PTY: the UI switches to a full-screen console surface streaming live output; interactive/TUI programs (vim, htop, git rebase -i) work. When the process exits, a `Press any key` line appears (skipped if the command produced no output), then panels return and both refresh.
- Process CWD = active panel directory; changing active panel directory updates the prompt.
- `cd <path>` (and bare `cd`, `cd -` optional) is intercepted: changes the active panel directory without spawning a shell. Quoted paths and `~` supported.
- Non-zero exit code is shown (`Exit code: 2`) above the restored panels in the console history.

**Acceptance criteria**
- [ ] `ls -la` / `dir` executes in the active panel dir and its output is readable before returning.
- [ ] `vim file` opens full-screen, edits, exits cleanly back to panels; panels show the modified file's new mtime.
- [ ] `cd /tmp` changes the active panel with no subprocess spawned; `cd nonexistent` reports an error inline.
- [ ] `Ctrl+O` recalls the last console output after returning to panels.
- [ ] A command printing 100k lines does not hang or exhaust memory (output ring buffer).

## F0.12 Viewer (F3)

**Expected functionality**
- `F3` opens the cursor file read-only, instantly regardless of size (windowed reads / mmap; never loads the whole file).
- MVP decoding: UTF-8 with `errors="replace"`, latin-1 fallback for invalid files (auto-detect arrives P1). Binary files render with replacement chars — usable, not pretty (hex mode is P1).
- Keys: arrows/PgUp/PgDn/Home/End scroll; `End` jumps to EOF instantly; `F2` toggles wrap; `F6` switches to editor; `F3`/`F10`/`Esc` close.
- Status bar: filename, size, current offset and percent.

**Acceptance criteria**
- [ ] 1 GB log opens in < 300 ms; `End` reaches EOF in < 300 ms; RSS growth stays bounded (< 100 MB) while paging through it.
- [ ] Wrap toggle preserves the top visible line's file position.
- [ ] File modified externally while viewing: viewer keeps working (stale window is acceptable; no crash).
- [ ] `F6` opens the same file in the editor at top of file, closing the viewer.

## F0.13 Editor (F4)

**Expected functionality**
- `F4` opens the cursor file in the built-in editor (Textual `TextArea` based): editing, `Ctrl+Z` undo / `Ctrl+Shift+Z` redo, `F2` save, `Shift+F2` save-as, `Esc`/`F10` close with "Save changes?" guard when modified.
- MVP encoding: UTF-8 (refuses undecodable files with a "binary file" message pointing at the viewer). Original EOL style (LF/CRLF, incl. mixed dominant) detected on open and preserved on save; trailing-newline state preserved.
- `Alt+F4` opens the file in `$EDITOR` (suspend TUI → run → resume → refresh panels). Config flag `editor.external_default` makes `F4` do this.
- Guard: file changed on disk since open → warn before overwriting on save.
- MVP size limit: files > 10 MB are redirected to the viewer with a notice.

**UI**
- Status bar: name, modified flag `*`, line:col, EOL style. Editor key bar (F2 Save … F10 Quit).

**Acceptance criteria**
- [ ] Open→edit→save roundtrip on a CRLF file keeps CRLF endings and produces no spurious diff beyond the edit.
- [ ] Undo/redo chain of ≥ 50 operations replays correctly.
- [ ] Quitting with unsaved changes always prompts (Save / Discard / Cancel); Cancel returns to editing.
- [ ] External `$EDITOR` roundtrip works in tmux and plain terminals; panels reflect changes after return.
- [ ] Concurrent-modification guard fires when the file was touched externally.

## F0.14 Key bar

**Expected functionality**
- Bottom row with 10 labeled slots (`1Help 2Menu 3View …`), context-sensitive: panels, viewer, editor, and dialogs each set their own labels. Labels update live while `Ctrl`/`Shift`/`Alt` is held where the terminal reports modifier state; otherwise base labels stay.
- Mouse click on a slot triggers the corresponding key.

**Acceptance criteria**
- [ ] Labels match actual bindings in each context (generated from the keymap — no drift possible).
- [ ] Unassigned slots render empty, not stale.
- [ ] Clicking `5Copy` starts a copy exactly like pressing `F5`.

## F0.15 Dialog engine & theme

**Expected functionality**
- Reusable modal dialog kit: framed window, title, text, input fields, button row. `Tab`/arrows cycle focus, highlighted hotkey letters (`Alt+letter` or bare letter when no input focused), `Enter` = default button, `Esc` = cancel. Dialogs stack (a dialog can open an error dialog).
- Theme: "Far classic" palette (blue panels, cyan frames, grey dialogs, yellow selection) as the default; colors defined in one theme file — no hard-coded colors anywhere.

**Acceptance criteria**
- [ ] All Phase 0 dialogs are built on this kit (audit: zero ad-hoc modal code).
- [ ] Fully keyboard-navigable; focus order deterministic; `Esc` always cancels safely.
- [ ] Renders correctly on truecolor and 256-color terminals, light-terminal safe (no invisible text).

## F0.16 Persistence (SQLite)

**Expected functionality**
- Single SQLite DB (WAL mode) at the platform config dir (`~/.config/<app>/state.db`, `%APPDATA%\<app>\state.db`). Stored in MVP: per-panel path, sort mode+direction, view mode; hidden-files toggle; last window state. Schema versioned with migrations; history tables created (filled from P1).
- Writes debounced; final flush on exit. Corrupt/missing DB → recreate with defaults, never block startup.

**Acceptance criteria**
- [ ] Kill-9 during use loses at most the last few seconds of state, never corrupts the DB (WAL).
- [ ] Restart restores both panels' paths, sort and view modes, hidden toggle.
- [ ] Deleting the DB yields clean defaults on next start.
- [ ] A panel path that no longer exists falls back to the nearest existing ancestor, then `$HOME`.

## F0.17 LLM provider configuration & offline degradation

**Expected functionality**
- Credentials resolved from `ANTHROPIC_API_KEY` env, else OS keychain entry set via an in-app command; never stored in plaintext config. Model configurable, default `claude-opus-5`; requests use streaming and adaptive thinking defaults.
- **Architectural rule:** the app is 100 % functional without a key or network. AI entry points, when unconfigured, show a one-time setup dialog (how to set the key) instead of erroring. No network traffic unless an AI feature is explicitly invoked.

**Acceptance criteria**
- [ ] With no key: every non-AI feature works; invoking AI shows the setup dialog, not a traceback.
- [ ] With an invalid key: authentication error surfaced as a friendly dialog with fix instructions.
- [ ] tcpdump during a non-AI session shows zero outbound calls from the app.
- [ ] Key set via keychain path is used on next AI invocation without restart.

## F0.18 AI command palette

**Expected functionality**
- `Ctrl+Space` opens a palette: user types intent in natural language ("find all files over 100MB modified this week"). The app calls the Anthropic API (streaming, structured output) with context: OS, shell, CWD, selected file *names*, truncated listing of the active panel — never file contents in MVP.
- Response renders as: proposed shell command + one-line explanation + danger level. Dangerous patterns (recursive delete, chmod -R, dd, sudo, pipe-to-shell) are flagged red with an explicit extra warning.
- Actions: **Run** (executes via F0.11 pipeline), **Edit** (inserts into command line for manual editing), **Copy**, **Cancel**. **A generated command is never executed without one of these explicit user actions.**
- API errors (network, rate limit, refusal) shown inline in the palette; palette remains usable to retry or cancel.

**UI**
```
┌─ AI Command ──────────────────────────────────────────────┐
│ > archive all logs older than 30 days into logs.tar.gz    │
│ ───────────────────────────────────────────────────────── │
│ find . -name '*.log' -mtime +30 -print0 |                 │
│   tar --null -czf logs.tar.gz --files-from=-              │
│ Archives matching logs into logs.tar.gz (files kept).     │
│ ⚠ none                                                    │
│      [ Run ]  [ Edit ]  [ Copy ]  [ Cancel ]              │
└───────────────────────────────────────────────────────────┘
```

**Acceptance criteria**
- [ ] 10-case golden set (list/find/archive/rename/git tasks) produces commands that run correctly in the active panel's context.
- [ ] Nothing executes without an explicit Run; `Esc` at any point runs nothing.
- [ ] A destructive request ("delete everything here") produces the red danger warning before Run is possible.
- [ ] Streaming: first tokens visible < 2 s on a normal connection; palette can be cancelled mid-stream.
- [ ] Offline: clear inline error within the timeout, app fully usable afterwards.
- [ ] Selected file names appear correctly in generated commands (quoting/spaces handled).

## F0.19 "Open Claude Code here"

**Expected functionality**
- Menu entry + key (default `Ctrl+K`, then `C`; also in F9 menu) launches the `claude` CLI in the **active panel's directory**: TUI suspends, `claude` runs attached full-screen in the same terminal, on exit the TUI resumes and both panels refresh (agent likely changed files).
- Binary discovery on `PATH`; if absent, a dialog explains how to install Claude Code (link to docs) — no crash, no dead menu item.
- Config option to launch in an external terminal window instead (macOS Terminal/iTerm, `$TERMINAL` on Linux).

**Acceptance criteria**
- [ ] Session starts in the correct directory (verified by `pwd`-style check inside Claude Code).
- [ ] Full interactive session works: colors, resize, Ctrl+C handled by `claude`, not the host app.
- [ ] On exit, panels show files created/modified during the session without manual refresh.
- [ ] `claude` not installed → informative dialog; app state unaffected.
- [ ] Works under tmux and plain terminal on macOS and Linux.

---

## Out of MVP (explicitly deferred to Phase 1+)
Trash-aware delete, histories UI, quick search, highlighting groups, drives/locations menu, auto-refresh watcher, hex viewer, encodings menu, editor/viewer search, syntax highlighting, archives, clipboard integration, find file, chat sidebar, headless Claude runner / Agent SDK embedding.
