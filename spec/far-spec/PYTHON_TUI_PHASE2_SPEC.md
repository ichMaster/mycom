# Phase 2 (Maturity) — Feature Specifications

Companion to [PYTHON_TUI_PRODUCT_SCOPE.md](PYTHON_TUI_PRODUCT_SCOPE.md). Details every Phase 2 feature: expected functionality, UI, and acceptance criteria. Phase 0 is specified in [PYTHON_TUI_PHASE0_SPEC.md](PYTHON_TUI_PHASE0_SPEC.md).

**Entry criteria (delivered by Phase 1, assumed present):** file-masks engine, histories, auto-refresh watcher, archives read/write, highlighting groups, quick view, encodings, editor/viewer search, clipboard, theming, chat sidebar, headless Claude runner → Agent SDK embedding with TUI permission prompts, cost guardrails.

Conventions as in Phase 0 (Far-compatible default keys; keyboard-first; async UI).

---

# A. Panels & Navigation

## F2.1 Panel filter (Ctrl+I)

**Expected functionality**
- Per-panel display filter: show only entries matching criteria — include/exclude masks (reuses the Phase 1 masks engine), size range, modified-date range, attributes (dirs/files/hidden/symlinks).
- Filter is a view: operations act only on visible entries; footer warns that a filter is active.
- Quick presets: "today", "this week", "source files" — user-editable, stored in DB.

**UI**
```
┌─ Panel filter ────────────────────────────────┐
│ Include masks  [*.py;*.toml            ]      │
│ Exclude masks  [__pycache__/*          ]      │
│ Size   [ ≥ 0 B ] – [ ∞ ]   Date [any ▾]       │
│ [x] Files  [x] Dirs  [ ] Hidden only          │
│ Presets: (Today)(Week)(Source)  [Save preset] │
│        [ Apply ] [ Clear ] [ Cancel ]         │
└───────────────────────────────────────────────┘
```
- Active filter indicator in the panel title: `/path ▼filtered`.

**Acceptance criteria**
- [ ] Filtered panel shows only matching entries; count footer says `12 of 480 shown`.
- [ ] `Ctrl+I` → Clear restores the full listing and cursor position.
- [ ] Copy/delete with an active filter touches only visible entries.
- [ ] Filter survives directory refresh but resets on directory change (configurable).
- [ ] Presets persist across restarts.

## F2.2 Extended sorting modes

**Expected functionality**
- Add: ctime, atime, owner, natural-numeric (`file2 < file10`), case-sensitive toggle, "unsorted" (directory order). Sort menu via `Ctrl+F12` listing all modes with current one marked.
- Per-panel "directories first" toggle moves from hard-coded to configurable.

**Acceptance criteria**
- [ ] Each new mode ordered correctly on a fixture tree (unit-tested, incl. numeric names and unicode owners).
- [ ] `Ctrl+F12` menu selects any mode; glyph in the panel header updates.
- [ ] Natural sort: `a2.txt` precedes `a10.txt`.

## F2.3 Custom column configuration

**Expected functionality**
- User-defined view modes beyond the built-in three: an ordered list of columns (name, size, packed size, mtime/ctime/atime, permissions, owner, link target, extension) with width specs (fixed, auto, percent).
- Definitions editable in the settings UI (F2.10) and stored in DB; assignable to `Ctrl+4…Ctrl+9` slots.

**Acceptance criteria**
- [ ] A custom mode with permissions + owner renders correctly and can be bound to `Ctrl+4`.
- [ ] Width rules honored across terminal resizes; minimum widths enforced.
- [ ] Broken definition (e.g., zero columns) rejected by validation, never renders a corrupt panel.

## F2.4 Tree panel

**Expected functionality**
- Alternate panel mode showing a directory tree of the current volume/root with lazy expansion. Cursor + `Enter` sets the *other* panel to the highlighted directory; `Right`/`Left` expand/collapse.
- Incremental type-to-find within the tree.

**UI**
- Tree replaces the panel's file list: indented branches with `├─`/`└─` guides; current branch highlighted.

**Acceptance criteria**
- [ ] Expanding a node with 5,000 subdirs stays responsive (lazy load, spinner while scanning).
- [ ] `Enter` navigates the passive panel and returns focus to it (configurable).
- [ ] Deleted-externally node handled gracefully on expand (prunes with a notice).

