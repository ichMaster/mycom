# Roadmap — MyCom

Two versions, built in order: **v0 — MVP** ("it feels like Far" + one wow feature per AI module) → **v1 — first public release** (the features any orthodox-FM user expects, plus the full AI/agent layer). Versions are numbered from 0; phases inside a version are numbered `vA.B` (A = version, B = phase). Each phase lists a **Goal**, a short description, a **Tasks** list, and a **Definition of Done (DoD)**, and ships with the automated tests that encode its DoD (see [architecture.md](architecture.md) §Testing and CI).

The scope is not invented here: v0 implements **Phase 0** of the FAR-derived feature scan and v1 implements **Phase 1** — see [far-spec/PYTHON_TUI_PRODUCT_SCOPE.md](far-spec/PYTHON_TUI_PRODUCT_SCOPE.md) (§13 phase scopes) and the per-feature acceptance criteria in [far-spec/PYTHON_TUI_PHASE0_SPEC.md](far-spec/PYTHON_TUI_PHASE0_SPEC.md) (features `F0.x`, referenced below). Maturity features (Phase 2: filters, custom columns, tree/info panels, SFTP, plugin API, AI rename, semantic search, diff review, session manager) are specified in [far-spec/PYTHON_TUI_PHASE2_SPEC.md](far-spec/PYTHON_TUI_PHASE2_SPEC.md) and deliberately kept out of this roadmap until v1 ships.

**Versioning (`A.B.C`).** Roadmap phase `vA.B` → semver `A.B.0`; a post-release fix on that phase bumps `C`. Releases are cut per phase. Never bump the version without explicit confirmation. The pre-pivot release `0.1.0` (old concept) approximately delivers the new v0.1 scope; the v0.1 retrofit below therefore ships as `0.1.1`, and the first fully new phase (v0.2) ships as `0.2.0`.

**Global acceptance criteria (apply to every phase):**
- Every function reachable with keyboard only; mouse optional.
- No user data lost by a failed or cancelled operation.
- UI never freezes: work > 100 ms runs async with visible progress.
- Works in an 80×24 terminal; truecolor with 256-color fallback.
- Cold start < 500 ms to interactive panels.

---

## v0 — MVP: "it feels like Far" + AI palette + Open Claude Code here

The bar for v0 is emotional, not just functional: a FAR user sits down and their hands already know what to do. Dual panels with views, sorting and selection; F5/F6/F7/F8 with real progress and conflict handling; a command line with cd-sync that runs vim cleanly; a viewer that opens a 1 GB log instantly; a basic editor with a `$EDITOR` escape hatch; the key bar, the dialog kit, the Far-blue theme; SQLite persistence. Plus the two wow features that define the product: the **AI command palette** (F0.18) and **"Open Claude Code here"** (F0.19). Everything implements the acceptance criteria of `F0.1–F0.19` in the Phase 0 spec. Depends on: nothing — this is the foundation.

### v0.1 — Panel core retrofit

**Goal:** the existing panel code fully meets the Phase 0 acceptance criteria for navigation, views, and sorting — and every feature is actually reachable from the keyboard.

The pre-pivot codebase already renders dual panels, navigates, sorts, and filters — but key handling is minimal, config is loaded and ignored, and the integration tests bypass the keyboard. This phase closes the gap between "code exists" and "feature works" (F0.1 navigation, F0.2 column views, F0.3 sorting) and lays the two foundations everything else reuses: a data-driven keymap registry and structured logging.

