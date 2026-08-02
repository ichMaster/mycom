# Phase 1 (First Public Release) — Feature Specifications

Companion to [PYTHON_TUI_PRODUCT_SCOPE.md](PYTHON_TUI_PRODUCT_SCOPE.md). Details every Phase 1 feature: expected functionality, UI, and acceptance criteria. Phase 0 is specified in [PYTHON_TUI_PHASE0_SPEC.md](PYTHON_TUI_PHASE0_SPEC.md), Phase 2 in [PYTHON_TUI_PHASE2_SPEC.md](PYTHON_TUI_PHASE2_SPEC.md).

**Entry criteria:** all Phase 0 acceptance criteria green (dual panels, F5–F8 ops, command line, basic viewer/editor, dialog kit, SQLite persistence, AI palette, "Open Claude Code here").

**Phase goal:** the quality bar of a first public release — the product a Far Manager user can adopt as a daily driver, plus the AI/Claude layer that no other file manager has.

Conventions as in Phase 0 (Far-compatible default keys; keyboard-first; async UI; every feature reachable without mouse).

---

# A. Panels & Navigation

## F1.1 Quick search (type-to-jump)

**Expected functionality**
- `Alt+<letter>` starts incremental search in the active panel; further typed characters narrow the match; cursor jumps to the first matching entry, `Ctrl+Enter` cycles to the next match. `Backspace` shortens the pattern; `Esc`/navigation key exits.
- Matching: case-insensitive prefix match by default; `*` allowed inside the pattern (mask semantics from F1.20).

**UI**
- Small overlay box at the bottom of the panel frame: `Search: rep█`, match count `(3)`. No layout shift.

**Acceptance criteria**
- [ ] Typing `Alt+r`, `e` lands on the first `re…` entry; `Ctrl+Enter` cycles matches wrapping around.
- [ ] No matches → overlay flashes/red, cursor stays put.
- [ ] Exiting restores normal key handling (letters go to command line again).
- [ ] Works on a 10k-entry panel without input lag.

## F1.2 File highlighting groups

**Expected functionality**
- Config-driven coloring of panel entries by rule groups, first match wins: each rule = masks (F1.20) + attribute predicates (dir, symlink, executable, hidden, broken link) → color pair (normal + selected variants).
- Ship a default rule set mirroring Far's feel: dirs white-bold, executables green, archives magenta, media/docs distinct, hidden dimmed, broken links red.
- Rules stored in the theme-adjacent config (TOML), editable by hand in P1 (UI editor arrives with settings UI in P2); reloaded on change.

**Acceptance criteria**
- [ ] Default set colors a fixture directory exactly per snapshot test (both panels, selected + unselected variants).
- [ ] Rule order respected: an entry matching two groups takes the first.
- [ ] Invalid rule file → warning + fallback to defaults, never a crash.
- [ ] Highlighting adds no perceptible render cost on 10k-entry listings (rules pre-compiled).

## F1.3 Quick view panel (Ctrl+Q)

**Expected functionality**
- `Ctrl+Q` switches the passive panel into quick-view mode: live preview of the active panel's cursor item — text head for files (viewer engine, read-only, first N KB), entry count + total size for directories (computed async, cancellable on cursor move), file info fallback for binaries (size, type guess, mtime, permissions).
- Preview updates on cursor move with debounce (~150 ms); `Ctrl+Q` again restores the file panel.

**Acceptance criteria**
- [ ] Moving the cursor across 50 files quickly never blocks navigation; previews render for the resting position.
- [ ] Directory totals stream in (`計算…` → final count) and cancel cleanly when the cursor moves on.
- [ ] Binary file shows the info card, not garbage.
- [ ] Mode survives Tab switching and is per-panel-slot, restored on `Ctrl+Q` toggle only.

## F1.4 Drives / locations menu (Alt+F1 / Alt+F2)

**Expected functionality**
- `Alt+F1`/`Alt+F2` open the locations menu for the left/right panel: platform volumes (POSIX: mount points with fs type and free space; Windows: drive letters), `~`, `/`, XDG user dirs (Desktop/Documents/Downloads…), saved directory shortcuts (read-only list in P1; management is P2), and — when the archive/remote providers are active — an "open panel providers" section.
- Selecting an entry sets that panel's directory. Menu is type-to-filter.