## F2.5 Info panel

**Expected functionality**
- Alternate panel mode summarizing the passive panel's context: volume total/free space, filesystem type, directory totals (files/dirs/bytes computed async), and the passive panel's cursor file details (size, times, permissions, owner, link target, MIME guess).

**Acceptance criteria**
- [ ] Totals compute in background; UI responsive during a deep scan; scan cancels on mode exit.
- [ ] Values match `df`/`du` within rounding.
- [ ] Updates live as the passive panel cursor moves.

## F2.6 Directory shortcuts (Ctrl+0…9)

**Expected functionality**
- `Ctrl+Shift+<digit>` stores the active panel's path in slot *digit*; `Ctrl+<digit>` jumps to it. Slots listed and editable in a small manager dialog (also reachable from the drives menu). Persisted in DB.

**Acceptance criteria**
- [ ] Save/jump roundtrip works for all 10 slots; jump to a vanished path falls back to nearest ancestor with a notice.
- [ ] Slots visible with their paths in the manager dialog; deletable there.

---

# B. File Operations

## F2.7 Background / queued operations

**Expected functionality**
- Copy/move/delete can be sent to background (`B` button in the progress dialog or `Ctrl+B`): the dialog collapses into a status-line indicator; the user keeps working.
- Operation queue: multiple background jobs run sequentially per target device (parallel across devices); a jobs panel (`Ctrl+J`) lists jobs with progress, pause/resume/cancel.
- Conflicts and errors in a background job pop the job to the foreground for interaction (never silently skip).

**UI**
- Status line chip: `⇅ 2 jobs · 46% · 112 MB/s`; jobs panel = modal list with per-job progress bars and controls.

**Acceptance criteria**
- [ ] A large copy sent to background leaves panels fully interactive; completion shows a toast notification.
- [ ] Two jobs to the same disk queue sequentially; to different disks run concurrently.
- [ ] Conflict inside a background job surfaces the F0.10 dialog; answering resumes the job in background.
- [ ] Cancel from the jobs panel behaves identically to foreground cancel (no source damage).
- [ ] App quit with active jobs warns and offers wait/cancel.

## F2.8 Symlink / hardlink creation (Alt+F6)

**Expected functionality**
- `Alt+F6` on cursor file opens a link dialog: link type (symbolic relative / symbolic absolute / hard), target location pre-filled with passive panel dir. Hardlinks restricted to same filesystem, files only; sensible errors otherwise.
- Windows: symlinks require developer mode/privilege — detect and explain.

**Acceptance criteria**
- [ ] Each link type produces a correct link verified by `readlink`/inode comparison.
- [ ] Relative symlink remains valid after moving the pair of directories together.
- [ ] Cross-device hardlink attempt yields a clear refusal, not an OS traceback.

## F2.9 Multi-file rename by pattern

**Expected functionality**
- On a selection, `Shift+F6` opens batch-rename: pattern with placeholders (`[N]` name, `[E]` ext, `[C]` counter with width/start, date tokens), plus regex search→replace mode and case transforms (lower/upper/title).
- Live preview table (old → new) with per-row validity; collisions detected before execution. Rename executes as a transaction plan (two-phase for swap cases); undo of the last batch (`Ctrl+Z` in panel) while session-local journal is intact.
- "Ask AI" button hands the file list + instruction to the LLM module (F2.22).

**UI**
```
┌─ Rename 14 files ─────────────────────────────────────────┐
│ Pattern  [ [C:03]-[N].[E] ]      ( ) Regex  (•) Pattern   │
│ Search   [            ]  Replace [            ]  [aA ▾]   │
│ ───────────────────────────────────────────────────────── │
│ IMG_2041.jpg      → 001-IMG_2041.jpg                      │
│ IMG_2042.jpg      → 002-IMG_2042.jpg                      │
│ …                                        ⚠ 0 conflicts    │
│        [ Rename ] [ Ask AI ] [ Cancel ]                   │
└───────────────────────────────────────────────────────────┘
```

**Acceptance criteria**
- [ ] Preview always equals the executed result (property-tested on random name sets).
- [ ] Collision (two sources → one target, or target exists) blocks execution with rows flagged.
- [ ] Swap chains (`a→b`, `b→a`) succeed via temp names.
- [ ] Undo restores all names if nothing touched the files in between; refuses with a report otherwise.