**Tasks:**
- Keymap registry: one data structure mapping action → key(s) → context, feeding both Textual bindings and (later) the key bar; config `[keybindings]` overrides applied. No hard-coded keys in widgets.
- Wire the config: `show_hidden`, `default_sort`, `default_sort_direction` flow into panel construction; delete dead config paths.
- F0.1: `Ctrl+U` panel swap (paths, cursors, selections); cursor lands on the child directory when going up; unreadable directory (EACCES) → error dialog, stay in place (surface the error instead of the current silent empty panel).
- Panel resize: `Ctrl+Left`/`Ctrl+Right` shift the split (30/50/70), persisted with panel state — the scope §1 "resize" part absent from F0.1's criteria, owned here by decision ([feature-coverage.md](feature-coverage.md) Part 3).
- F0.2: three view modes — Brief / Full / Wide (`Ctrl+1/2/3`), `<DIR>` size column, symlink marking, `…` truncation with full name in the panel footer.
- F0.3: sort keys `Ctrl+F3/F4/F5/F6` with direction toggle, dirs-first invariant, sort glyph (`▲`/`▼`) in the header; sorting stays a pure function in `operations/sort.py`.
- Structured logging (`logging`, env-configurable level/file) wired through app startup — invaluable for debugging a TUI, cheap now, painful later.
- Pilot-driven integration tests: every acceptance check above exercised through key presses, not direct method calls.

**DoD:** all F0.1–F0.3 acceptance boxes check when driven from the keyboard; a 10,000-entry directory navigates with no perceptible lag; config edits visibly change behavior at next start.

**Tests:** unit — keymap resolution/overrides, sort purity (unicode fixtures), view-mode formatting; integration (Pilot) — Tab/Ctrl+U/Enter/Backspace flows, EACCES dialog, cursor-restore on go-up.

### v0.2 — Dialog kit, Far theme, key bar

**Goal:** one reusable modal engine and the exact FAR look — the visual and interactive foundation every later phase builds on.

Implements F0.15 (dialog engine & theme) and F0.14 (key bar). The palette is already applied ad-hoc; this phase moves every color into one theme file and rebuilds the existing dialogs on the kit.

**Tasks:**
- Dialog kit: framed modal with title, text, inputs, button row; `Tab`/arrows focus cycling, hotkey letters, `Enter` = default, `Esc` = cancel; dialogs stack (error over progress).
- Rebuild `ConfirmDialog` / `InputDialog` / `ProgressDialog` on the kit; audit: zero ad-hoc modal code remains.
- Theme file: the FAR palette (from `colormix.cpp`/`palette.cpp`, confirmed against a live FAR screenshot) as the single source of color — no hard-coded colors anywhere; 256-color fallback table.
- Key bar (F0.14): 10 labeled slots generated from the keymap registry per context (panels / viewer / editor / dialog); unassigned slots empty; mouse click triggers the key.
- Panel footer per the reference layout: item count, selection summary, free space placeholder.

**DoD:** all Phase 0 dialogs run on the kit; key-bar labels are generated (drift impossible); the app renders correctly on truecolor and 256-color terminals.

**Tests:** unit — keymap → key-bar label generation, theme fallback mapping; integration (Pilot) — dialog focus order, Esc-cancels-safely, stacked dialogs.

### v0.3 — Selection model, hidden files, SQLite persistence

**Goal:** the selection model that drives all file operations, plus state that survives a restart.

Implements F0.4 (selection), F0.5 (hidden toggle), F0.16 (persistence). Selection is the input contract of every F5/F6/F8 operation, so it lands before them.

**Tasks:**
- Selection: `Ins` and `Space` toggle + move down; `Gray +`/`Gray -` (fallback `Alt+=`/`Alt+-`) mask select/deselect dialogs (glob list, case-insensitive); `Gray *` (fallback `Alt+8`) invert; select-all via mask `*` (decision: no separate key); `..` never selectable; yellow rendering + footer `N selected (X MB)`.
- Selection semantics: per-panel, survives sort/view changes, resets on directory change; operations consume selection-else-cursor and deselect processed entries on success.
- `Ctrl+H` hidden toggle, global, cursor-preserving.
- State DB: SQLite (WAL) at the platform config dir; schema versioning + migrations; debounced writes, final flush on exit; corrupt/missing DB → recreate, never block startup. Stored: per-panel path, sort, view mode, hidden toggle, window state; history tables created (filled in v1).
- Fallback for a vanished panel path: nearest existing ancestor, then `$HOME`.