**UI**
```
┌─ Left panel location ────────────────┐
│ ~  /home/user                        │
│ /  root                              │
│ ▸ /mnt/data      ext4   412 GB free  │
│ ▸ /Volumes/T7    exfat  1.2 TB free  │
│ ─────────────────────────────────    │
│ ⌂ Downloads   ⌂ Documents            │
└──────────────────────────────────────┘
```

**Acceptance criteria**
- [ ] All mounted volumes appear with correct free-space figures; unmounted/stale network mounts don't hang the menu (async probe with timeout, entry marked unavailable).
- [ ] Selection changes only the targeted panel.
- [ ] Menu opens < 100 ms even when a network mount is unresponsive.

## F1.5 Panel footer: free space & totals

**Expected functionality**
- Panel footer permanently shows: item totals of the listing (`128 files, 14 dirs, 2.3 GB`), selection summary when active, and the volume's free/total space for the panel's directory.

**Acceptance criteria**
- [ ] Figures match `df`/`du` within rounding; update after operations and on auto-refresh events.
- [ ] Footer degrades gracefully at narrow widths (drops totals before free space).

## F1.6 Auto-refresh on filesystem change

**Expected functionality**
- `watchdog` observers on both visible directories: external create/delete/rename/size changes re-list the affected panel with debounce (200 ms), preserving cursor (follow the cursor file by name) and selection (by name; vanished entries drop out).
- Fallback to timed polling (configurable, default 2 s) where native watching is unavailable (some network FS); watching auto-suspends while a modal file operation is running on that directory.

**Acceptance criteria**
- [ ] `touch x` in another terminal makes `x` appear within 500 ms without user input.
- [ ] Cursor stays on the same file across a refresh; selection survives except deleted entries.
- [ ] A build spamming 1000 events/s coalesces into few refreshes (no UI thrash, CPU bounded).
- [ ] Watcher failure (e.g., inotify limit) degrades to polling with a one-time status notice.

---

# B. File Operations

## F1.7 Trash-aware delete

**Expected functionality**
- `F8` now deletes to the OS trash (`send2trash`) by default; `Shift+Del` deletes permanently (Far convention). Confirmation wording reflects the destination ("Move to Trash" vs red "Delete permanently").
- Volumes without trash support (some network/removable) fall back to permanent with an explicit warning in the dialog.
- Config toggle to invert the default.

**Acceptance criteria**
- [ ] `F8` file is recoverable from the OS trash on macOS, GNOME/KDE, Windows.
- [ ] `Shift+Del` bypasses trash; dialog visually distinct (red).
- [ ] No-trash volume: dialog states permanent deletion before proceeding.
- [ ] Large-selection trash operation shows progress and is cancellable.

## F1.8 Operation error recovery

**Expected functionality**
- Any per-file error during copy/move/delete (permission denied, file busy, disk full, path too long, vanished source) raises a recovery dialog: **Retry · Skip · Skip All · Cancel**, with the OS error text and the affected path. "Skip All" scopes to same-class errors for the operation.
- Skipped files are collected; on completion a summary dialog lists them (copyable text).
- Disk-full during copy: partial target file is removed on Skip/Cancel (never left truncated silently).

**Acceptance criteria**
- [ ] Scripted fixture (1 unreadable file among 100) with Skip completes 99 and lists 1 in the summary.
- [ ] Retry after fixing permissions in another terminal succeeds and continues the run.
- [ ] Disk-full path verified with a small loopback/quota volume: no truncated file left behind on skip.
- [ ] Cancel mid-recovery behaves like operation cancel (sources intact).

## F1.9 Attributes / permissions dialog (Ctrl+A)

**Expected functionality**
- `Ctrl+A` on cursor/selection: POSIX — rwx grid (user/group/other), setuid/setgid/sticky, octal field kept in sync, owner/group display (change requires elevation → P2, greyed with hint), mtime/atime editing; Windows — RO/Hidden/Archive checkboxes, times.
- Multi-file mode: tri-state checkboxes (set/clear/leave); optional "recurse into subdirectories" with separate file/dir masks for the recursion.
- Timestamps editable via ISO field with "now" button.

**UI**
- Grid dialog: checkboxes + live octal (`0755`); `[ Set ] [ Cancel ]`.