---

# C. Command & Automation

## F2.10 Settings UI

**Expected functionality**
- `F9 → Options`: tabbed dialog covering panel behavior, confirmations, editor/viewer defaults, colors/theme selection, AI settings (model, budget), Claude Code settings. Every option maps 1:1 to a documented key in the config store; live apply where safe, marked-restart where not.

**Acceptance criteria**
- [ ] Every Phase 0–2 configurable is reachable in the dialog (audited list); no orphan hidden-only settings.
- [ ] Changes persist and apply without restart except flagged items.
- [ ] Reset-to-defaults per tab and global.

## F2.11 Keybinding customization

**Expected functionality**
- All actions routed through a named-action keymap; settings UI section lists actions with current bindings, rebind by pressing keys, conflict detection, per-context maps (panel/viewer/editor). Export/import with the config (F2.12). Ship the Far-default map; provide a "vim-ish navigation" alternate map.

**Acceptance criteria**
- [ ] Rebinding F5→F8 (swap) works and the key bar labels follow automatically.
- [ ] Conflict within a context is refused with the clash shown.
- [ ] Broken/missing keymap in config falls back to defaults with a warning, never an unusable app.

## F2.12 Config export / import

**Expected functionality**
- `Export settings` writes a single TOML file (settings, keymap, themes, column modes, filter presets, shortcuts, user menu — no secrets, no histories by default; flags to include). `Import` validates, shows a summary diff, applies atomically.

**Acceptance criteria**
- [ ] Export→wipe→import restores an identical environment (golden test comparing effective config).
- [ ] Import of a newer-version file degrades gracefully (unknown keys reported, not fatal).
- [ ] Secrets (API keys) provably absent from the export.

## F2.13 User menu (F2)

**Expected functionality**
- `F2` opens a user-defined command menu: entries have a hotkey letter, title, and command template with substitutions (`{file}`, `{files}`, `{dir}`, `{other_dir}`, `{stem}`, `{ext}`), optional "confirm before run" and "stay in console" flags. Nested submenus. Local (`.<app>.menu.toml` in dir) merges over the global menu, Far-style.

**Acceptance criteria**
- [ ] Menu entry runs with correct substitutions incl. quoting of names with spaces.
- [ ] Local menu file overrides/extends the global one when present.
- [ ] Editing entries via the settings UI writes valid TOML readable on next `F2`.

## F2.14 Window stack & F12 switcher

**Expected functionality**
- Editors and viewers open as windows in a stack over the panels instead of exclusive modes: `Ctrl+Tab` cycles, `F12` lists all open windows (panels, N editors, M viewers) for direct switching; closing returns to the previous window. Unsaved editors marked; quitting the app enumerates unsaved windows.

**UI**
- `F12` popup list: number, type icon, title (path), modified flag.

**Acceptance criteria**
- [ ] Two editors + one viewer can be open simultaneously; switching preserves each window's full state (cursor, scroll, undo).
- [ ] `F12` numbers select directly (`2` jumps to window 2).
- [ ] App exit with an unsaved editor prompts per window; cancel aborts exit entirely.

## F2.15 Help system (F1)

**Expected functionality**
- `F1` opens built-in help: Markdown pages rendered in a viewer-like window with links, TOC, search; context-sensitive entry (from copy dialog → copy topic). Content shipped with the app; also the browser-openable online version.

**Acceptance criteria**
- [ ] Every Phase 0–2 feature has a help page; `F1` from each major dialog lands on the right topic.
- [ ] Links and back-navigation work; search finds topics by keyword.

## F2.16 Localization (en + uk)

**Expected functionality**
- All user-visible strings externalized (gettext); shipped locales: English, Ukrainian. Language auto-detected from locale, overridable in settings. Help content localizable independently (falls back to English per page).

**Acceptance criteria**
- [ ] `LANG=uk_UA.UTF-8` yields a fully Ukrainian UI (audit: zero hard-coded English in `uk` run, CI check on string extraction).
- [ ] Dialog layouts survive longer translated strings (no truncation/overlap at 80 cols).
- [ ] Switching language in settings applies on the fly or after a flagged restart.

---

# D. Viewer & Editor