**DoD:** select-3-delete-3 flow works end-to-end; restart restores both panels' paths, sort, view, hidden state; kill-9 never corrupts the DB.

**Tests:** unit — selection invariants (invert excludes `..`, reset rules), mask matching, DB migration from empty and from v-1 schema; integration — restart round-trip, kill-during-write recovery.

### v0.4 — File operations

**Goal:** F5/F6/F7/F8 with real progress, cancellation, and conflict handling — the hardest MVP piece, done to FAR's standard.

Implements F0.6 (copy/move), F0.7 (mkdir), F0.8 (delete), F0.9 (rename), F0.10 (conflict dialog). All operations run as async workers over a task plan; the UI stays responsive; cancel never corrupts anything.

**Tasks:**
- Operation engine: walk → plan (count, total bytes) → execute in a worker with per-file + total progress (bytes, speed, ETA), `Esc` cancel at chunk boundaries.
- Copy (F5): target pre-filled with passive panel dir; recursive; `shutil.copystat` metadata; symlinks copied as symlinks; copy-onto-itself/into-own-subdir refused.
- Move (F6): same-FS = instant `rename()`; cross-device = copy + verified delete (source removed only after its copy fully succeeded).
- Mkdir (F7): nested `a/b/c`; cursor lands on the new directory.
- Delete (F8): permanent, confirmation (stronger for non-empty dirs), read-only prompt, progress for large trees, cursor to next survivor.
- Rename (Shift+F6): in-place dialog, stem pre-selected; conflict path shared with move.
- Conflict dialog (F0.10): both files' size/mtime with the newer marked; Overwrite / Skip / Rename / Overwrite All / Skip All / Cancel; "All" scoped to the operation; dir-over-dir merges, file-over-dir refused.
- Passive panel refresh on completion.

**DoD:** a 1 GB tree copies byte-identical with preserved mtimes and live progress; cancelled cross-device move leaves the source intact; the scripted 10-conflict fixture exercises all six choices correctly.

**Tests:** unit — plan builder, conflict policy state machine, same-FS detection; integration — copy/move/delete/rename fixtures incl. cancellation mid-tree, read-only delete, merge conflicts (tmpfs fixtures, no mocks).

### v0.5 — Command line, execution, cd-sync

**Goal:** the shell is one keystroke away and panels always follow the shell — the orthodox-FM covenant.

Implements F0.11. Printable characters type into the command line (FAR behavior); `Enter` runs the command in a PTY on a full-screen console surface where interactive programs (vim, htop, `git rebase -i`) work; on exit, panels return and refresh.

**Tasks:**
- Command line widget under the panels: prompt shows active panel CWD; printable keys route here, navigation keys stay with the panel.
- PTY runner (script-style passthrough): child gets the real terminal semantics; output tee'd into a ring buffer (100k-line safe); `Press any key` on exit (skipped when no output); non-zero exit code surfaced.
- `Ctrl+O`: toggle panels / last console output.
- `cd` interception (incl. `~`, quoted paths): changes the active panel directory with no subprocess; errors inline.
- cd-sync both ways: panel navigation updates the prompt; process CWD is always the active panel dir.
- Both panels refresh listings after any external command returns.

**DoD:** `vim file` round-trips cleanly back to panels showing the new mtime; `cd /tmp` is instant with no spawn; a 100k-line command neither hangs nor exhausts memory.

**Tests:** unit — cd parser (quoting, `~`), ring buffer; integration — scripted PTY sessions (non-interactive), `Ctrl+O` recall, exit-code surfacing; manual matrix — vim/htop under tmux and plain terminal on macOS + Linux.

### v0.6 — Viewer and editor

**Goal:** `F3` opens anything instantly; `F4` edits safely; `$EDITOR` is always there.