**Acceptance criteria**
- [ ] Octal field and checkboxes stay bidirectionally consistent.
- [ ] Multi-file tri-state: "leave" genuinely leaves differing bits untouched (verified on a mixed fixture).
- [ ] Recursive apply honors the file/dir distinction; progress + cancel for big trees.
- [ ] mtime edit round-trips to the second; panel reflects changes immediately.

---

# C. Command Line

## F1.10 Command history

**Expected functionality**
- Every executed command stored in the DB (deduplicated to most-recent, capped LRU, timestamps). `Ctrl+E`/`Ctrl+X` cycle prev/next into the command line (Far keys); `Alt+F8` opens the history dialog: type-to-filter list, `Enter` executes, `Shift+Enter` inserts without executing, `Del` removes an entry, pinning supported.
- History excluded: commands prefixed with a space (convention), configurable.

**Acceptance criteria**
- [ ] History survives restart; ordering = recency; duplicates collapse.
- [ ] `Alt+F8` filter narrows on substring; both execute and insert paths work.
- [ ] Space-prefixed command provably absent from the DB.
- [ ] 10k-entry history: dialog opens and filters instantly (indexed query).

## F1.11 Name/path insertion & environment expansion

**Expected functionality**
- `Ctrl+Enter` inserts the cursor file's name into the command line (quoted if needed); `Ctrl+F` inserts its full path; `Ctrl+[` / `Ctrl+]` insert the left/right panel path. Multiple presses append with separating spaces.
- Environment variables (`$VAR`, `${VAR}`, `%VAR%` on Windows) and `~` expand at execution time (shell does it — the app must merely not mangle them; the `cd` interceptor performs its own expansion).

**Acceptance criteria**
- [ ] Names with spaces/quotes insert correctly quoted for the active shell.
- [ ] `cd $HOME/pro*` style input: `cd` interceptor expands env + `~` (glob not required, documented).
- [ ] All four insertion keys work in every panel mode.

## F1.12 Command-line completion

**Expected functionality**
- `Tab` with a non-empty command line completes: first token → executables from PATH + shell builtins; other tokens → files/dirs relative to the active panel (dirs get a trailing `/`). Ambiguity opens an inline dropdown navigated by arrows; unique match completes in place. Empty command line: `Tab` keeps switching panels (documented deviation from Far).
- Hidden files included only when the prefix starts with `.`.

**Acceptance criteria**
- [ ] `git ch<Tab>` shows dropdown of matching files only if no unique completion; `./scr<Tab>` completes `./script.sh`.
- [ ] Completion respects quoting mid-token (`"My Do<Tab>` → `"My Documents/`).
- [ ] Dropdown dismisses with `Esc` leaving the line untouched.
- [ ] PATH scan cached; first completion < 150 ms.

## F1.13 File associations (Enter opens)

**Expected functionality**
- `Enter` on a non-executable file resolves an association table (ordered rules: mask → command template with `{file}` etc., flags: internal viewer / internal editor / external command / OS default). Default table ships: text-ish → internal viewer? No — default: OS default opener (`open`/`xdg-open`/`start`) for media & documents, internal viewer for unknown text, archives → archive panel (F1.28).
- `Shift+Enter` always uses the OS default opener, bypassing rules. Rules editable in TOML config (UI in P2).

**Acceptance criteria**
- [ ] `Enter` on `.png` opens the OS image viewer without blocking the TUI; on `.log` opens the internal viewer; on `.zip` enters the archive.
- [ ] Custom rule (`*.md` → `glow {file}`) executes via the console pipeline with correct quoting.
- [ ] Broken rule (missing binary) → error dialog naming the rule, no crash.
- [ ] `Shift+Enter` bypass verified for a masked type.

---

# D. Viewer Upgrades

## F1.14 Hex / dump mode

**Expected functionality**
- `F4` inside the viewer toggles text ↔ hex: offset column, 16 bytes hex, ASCII gutter; navigation by byte offset; same windowed-read engine (any file size). Read-only.
- Text-mode search hits carry over to the equivalent offset when switching modes.

**UI**
```
000012a0  4d 5a 90 00 03 00 00 00  04 00 00 00 ff ff 00 00  MZ..............
```