## F2.17 Viewer: goto, positions, syntax highlighting

**Expected functionality**
- `Alt+F8` goto dialog: absolute offset (dec/hex), line number, or percent.
- Per-file position memory (path+size+mtime keyed, stored in DB, LRU-capped): reopening a file restores offset, wrap mode, encoding choice.
- Syntax highlighting (pygments) for text files under a size threshold (default 5 MB), language by extension/shebang; toggleable (`F8` cycles plain/highlighted alongside encoding menu reorganization from P1).

**Acceptance criteria**
- [ ] Goto `50%` of a 1 GB file lands within one screen of the midpoint instantly.
- [ ] Close at offset X, reopen → same offset; file changed on disk → position discarded silently.
- [ ] Highlighting adds < 50 ms per screen redraw on typical source files; auto-off above threshold.

## F2.18 Editor: columnar (rectangular) blocks

**Expected functionality**
- `Alt+Shift+arrows` selects a rectangular block (Far behavior); copy/cut/paste of columnar blocks (paste inserts block at cursor column across lines, padding with spaces as needed); delete/type-over on block. Interops with stream selection (starting a stream selection drops the columnar one and vice versa).

**Acceptance criteria**
- [ ] Column-cut then column-paste elsewhere reproduces the block exactly, including on lines shorter than the target column (space padding).
- [ ] Works with tabs in the text (columns computed on expanded view, edits preserve tabs outside the block).
- [ ] Undo treats a block operation as a single step.

---

# E. Extensibility, Compare & Remote

## F2.19 Plugin API (Python entry points)

**Expected functionality**
- Public, versioned API (`<app>.api`) with three extension kinds:
  1. **Panel providers** — virtual filesystems: `list(path)`, `open`, `read/write`, `delete`, capabilities flags (archives, SFTP, temp panel are implemented on this interface — dogfooding requirement);
  2. **Commands/actions** — named actions with default bindings, menu placement (F9/F11), and access to app context (panels, selection, dialogs API);
  3. **Event hooks** — on dir change, before/after file ops, on app start/exit.
- Discovery via Python entry points (`pip install <app>-plugin-x`) and a local plugins dir; `F11` lists loaded plugins with enable/disable; a failing plugin is sandboxed to an error report, never a crash.
- Semver policy: API breaking changes only on major versions; deprecation warnings one minor ahead.

**Acceptance criteria**
- [ ] The bundled archive, SFTP, and temp panels are implemented purely against the public API (no private imports — CI-enforced).
- [ ] A "hello world" third-party plugin (docs tutorial) installs via pip and appears in `F11` without config edits.
- [ ] A plugin raising in `list()` shows an error dialog and leaves both panels functional; plugin can be disabled from `F11`.
- [ ] API docs published; tutorial covers all three extension kinds.

## F2.20 Temp panel (virtual file collection)

**Expected functionality**
- A virtual panel holding an arbitrary list of real files/dirs from anywhere: populated from find-file results ("send to temp panel"), from AI/semantic search results, via `Ctrl+P` "add to temp panel", or drag of selection. Entries display their real full path column; all file operations act on the real files; removing an entry removes only the reference (`F8` asks: remove entry vs delete file).

**Acceptance criteria**
- [ ] Find-file results sent to temp panel can be copied somewhere as a batch in one F5.
- [ ] `F8` clearly distinguishes de-listing from deleting; both work as chosen.
- [ ] Entries from different directories with equal basenames coexist and operate correctly.
- [ ] Temp panel contents survive panel switching but not restart (by design, documented).

## F2.21 SFTP remote panel

**Expected functionality**
- `sftp://user@host[:port]/path` in the drives/locations menu (with saved connections) opens a remote FS in a panel via the plugin API (paramiko/asyncssh backend): listing, viewer/editor (download-edit-upload with mtime guard), copy between local↔remote and remote↔remote (through local relay), delete/mkdir/rename/chmod.
- Auth: ssh-agent, key files, password prompt (never stored plaintext; optional keychain). Connection state indicator; reconnect with backoff on drop; all remote ops async with per-op progress.