Implements F0.12 (viewer) and F0.13 (editor). The viewer never loads a whole file; the editor is Textual `TextArea` with the guards that make it trustworthy — and the escape hatch that keeps scope honest.

**Tasks:**
- Viewer: windowed reads/mmap; UTF-8 with `errors="replace"`, latin-1 fallback; arrows/PgUp/PgDn/Home/`End`-to-EOF instant; `F2` wrap toggle preserving position; `F6` → editor; status bar (name, size, offset, %).
- Editor: `TextArea`-based; undo/redo; `F2` save, `Shift+F2` save-as; modified-guard on close (Save/Discard/Cancel); EOL style (LF/CRLF, dominant-mixed) detected and preserved; trailing-newline preserved; UTF-8 only with binary refusal → viewer; >10 MB redirect → viewer.
- External-change guard: file touched on disk since open → warn before save.
- `Alt+F4` opens `$EDITOR` (suspend → run → resume → refresh); config `editor.external_default` makes `F4` do this.
- Key bar contexts for viewer and editor.

**DoD:** 1 GB log opens < 300 ms with bounded RSS; CRLF round-trip produces no spurious diff; quitting dirty always prompts; `$EDITOR` round-trip works in tmux.

**Tests:** unit — EOL detection/preservation, window paging math, binary detection; integration — view/edit/save round-trips on fixtures (huge file, CRLF, mixed EOL, binary), external-modification guard.

### v0.7 — AI foundation: provider config + command palette

**Goal:** the first wow feature — natural language becomes a shell command, never executed without explicit consent — on an AI layer the whole product can trust.

Implements F0.17 (provider config & offline degradation) and F0.18 (AI command palette). Everything goes through the `LLMClient` seam; the app remains fully functional with no key and generates zero network traffic unless AI is invoked.

**Tasks:**
- `LLMClient` seam over the Anthropic SDK: streaming, adaptive thinking defaults, model from config (default `claude-opus-5`); mockable; the core never imports the SDK directly.
- Credentials: `ANTHROPIC_API_KEY` env → OS keychain (set via in-app command); never plaintext config. Unconfigured AI entry point → one-time setup dialog, not an error.
- Offline rule enforced by design: no AI object constructed until first invocation; tcpdump-clean non-AI sessions.
- Palette (`Ctrl+Space`): intent input → streamed response with proposed command + one-line explanation + danger level; context sent: OS, shell, CWD, selected file *names*, truncated listing — never file contents in v0.
- Danger heuristics: recursive delete, `chmod -R`, `dd`, `sudo`, pipe-to-shell → red flag + explicit extra warning before Run is possible.
- Actions: Run (via the v0.5 pipeline) / Edit (insert into command line) / Copy / Cancel; API errors inline, palette stays usable.
- Structured output for `{command, explanation, danger}` via `output_config.format`.

**DoD:** the 10-case golden set (list/find/archive/rename/git) produces commands that run correctly in panel context; nothing ever executes without explicit Run; offline invocation degrades to a clear inline error.

**Tests:** unit — danger classifier, context builder (quoting/spaces), structured-output parsing against a mock `LLMClient`; integration — palette flow with mocked streaming (first tokens < 2 s asserted via fake clock); zero paid calls in CI.

### v0.8 — Open Claude Code here

**Goal:** the second wow feature — the coding agent one keystroke away from any directory — completing the MVP.

Implements F0.19. The cheapest possible Claude Code integration with immediate value: suspend the TUI, hand the terminal to `claude` in the active panel's directory, resume and refresh when it exits.

**Tasks:**
- `Ctrl+K` (and F9-menu entry when menus land in v1): launch `claude` in the active panel dir via suspend/attach; full colors, resize, Ctrl+C owned by `claude`.
- On exit: resume TUI, refresh both panels (the agent likely changed files).
- Binary discovery on `PATH`; absent → informative install dialog (docs link), no crash, no dead menu item.
- Config option: launch in an external terminal instead (macOS Terminal/iTerm, `$TERMINAL` on Linux).
- MVP release notes + README refresh: v0 = Phase 0 complete.