**Acceptance criteria**
- [ ] 1 GB binary: instant open, instant `End`, bounded memory (same targets as F0.12).
- [ ] Offsets and bytes verified against `xxd` output on a fixture.
- [ ] Mode toggle preserves the current file position (top byte visible in both modes).

## F1.15 Encodings & auto-detection (viewer)

**Expected functionality**
- Auto-detect on open via `charset-normalizer` (BOM honored first); `Shift+F8` opens the encoding menu (UTF-8, UTF-16LE/BE, cp1251, koi8-u, latin-1, …, full codec list searchable); `F8` cycles a short user-configurable ring. Re-decode is instant (windowed).
- Detected/selected encoding shown in the status bar.

**Acceptance criteria**
- [ ] Fixture set (UTF-8, UTF-8+BOM, UTF-16LE, cp1251, koi8-u) auto-detects correctly ≥ 95 % (golden test).
- [ ] Manual override re-renders the visible window < 50 ms and persists for this file via position memory (P2 full memory; P1 session-scoped).
- [ ] Invalid bytes render as replacement chars, position math stays correct.

## F1.16 Viewer search

**Expected functionality**
- `F7` search dialog: modes text (with case toggle), regex, hex bytes; direction; `Shift+F7`/`Alt+F7` next/previous. Search runs over the whole file with streaming scan + progress + cancel for large files; hits highlighted in view; wraps with notice.

**Acceptance criteria**
- [ ] Text, regex and hex (`4D 5A`) searches each find known fixtures; next/prev traverse all matches.
- [ ] Search in a 1 GB file streams with progress and remains cancellable; UI responsive.
- [ ] Regex timeout/catastrophic patterns guarded (scan budget per window, warning).

---

# E. Editor Upgrades

## F1.17 Editor search & replace

**Expected functionality**
- `F7` find (text/regex, case, whole-word), `Shift+F7` next, `Ctrl+F7` replace with **Replace / All / Skip / Cancel** flow; regex replace supports group references (`\1`). "All" reports the replacement count; whole-All is one undo step.

**Acceptance criteria**
- [ ] Regex replace with groups verified (`(\d+)-(\d+)` → `\2-\1`).
- [ ] Replace-All on a 100k-line file completes < 2 s and undoes as a single step.
- [ ] Search wraps with notice; no-match states clear.

## F1.18 Editor encodings & EOL controls

**Expected functionality**
- Open uses the same auto-detect as F1.15; `Shift+F8` in the editor changes the interpretation (re-decodes from disk, guarded if buffer modified); save-as dialog gains encoding and EOL (LF/CRLF) selectors. Status bar shows encoding + EOL, both clickable.

**Acceptance criteria**
- [ ] cp1251 fixture opens readable automatically; save preserves cp1251 bytes (round-trip diff clean).
- [ ] Changing EOL to CRLF on save converts all line endings exactly once.
- [ ] Re-decode with unsaved changes prompts before discarding the buffer.

## F1.19 Editor syntax highlighting

**Expected functionality**
- Pygments-based highlighting by extension/shebang/modeline, theme-integrated; incremental re-lex of edited regions (or debounced window re-lex) to keep typing latency flat; auto-disabled above a size threshold (default 5 MB) and for pathological lines (> 50k chars); toggle in the editor menu.

**Acceptance criteria**
- [ ] Python/JS/Markdown/TOML fixtures highlighted correctly per snapshot.
- [ ] Typing latency with highlighting on a 5k-line file: no perceptible difference (< 16 ms per keystroke budget).
- [ ] Threshold fallback and manual toggle both work and are indicated in the status bar.

---

# F. Search & Masks

## F1.20 File-masks engine (foundational)

**Expected functionality**
- One shared library implementing Far-style masks used by selection, highlighting, associations, find-file (and later filters/plugins): semicolon/comma-separated globs (`*.py;*.toml`), `|` separator for exclude section (`*|*.bak;*~`), `?` and `[a-z]` classes, case-insensitive by default, optional path-relative matching (`src/**/*.py`).
- Compiled to predicates once; documented grammar with error reporting (position of bad token).

**Acceptance criteria**
- [ ] Grammar unit suite ≥ 50 cases incl. excludes, classes, unicode names, `**`.
- [ ] Same mask string yields identical results in selection, highlighting and find-file (cross-feature test).
- [ ] Malformed mask → inline error with caret position in every consuming dialog.
- [ ] 10k-file matching < 10 ms per mask set (pre-compiled).