**Acceptance criteria**
- [ ] Browse + F5 copy of a 100 MB tree in both directions with correct progress/ETA and preserved mtimes.
- [ ] `F4` edit of a remote file: save uploads; concurrent remote change detected via mtime and prompts.
- [ ] Network drop mid-listing degrades to an error + reconnect offer; app remains stable; no zombie connections (verified by server-side session count).
- [ ] Saved connection with agent auth connects without prompts; wrong-password path allows 3 retries then aborts cleanly.

## F2.22 Compare: folders & files

**Expected functionality**
- **Folders** (`F9 → Commands → Compare directories`): compares active vs passive panel by presence + size (+ optional mtime, content-hash modes); result = selection of differing files in both panels, ready for F5 sync-by-hand.
- **Files**: on two selected files (one per panel or two in one), open a side-by-side diff viewer (read-only, hunk navigation `n/p`, intra-line highlights, ignore-whitespace toggle). Binary files: report equal/different + size/hash only.

**Acceptance criteria**
- [ ] Presence/size mode on 10k-file trees completes < 2 s; content mode shows progress and is cancellable.
- [ ] Post-compare selections in both panels exactly represent the differences (unit-tested fixture trees).
- [ ] Diff viewer renders a 50k-line diff smoothly; hunk navigation and whitespace toggle work.
- [ ] Identical files report "identical" without opening the diff view.

---

# F. OS Integration

## F2.23 Privilege elevation