**DoD:** a session starts in the correct directory, runs fully interactively, and on exit the panels show the agent's changes without manual refresh; missing binary degrades gracefully; works under tmux and plain terminals on macOS + Linux.

**Tests:** unit — binary discovery, launch-command construction (internal/external); integration — fake `claude` script round-trip (creates a file → panels show it); manual matrix — real `claude` in tmux/plain on macOS + Linux.

---

## v1 — First public release: the orthodox-FM expectation bar + the full AI layer

v0 makes it feel like Far; v1 makes it *complete enough to publish*: quick search, highlighting, drives menu, auto-refresh, trash, error recovery, histories, completion, hex/encodings/search/syntax in viewer and editor, find-file, archives, clipboard, menus, themes — and the AI layer grows from one palette into a context-aware assistant (chat sidebar, explain/summarize, smart selection, cost guardrails) and a real agent host (headless runner → Agent SDK embedding with TUI permission prompts). Scope: the Phase 1 column of the product scope (§13). Depends on: all of v0.

### v1.1 — File masks engine, quick search, highlighting

**Goal:** the shared masks engine plus the two features that make panels *feel* alive: type-to-jump and color groups.

**Tasks:**
- Masks engine (`*.py,*.md|*test*`, exclude part): one implementation reused by selection dialogs, highlighting, find-file, and (v2) filters; documented grammar.
- Quick search: `Alt+letter` type-to-jump within the panel, incremental, `Esc`/navigation clears.
- File highlighting groups: config-driven mask/attribute → color (dirs white, executables green, archives magenta, temp brown — FAR defaults shipped as data).
- Panel footer completion: free space + directory totals.
- Retrofit selection dialogs (v0.3) onto the masks engine.

**DoD:** highlighting matches FAR defaults out of the box and is fully user-editable; quick search jumps correctly in a 10k-entry dir; one masks implementation serves all consumers.

**Tests:** unit — masks grammar (include/exclude, unicode, case rules), highlight resolution precedence; integration — quick-search key flows.

### v1.2 — Drives menu, auto-refresh, clipboard, mouse

**Goal:** the panel talks to the outside world: locations, live FS changes, the system clipboard, and the mouse.

**Tasks:**
- Drives/locations menu (`Alt+F1`/`Alt+F2`): POSIX mount points + `~` + bookmarks; Windows drives best-effort.
- Auto-refresh: `watchdog` observers on both panel dirs, debounced; cursor and selection preserved across refreshes.
- Clipboard: copy names / full paths / file contents; `pyperclip` with OSC 52 fallback for SSH sessions.
- Mouse: click-to-focus, click-to-cursor, double-click enter, wheel scroll, key-bar clicks (mostly free in Textual — audit and fix gaps).

**DoD:** external `touch`/`rm` appears in the panel within a second without losing cursor or selection; locations menu navigates on macOS and Linux; copy-path works over SSH.

**Tests:** unit — locations provider per platform (mocked mounts), debounce logic; integration — watchdog fixture (create/delete during session), clipboard round-trip where the environment allows.

### v1.3 — Resilient file operations

**Goal:** file operations grow FAR's exemplary error manners: trash, retry, and an attributes dialog.

**Tasks:**
- Delete to trash (`send2trash`) as the `F8` default; `Shift+F8` permanent; config toggle; release-notes the change from v0.
- Error recovery in the operation engine: per-file failure → Retry / Skip / Skip All / Cancel dialog, operation continues correctly.
- Attributes dialog (`Ctrl+A`): POSIX mode bits + owner (chmod/chown) for cursor or selection, recursive option.
- Verify + pin metadata preservation on copy (mtime, permissions) with explicit tests.