## F1.21 Find file (Alt+F7)

**Expected functionality**
- Dialog: masks (F1.20), root (active dir / custom / all mounted — P1: active + custom), subdirectory depth option, optional content search (plain/regex, encoding-aware via detection; delegates to `rg` when available and equivalent flags map, transparent fallback to internal scanner), size/date quick filters.
- Async scan streaming results into a list as found: `Enter` jumps the active panel to the file, `F3`/`F4` view/edit in place, `Ctrl+Enter` continues search. Progress (dirs scanned, matches), cancellable. Results panel push to temp panel arrives in P2 — P1 keeps the list dialog.

**UI**
```
┌─ Find file ───────────────────────────────────────────────┐
│ Masks [ *.py;*.md      ]  In [ /home/user/proj      ▾ ]   │
│ [x] Subdirectories   Containing [ TODO             ]     │
│ ( ) Plain (•) Regex  [x] Case-insensitive                 │
│ ───────────────────────────────────────────────────────── │
│ src/app/main.py:212        TODO: remove after v2          │
│ docs/plan.md:8             TODO: budget                   │
│ … searching src/vendor  ▏ 1 240 dirs, 18 matches [Cancel] │
└───────────────────────────────────────────────────────────┘
```

**Acceptance criteria**
- [ ] Name-only search over 100k files streams results and completes without UI freeze.
- [ ] Content regex search finds fixture strings in cp1251 files (detection applied).
- [ ] `rg`-backed and internal scanners return the same match set on the fixture corpus.
- [ ] `Enter` on a result lands panel cursor on that file; dialog state (incl. last query) restored on next `Alt+F7`.
- [ ] Cancel stops the scan within 200 ms.

---

# G. UI, Persistence & Platform

## F1.22 Histories: folders, viewed/edited, dialog inputs

**Expected functionality**
- Three more persistent histories: folders visited (`Alt+F12` dialog → jump), files viewed/edited (`Alt+F11` → reopen in viewer/editor), and per-field dialog input histories (`Ctrl+Down` dropdown on any history-enabled input: copy targets, masks, search strings…). Same dialog features as F1.10 (filter, delete, pin); shared LRU caps; single "clear histories" command.

**Acceptance criteria**
- [ ] Folder jump from `Alt+F12` restores that directory incl. from an archive path (falls back to nearest real ancestor if gone).
- [ ] `Alt+F11` reopens a file in the same mode (view vs edit) it was last used.
- [ ] Every input dialog shipped in P0/P1 exposes `Ctrl+Down` history (audit checklist).
- [ ] Clear-histories wipes all four stores (verified in DB).

## F1.23 Theming

**Expected functionality**
- Themes as TOML files (colors for panels, dialogs, menus, editor/viewer, highlighting palette hooks); ship **Far classic**, **Dark modern**, **Light**. Selection via `F9 → Options → Theme` (simple picker; full settings UI is P2); hot-applied. User themes dropped into the config dir are picked up.

**Acceptance criteria**
- [ ] Switching themes re-renders everything live with no restart and no color bleed.
- [ ] All three shipped themes pass a contrast audit on 256-color terminals.
- [ ] A user theme overriding only two keys inherits the rest from its declared base.

## F1.24 Menu bar (F9)

**Expected functionality**
- `F9` activates the top menu: **Left / Files / Commands / Options / Right** (Far layout). Every user-facing action available via menus with its shortcut shown (single source of truth: the action registry from the keymap). Left/Right menus: panel mode, sort, re-read, drives. `Esc` closes; hotkey letters navigate.

**Acceptance criteria**
- [ ] Menu tree audit: every P0/P1 action present exactly once with the correct live shortcut label.
- [ ] Full keyboard traversal (F9, arrows, hotkeys, Enter, Esc).
- [ ] Menu invokes identical code paths as shortcuts (no duplicated logic — spot-check via action registry).

## F1.25 Mouse support

**Expected functionality**
- Click focuses panel and sets cursor; double-click = `Enter`; wheel scrolls panel/viewer/editor; click on key-bar slot and menu items activates them; dialog buttons/inputs clickable; viewer/editor click positions cursor. Right-click on a panel entry toggles selection (Far-ish). No drag-and-drop in P1.