**Expected functionality**
- File operation hitting `EACCES`/`EPERM` offers "Retry as administrator": re-runs the specific operation through an elevated helper (POSIX: `sudo`-spawned helper process over a pipe protocol — mirroring Far's `elevation.cpp` design; Windows: UAC-elevated helper). Elevation is per-operation-session, dropped on completion; elevated state clearly indicated in the progress dialog.
- Never elevate the whole app; helper executes only whitelisted operations (copy/delete/chmod/mkdir/rename).

**Acceptance criteria**
- [ ] Copy into `/etc` (denied) → elevation prompt → succeeds with correct ownership of result; helper exits afterward (no lingering root process — verified).
- [ ] Cancel at the sudo prompt returns to the normal conflict/error flow.
- [ ] Helper rejects any request outside the whitelist (security test).
- [ ] Elevated operations logged (audit line: op, paths, result).

---

# G. AI Module (Phase 2 additions)

## F2.24 AI rename suggestions

**Expected functionality**
- "Ask AI" in the batch-rename dialog (F2.9): sends the selected file *names* (+ optional short content peek for text files, opt-in) and the user's instruction ("English titles, kebab-case, keep dates") to the LLM; response (structured output: array of old→new) fills the standard preview table — same validation, collision detection, and undo as manual patterns. Nothing is renamed without the user pressing Rename.

**Acceptance criteria**
- [ ] Suggestions land in the preview table and are editable before execution; all F2.9 safety criteria apply unchanged.
- [ ] Malformed/partial AI output degrades to filling only valid rows with a notice, never crashes the dialog.
- [ ] Offline/API error keeps the manual dialog fully usable.
- [ ] File contents are only sent when the opt-in peek toggle is on (network-audited).

## F2.25 Editor AI actions

**Expected functionality**
- In the editor, `Ctrl+.` on a selection (or current block) opens an action menu: Explain, Fix/complete, Transform per free-form instruction, Summarize. Result appears in a side-by-side proposal pane with a diff against the selection; **Apply** replaces the selection (single undo step), **Copy** and **Discard** available. Streaming render; request context = selection + configurable surrounding lines, never the whole file above a size cap without confirmation.

**UI**
- Right-hand proposal pane (editor shrinks): instruction input on top, streamed result, `[ Apply ] [ Copy ] [ Discard ]`.

**Acceptance criteria**
- [ ] Explain on a selection produces output without modifying the buffer.
- [ ] Apply of a transform replaces exactly the selection and is undone by a single `Ctrl+Z`.
- [ ] Cancelling mid-stream leaves the buffer untouched.
- [ ] Cost guardrails (Phase 1) apply: per-session budget respected; token estimate shown before sending large selections.

## F2.26 Semantic / natural-language search

**Expected functionality**
- Extension of find-file: a "smart" mode where the query is natural language ("configs mentioning postgres timeouts", "the invoice from March"). Pipeline: cheap local candidate pass (names, extensions, mtime, ripgrep keyword pre-filter derived from the query by the LLM) → LLM relevance ranking over candidate snippets → results with one-line "why matched" explanations. Results go to the standard results list / temp panel (F2.20).
- Fully cancellable; shows candidate/scan progress; hard cap on files/bytes sent to the API, visible to the user; respects a `.aiignore`-style exclusion file.

**Acceptance criteria**
- [ ] A seeded fixture repo: 10 golden natural-language queries return the expected file in the top 3 results.
- [ ] Data sent to the API never exceeds the displayed cap; excluded paths (`.aiignore`) provably never leave the machine (network audit test).
- [ ] Cancel mid-ranking returns partial results already ranked.
- [ ] Offline: smart mode unavailable with a clear notice; classic find-file unaffected.

---

# H. Claude Code Module (Phase 2 additions)

## F2.27 Live diff review pane

**Expected functionality**
- While an embedded Agent SDK session (Phase 1) runs, a review pane tracks file changes the agent makes in the working directory (watcher + git status when inside a repo): list of touched files with change kind; selecting one shows a live diff (working tree vs HEAD in git; vs session-start snapshot otherwise — the app snapshots small files lazily on first change).
- Post-session review mode: walk all changes, per-file **Keep** / **Revert** (git checkout / snapshot restore); "Revert all". Integrates with permission prompts: a denied write never appears as a change.

**UI**
```
┌ Claude session ──────────────┐┌ Diff: src/api.py (M) ─────────┐
│ M src/api.py        +42 −7   ││ @@ -10,7 +10,9 @@             │
│ A tests/test_api.py +88      ││ -    def fetch(self):         │
│ M README.md         +3  −1   ││ +    async def fetch(self):   │
│                              ││ +        ...                  │
│ [Keep all] [Revert all]      ││ [ Keep ] [ Revert file ]      │
└──────────────────────────────┘└───────────────────────────────┘
```

**Acceptance criteria**
- [ ] Files edited by the agent appear in the list within 1 s of the write; diff matches `git diff` output for repo files.
- [ ] Revert of a non-git file restores byte-identical session-start content; Keep leaves it untouched.
- [ ] Snapshotting is capped (size + count) with clear marking of "no snapshot → revert unavailable" files.
- [ ] Panels and the review pane stay consistent after Keep/Revert-all (auto-refresh).

## F2.28 Claude session manager

**Expected functionality**
- A panel/dialog listing past and active Claude Code sessions for the current project (sourced from the CLI/SDK session store): id, title/first prompt, directory, last activity, status. Actions: **Resume** (opens embedded session with `resume`), **Fork** (new session from that history), **Open transcript** (read-only transcript viewer), **Delete**.
- Active embedded sessions show live status (working/awaiting permission/idle) and can be foregrounded.

**Acceptance criteria**
- [ ] Sessions created both via embedded SDK and via external `claude` in this directory are listed (shared store).
- [ ] Resume continues with full context — verified by asking a question about earlier turns.
- [ ] Transcript viewer renders a long session lazily; search within transcript works.
- [ ] Deleting a session removes it from the list and the store; active sessions cannot be deleted, only stopped first.

## F2.29 Background Claude tasks & notifications

**Expected functionality**
- Headless/SDK tasks (Phase 1 runner) can run in background like file jobs (F2.7): visible in the same jobs panel with live status derived from the stream (current tool, last message summary); completion/failure/permission-request raises a toast + status-line badge; clicking/entering opens the task's transcript or the pending permission dialog.
- Multiple concurrent tasks supported with a configurable cap; per-task budget from AI settings; app-quit warns about running tasks.

**Acceptance criteria**
- [ ] A background task runs to completion while the user browses/copies files; toast appears on finish with an "open result" action.
- [ ] A permission request in a background task interrupts non-intrusively (badge + toast), and the task resumes after the user answers.
- [ ] Task cancel stops the underlying SDK session/process (no orphaned `claude` processes — verified via process table).
- [ ] Concurrency cap enforced; queued tasks start automatically as slots free.

---

## Phase 2 exit checklist
- [ ] All features above land behind the settings UI where configurable, with help pages (F2.15) and both locales (F2.16).
- [ ] Plugin API frozen at 1.0 with archives/SFTP/temp-panel dogfooded on it.
- [ ] No regression of Phase 0/1 acceptance criteria (full suite green).