**DoD:** a copy over a directory with one unreadable file completes via Skip with an accurate summary; trashed files are restorable via the OS; chmod on a selection works recursively.

**Tests:** unit — recovery state machine, mode-bit editing; integration — EACCES-mid-copy fixture, trash round-trip, recursive chmod.

### v1.4 — Histories, completion, command-line niceties

**Goal:** the command line gets a memory and the muscle-memory keys every FAR user expects.

**Tasks:**
- Persistent histories in the state DB (commands, folders, viewed/edited files, dialog inputs) with pinning and search (`Alt+F8` commands, `Alt+F12` folders).
- Tab completion: files in context + commands on PATH.
- `Ctrl+Enter` — insert cursor file name into the command line; `Ctrl+F` — full path.
- Environment variable expansion in commands and dialog paths.
- `Enter` on a file → open by association: configurable associations (masks engine) + OS default open fallback.

**DoD:** histories survive restart and are searchable; `Ctrl+Enter` quoting is correct for names with spaces; associations open the right app with OS fallback.

**Tests:** unit — history store (dedup, pin, cap), completion candidates, association resolution; integration — history navigation key flows.

### v1.5 — Viewer and editor II

**Goal:** the viewer and editor graduate from MVP to daily-driver: hex, encodings, search, syntax color, quick view.

**Tasks:**
- Viewer hex/dump mode (`F4` in viewer) with offset column.
- Viewer tab-width setting (configurable, default 8) — the scope §4 "tab width" part absent from F0.12/F1.x, owned here by decision ([feature-coverage.md](feature-coverage.md) Part 3).
- Encoding: auto-detect via `charset-normalizer` + manual selection menu (`Shift+F8`); applies to viewer and editor open/save.
- Search: viewer text/regex/hex (`F7`/`Shift+F7`); editor find/replace with regex.
- Syntax highlighting via `pygments` in both viewer and editor (FAR needs a plugin for this — we ship it built-in).
- Quick view panel (`Ctrl+Q`): passive panel previews the cursor file (text head, dir size async) reusing viewer machinery.

**DoD:** a Windows-1251 file auto-detects and round-trips through the editor unchanged; hex search finds a byte pattern in a large binary; quick view updates as the cursor moves without lag.

**Tests:** unit — detection fixtures (utf-8/1251/latin-1/koi8), hex search, replace-with-groups; integration — quick-view follows cursor, encoding menu flow.

### v1.6 — Find file and content search

**Goal:** `Alt+F7` — the classic answer to "where is it?", with modern content search underneath.

**Tasks:**
- Find file dialog: masks (v1.1 engine), start dir, subdirs toggle, optional content substring/regex.
- Content search: delegate to `ripgrep` when present (encoding-aware fallback in Python otherwise).
- Results list: navigate → jump panel to file; foundation shaped for a v2 temp panel.
- Async with live count + cancel.

**DoD:** finding `*.py` containing a pattern across a large tree streams results with a responsive cancel; jump lands the panel on the hit.

**Tests:** unit — query builder (rg args, fallback), result parsing; integration — fixture-tree searches incl. cancellation.

### v1.7 — Archives

**Goal:** archives behave like directories — browse in, copy out, create new — without leaving the panels.

**Tasks:**
- Archive panel provider: enter zip/tar(.gz/.bz2/.xz) as a virtual read-only panel (stdlib `zipfile`/`tarfile`); nested navigation, viewer works on members.
- Extract: `F5` from inside an archive copies members out through the normal operation engine (progress, conflicts).
- Create: `Shift+F1` packs the selection (zip/tar.gz) with progress.
- 7z read via `py7zr` if installed (optional extra), degrade gracefully.

**DoD:** enter a 10k-member zip instantly, view a member, extract a subtree with progress and conflicts; create an archive from a selection and get byte-correct content.

**Tests:** unit — virtual listing mapping, path safety (zip-slip refusal); integration — browse/extract/create round-trips on fixtures.