**Acceptance criteria**
- [ ] All listed interactions work in iTerm2, GNOME Terminal, Windows Terminal, and inside tmux (mouse mode on).
- [ ] Mouse can be disabled in config for terminals where it conflicts with native selection; app fully usable either way.

## F1.26 Clipboard integration

**Expected functionality**
- `Ctrl+Ins` copies selected names (newline-separated), `Alt+Shift+Ins` full paths, to the system clipboard; `Shift+Ins` pastes into the command line and dialog inputs; editor gets clipboard cut/copy/paste (`Ctrl+X/C/V` in edit context). Remote-safe: OSC 52 fallback when no native clipboard (SSH).

**Acceptance criteria**
- [ ] Names/paths copy verified on macOS (pbpaste), Linux (wl-paste/xclip), Windows.
- [ ] Over SSH without X forwarding, OSC 52 path delivers the clipboard to the local machine (supported terminals).
- [ ] Editor paste of multi-line clipboard preserves EOL policy of the buffer.

## F1.27 Logging framework

**Expected functionality**
- Structured logging (std `logging`) to a rotating file in the state dir; level and sinks configurable via config and env (`<APP>_LOG=debug`, `<APP>_LOG_SINK=file|stderr`), Far's `far.log.*` spirit. Subsystem loggers (fs.ops, ui, ai, claude, plugins). `--log-level` CLI flag. AI/Claude loggers redact prompts/keys by default (`ai.log_prompts=true` to opt in).
- Crash handler writes a traceback report file and shows a dialog pointing to it.

**Acceptance criteria**
- [ ] Debug run of a copy operation produces a readable op trace (paths, sizes, timings).
- [ ] API keys never appear in logs at any level (grep audit in tests).
- [ ] Forced crash produces the report file and the friendly dialog, not a raw traceback over the TUI.
- [ ] Rotation caps total log size (default 10 MB).

---

# H. Archives

## F1.28 Archive browsing as a panel

**Expected functionality**
- `Enter` on `.zip`, `.tar`, `.tar.gz/tgz`, `.tar.bz2`, `.tar.xz`, `.7z` (via `py7zr`) opens the archive as a read-only virtual panel: internal tree navigable like a directory, `..` at archive root exits to the real panel. `F3`/`F4`(read-only view) extract the file to a temp cache transparently. `F5` from inside the archive extracts selection to the passive panel (progress, conflicts via F0.10). Nested archive-in-archive: one level via temp extraction.
- Encrypted archives prompt for password (session-cached per archive, never persisted).

**Acceptance criteria**
- [ ] Each listed format browses and extracts a fixture correctly (contents byte-identical, mtimes restored where format supports).
- [ ] 10k-entry zip lists < 1 s; entering subdirs instant (central directory parsed once).
- [ ] Corrupt archive → error dialog, panel stays on the real directory.
- [ ] Password flow: wrong password re-prompts; cancel exits cleanly; password absent from DB/logs.
- [ ] Temp cache cleaned on app exit.

## F1.29 Archive create & extract operations

**Expected functionality**
- `Shift+F1` on a selection: create-archive dialog — format (zip/tar.gz/tar.xz/7z), name (default from dir/selection), compression level, "delete files after" off by default. Runs with progress/cancel.
- `Shift+F2` on an archive under cursor: extract dialog — target (default passive panel), "extract with full paths" toggle. `F5` semantics from F1.28 remain the primary extraction path.

**Acceptance criteria**
- [ ] Round-trip: create zip from 500-file selection, extract elsewhere, tree diff clean.
- [ ] Cancel mid-create removes the partial archive file.
- [ ] Paths with unicode and spaces survive round-trip on all formats.
- [ ] Progress shows entries + bytes; UI responsive during a 1 GB compression.

---

# I. AI Module

## F1.30 Cost guardrails

**Expected functionality**
- Central AI gateway (all features call through it) tracking per-session and per-day token usage and cost estimate (from the model's pricing table); status shown in every AI surface footer (`session: 41k tok · ~$0.31`).
- Configurable soft budget (warn) and hard budget (block with override dialog) per day; `count_tokens` pre-flight for large payloads (> 20k tokens estimated) with a confirm dialog; all AI requests logged (F1.27, redacted).

**Acceptance criteria**
- [ ] Usage counter matches API-reported `usage` fields across mixed streaming/non-streaming calls.
- [ ] Hard budget blocks the next request with a clear dialog; override works and is logged.
- [ ] Pre-flight confirm fires for an oversized context and honors cancel.
- [ ] Counters persist per-day in the DB and reset on date change.

## F1.31 Explain / summarize

**Expected functionality**
- `Alt+F3` on cursor item (also: AI palette action, viewer key `F1`-adjacent menu): file → streamed summary/explanation in a read-only result pane (viewer shell) — code files get "what it does + structure", docs get a summary, directories get a contents overview built from names + sizes + README head. Text extraction respects a size cap (head+tail sampling beyond it, disclosed in the output).
- Result pane offers **Copy**, **Ask follow-up** (jumps into the chat sidebar F1.33 with context carried over), **Close**.

**Acceptance criteria**
- [ ] Summary of a source file, a Markdown doc, and a directory each produce sensible streamed output (golden smoke set, manual rubric).
- [ ] Cap respected: a 500 MB log sends only the disclosed sample (network audit).
- [ ] Binary file → graceful "no readable text" with the info card instead of an API call.
- [ ] Follow-up lands in the chat sidebar with the same file context attached.

## F1.32 Smart selection (NL → selection)

**Expected functionality**
- In the select-by-mask dialog (`Gray +`) an **AI** mode: natural-language criterion ("logs older than a week, but not gzipped") → structured-output translation into a deterministic predicate (masks + size/date/attr ranges) shown to the user *before* applying, with the plain-language echo of what it will select. Apply executes the predicate locally — file names/metadata only ever leave the machine when needed (names list included only if the predicate can't be derived without examples; disclosed).
- Falls back to plain masks on API failure.

**Acceptance criteria**
- [ ] 10-case golden set of NL criteria produces predicates matching a hand-written oracle on a fixture tree.
- [ ] The derived predicate (not opaque AI output) is displayed and editable before applying.
- [ ] Zero-match predicate reports "nothing selected", not silence.
- [ ] Offline → dialog remains fully usable in mask mode.

## F1.33 Chat sidebar

**Expected functionality**
- `Alt+A` toggles a right-hand chat pane (panels shrink): conversation with the model with **context chips** the user can toggle per message — active dir listing (truncated), current selection names, current viewer/editor file (content within cap). Streaming markdown rendering; code blocks copyable (`y` on block / mouse); conversation scoped to the app session, with "save transcript to file" action; prompt caching used for the stable context prefix.
- Slash-commands inside chat: `/clear`, `/context` (show what would be sent), `/model`.
- Chat can propose shell commands — rendered with the same Run/Edit/Copy affordance and safety rules as the AI palette (F0.18); Run is always explicit.

**UI**
```
┌ panels (narrowed) ─────────┐┌ AI chat ─────────────────────┐
│                            ││ [dir] [3 selected] [viewer]  │
│                            ││ > why is this repo's build   │
│                            ││   slow?                      │
│                            ││ ▌Looking at the file list,   │
│                            ││  vendor/ holds 1.2 GB …      │
│                            ││ ───────────────────────────  │
│                            ││ ask: █          41k · $0.31  │
└────────────────────────────┘└──────────────────────────────┘
```

**Acceptance criteria**
- [ ] Toggle preserves chat state; panels reflow correctly at 80 and 200 cols.
- [ ] Context chips: `/context` shows exactly the payload; disabled chips provably excluded (network audit).
- [ ] Command proposals never execute without explicit Run; danger flagging as in F0.18.
- [ ] Streaming can be interrupted (`Esc`) leaving partial answer in place; follow-ups keep conversation history.
- [ ] Cache hit on the second message with unchanged context (verify `cache_read_input_tokens > 0`).

---

# J. Claude Code Module

## F1.34 Headless task runner

**Expected functionality**
- `Ctrl+K, T`: prompt dialog for a one-shot Claude Code task executed headless in the active panel directory (`claude -p` with stream-JSON output, or the SDK equivalent once F1.35 lands — same UI either way): live transcript pane shows assistant text, tool calls (collapsed one-liners: `⚒ Edit src/app.py`), and result; panels auto-refresh as files change (F1.6).
- Task is foreground-modal in P1 (background tasks arrive in P2) but cancellable (`Esc` → confirm → terminate process/session cleanly).
- On completion: summary line (exit status, files touched count, duration, cost if reported).

**Acceptance criteria**
- [ ] Task "create a README describing this directory" runs, transcript streams live, README appears in the panel without manual refresh.
- [ ] Cancel terminates the underlying process within 2 s, no orphans (process-table check).
- [ ] CLI missing/not-logged-in states produce guided dialogs (install / run `claude` login flow), not raw stderr.
- [ ] Transcript retained in a scrollback buffer viewable until the next task.

## F1.35 Embedded Agent SDK session

**Expected functionality**
- `Ctrl+K, A`: embedded interactive agent session via the **Claude Agent SDK for Python** (`claude-agent-sdk`, `query()`/client API) in the active panel dir: a persistent conversation pane (multi-turn), streamed assistant output and tool activity, interruptible turn, session continues until closed. Working directory, allowed tools, and permission mode set from app config.
- Supersedes the runner UI for interactive work; the F1.34 one-shot dialog remains for fire-and-forget tasks.
- Session transcript saved to the DB session store (groundwork for P2 session manager).

**Acceptance criteria**
- [ ] Multi-turn flow verified: task → follow-up correction → agent applies it in the same session context.
- [ ] Tool activity rendered live (file edits, bash) with the panels refreshing on changes.
- [ ] Interrupt (`Esc`) stops the current turn without killing the session; close ends it cleanly.
- [ ] SDK not installed → dialog with `pip install claude-agent-sdk` guidance; feature hidden from menus until available.
- [ ] Transcript persisted and reloadable read-only after the session ends.

## F1.36 Context passing

**Expected functionality**
- The current panel context is injectable into both runner and embedded sessions: selected files (paths; `@`-mentions in the prompt input autocomplete from panel entries), active/passive dir paths, and optionally the current viewer/editor file. A context strip above the prompt shows exactly what will be attached; toggles per item. File *contents* are read by the agent itself through its tools — the app passes paths, not bodies (keeps context honest and cheap).

**Acceptance criteria**
- [ ] With 3 selected files, the composed prompt (visible via a "show prompt" toggle) contains exactly those 3 paths.
- [ ] `@`-mention autocomplete offers entries from both panels, inserting panel-relative or absolute paths correctly quoted.
- [ ] Toggling a context item off provably removes it from the composed prompt.

## F1.37 Permission prompts as TUI dialogs

**Expected functionality**
- Embedded sessions run with SDK permission callbacks routed to the app's dialog kit: a tool request (edit, bash command, web fetch) raises a modal showing the tool, the concrete input (diff preview for edits, command line for bash), and options **Allow once · Allow for this session (this tool) · Deny** (+ optional deny message passed back to the agent). Permission decisions logged (F1.27).
- Config presets: "ask for everything", "ask for writes and bash" (default), "auto-accept edits" — matching the SDK's permission modes.

**UI**
```
┌─ Claude wants to run a command ───────────────────┐
│ bash: rm -rf build/ && make all                   │
│ in: /home/user/proj                               │
│ [ Allow once ] [ Allow bash this session ] [Deny] │
└───────────────────────────────────────────────────┘
```

**Acceptance criteria**
- [ ] Under the default preset, an agent file edit shows a diff preview before Allow; Deny with message makes the agent adjust course (observable in transcript).
- [ ] "Allow for session" persists for that tool until session end and no longer prompts.
- [ ] Dialog appears even while the transcript is streaming (turn pauses, resumes after the decision).
- [ ] All decisions appear in the log with tool + summary (redaction rules applied).

---

## Phase 1 exit checklist (release gate)
- [ ] All F1.x acceptance criteria green; no P0 regressions (full suite).
- [ ] A Far Manager user can perform their daily workflow (navigate, copy, view, edit, search, archives) without consulting docs — validated by ≥ 3 external testers.
- [ ] AI and Claude features fully optional: clean run with no API key, no `claude` CLI, no network.
- [ ] Packaging: `pipx install` + Homebrew formula; signed release notes stating trash behavior change (F1.7) and known Windows limitations.