### v1.8 — Menus and theming

**Goal:** discoverability and identity: the F9 menu bar and a real theme system.

**Tasks:**
- F9 menu bar + popup menus (dialog-kit based): every feature reachable through menus, generated from the same command registry as keys (labels show shortcuts).
- Theme system: themes as data files; ship "Far classic blue" (default) + one dark and one light-terminal-safe alternative; live switch; 256-color audit.
- Help screen (`F1`): generated keymap reference (full help system stays v2).

**DoD:** every roadmap feature is reachable via F9; switching themes recolors the whole app live with zero hard-coded colors remaining (audited).

**Tests:** unit — menu generation from the registry (drift impossible), theme file parsing/fallback; integration — menu navigation key flows.

### v1.9 — AI II: chat sidebar, explain/summarize, smart selection, guardrails

**Goal:** the AI layer becomes context-aware and cost-safe — the assistant sees what you see.

**Tasks:**
- Chat sidebar: a toggleable pane with streamed conversation; context = current dir, selection, viewed file (names + on-demand contents with size caps); prompt caching for the static context prefix.
- Explain/summarize: from panel (`file/dir`) or viewer (current file) → streamed into a viewer pane.
- Smart selection: natural language → structured-output selection predicate (masks + size/date ranges) previewed before applying; applies through the v0.3 selection model.
- Cost guardrails: `count_tokens` preflight for large contexts, per-session token budget with a visible meter, hard stop + dialog at the cap.
- All features honor the offline rule and the `LLMClient` seam.

**DoD:** "select all logs older than a week" selects exactly those files after preview; summarize on a directory streams within 2 s; the budget meter stops a runaway session at the cap.

**Tests:** unit — predicate schema validation/compilation, budget accounting, context assembly caps; integration — sidebar and smart-selection flows against a mock streaming client; zero paid CI calls.

### v1.10 — Claude Code II: headless runner and Agent SDK embedding

**Goal:** from "open a terminal for the agent" to "the agent is a first-class citizen of the file manager" — this phase is the public release.

**Tasks:**
- Headless runner: `claude -p "<task>"` on the selection/cwd with `--output-format stream-json`; live progress rendered in a task pane; result into viewer; cancel kills the process group.
- Agent SDK embedding (`claude-agent-sdk`): prompt box → agent session working in the active dir; streamed transcript pane (assistant text, tool calls, results).
- Permission prompts: SDK permission callbacks surfaced as dialog-kit TUI dialogs (allow / deny with message), honoring the confirm-before-run principle; per-session "always allow" scoping.
- Context passing: selected files / panel state injected into the session prompt.
- Panels auto-refresh (v1.2 watchers) as the agent edits — the live-diff review pane itself stays v2.
- Release engineering: PyPI packaging, `pipx`/`uv tool` install path, README + docs site refresh → **first public release**.

**DoD:** a headless task streams progress and lands its output in the viewer; an embedded session edits files only after TUI approval, with panels refreshing live; `uv tool install mycom` works on a clean machine.

**Tests:** unit — stream-json parser, permission-callback bridging, context injection; integration — scripted SDK session with a mock transport exercising the full approve/deny matrix; manual — real end-to-end agent session on macOS + Linux.

---

## Future (v2+, not scheduled)

Held in [far-spec/PYTHON_TUI_PHASE2_SPEC.md](far-spec/PYTHON_TUI_PHASE2_SPEC.md) with full acceptance criteria, deliberately out of this roadmap: panel filters, extended sorting, custom columns, tree/info panels, window stack (F12), settings UI, keybinding editor, folder/file compare, temp panel, SFTP panel, background operation queue, plugin API — and the AI maturity set: AI rename, editor AI actions, semantic search, the diff review pane, and the agent session manager. Opportunistic ideas (sort groups, xlat, process panel, Python user-snippets, localization beyond en/uk, an MCP server exposing panel state) live in the product scope §13.
