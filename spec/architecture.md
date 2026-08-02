# Architecture — MyCom

## Overview

Two independent axes. **The orthodox-FM core** grows: panels and navigation → selection and persistence → file operations → command line and console → viewer and editor. **The AI layer** grows separately: command palette → context-aware chat and smart selection → embedded Claude Code agent. They are bound by an async core under one rule: **a single event loop owns all UI mutation** (the single-writer rule — FAR's deferred `Manager::Commit` lesson translated to Python/Textual). Long work runs in workers; workers never touch widgets directly; results are marshalled back to the loop.

Three architectural rules are load-bearing and non-negotiable:

1. **No data loss.** Source files stay untouched until an operation fully completes; cancellation is always safe.
2. **Offline degradation.** The AI layer is optional at runtime: no key → setup dialog; no network traffic unless an AI feature is explicitly invoked.
3. **Data-driven UI.** Keys, menus, key-bar labels, colors, masks, highlighting, and associations are data (config, theme, registry) — never hard-coded in widgets.

## Components

- **App shell (`app.py`).** The Textual `App`: screen management (panels ↔ console ↔ viewer ↔ editor), global key routing through the keymap registry, startup/shutdown (state flush).
- **Keymap & command registry (`keymap.py`).** One data structure: command → key(s) → context → label. Feeds Textual bindings, the key bar, and (v1) the F9 menus — so labels and menus can never drift from actual bindings. Config `[keybindings]` overlays it.
- **Panels (`panels/`).** The dual-panel system: directory listing with view modes (Brief/Full/Wide), sorting, quick search (v1), highlighting (v1); the selection model; path bar and panel footer. Panels are pure consumers of `fs` snapshots — they never touch the disk directly.
- **Filesystem layer (`fs/`).** Directory scanning into immutable `FileEntry` snapshots, stat/symlink handling, human formatting, (v1) watchdog-based auto-refresh feeding panels through the event loop.
- **File operations engine (`fileops/`).** Plan → execute pipeline for copy/move/delete/mkdir/rename: an async worker walks and executes a plan, reporting `OpProgress` to a progress dialog and consulting a `ConflictPolicy` (the six-choice dialog with sticky "All" answers) and, in v1, a `RecoveryPolicy` (Retry/Skip/Skip All/Cancel). Cancellation at chunk boundaries; cross-device moves delete the source only after a verified copy.
- **Console (`console/`).** The command line under the panels, cd-sync (both directions), and the PTY runner: commands execute in a pseudo-terminal with `script`-style passthrough — the child owns the real terminal (vim/htop work), while output is tee'd into a bounded ring buffer for `Ctrl+O` recall. `cd` is intercepted, never spawned.
- **Viewer (`viewer/`).** Read-only, windowed (mmap/chunked — never whole-file): instant open at any size; wrap toggle; v1 adds hex mode, encodings, search, syntax highlighting, and the quick-view panel mode.
- **Editor (`editor/`).** Textual `TextArea`-based with the trust guards (modified-on-close, external-change-on-save, EOL preservation) and the `$EDITOR` escape hatch (suspend → run → resume → refresh). Deliberately modest: FAR's 20k-LOC editor is not the bar.
- **Dialog kit (`widgets/dialog.py`).** The one modal engine (frame, title, inputs, buttons, hotkeys, stacking) every dialog is built on. Zero ad-hoc modal code is an auditable invariant.
- **Theme (`theme.py` + theme files).** All color lives in theme data; default is "Far classic" lifted from FAR's `colormix.cpp`/`palette.cpp` (see the palette table below); truecolor with a 256-color fallback table.
- **State (`state.py`).** One SQLite DB (WAL) for runtime state and histories; TOML (`config.py`) for user-authored settings. See §Persistence.
- **Platform layer (`platform/`).** The only place OS-conditional code lives: locations/mounts, trash, clipboard, keychain, open-by-association, conpty specifics. POSIX first-class; Windows best-effort.
- **AI module (`ai/`).** The `LLMClient` seam over the Anthropic SDK, the command palette, and (v1) the chat sidebar, explain/summarize, smart selection, and cost guardrails. See §AI layer.
- **Claude Code integration (`claude_code/`).** Three tiers: suspend/attach launcher (v0), headless `claude -p` runner (v1), Agent SDK embedding with TUI permission prompts (v1). See §Claude Code integration.
- **Logging.** Structured `logging` from v0.1, env-configurable — the debugging lifeline for a full-screen TUI.

## Main screen (reference layout)

```
┌ /home/user/projects ──────────────┐┌ /home/user/downloads ─────────────┐
│ Name              Size    Date    ││ Name              Size    Date    │
│ ..                                ││ ..                                │
│▌src               <DIR>  02.08.26▐││ image.png        1.2 MB  01.08.26 │
│ tests             <DIR>  30.07.26 ││ notes.md         3.4 KB  29.07.26 │
│ README.md         2.1 KB 28.07.26 ││                                   │
│ src                               ││ 2 files, 1.2 MB                   │
└ 3 items, 1 selected (2.1 KB) ─────┘└───────────────────────────────────┘
/home/user/projects $ █
 1Help  2Menu  3View  4Edit  5Copy  6RenMov 7MkDir 8Delete 9Menu  10Quit
```

Component hierarchy:

```
MyComApp (textual.App)
├── Horizontal#panel-container
│   ├── FilePanel#left   (PathBar, FileList, PanelFooter)
│   └── FilePanel#right  (PathBar, FileList, PanelFooter)
├── CommandLine
└── KeyBar
+ screens: ConsoleScreen, ViewerScreen, EditorScreen
+ modals:  dialog-kit dialogs (confirm / input / progress / conflict / palette / permission)
```

## The single-writer rule

Textual's event loop is the only writer of UI state. Everything slower than ~100 ms — directory scans of huge trees, file operations, PTY reads, LLM streams, agent sessions — runs in a worker (thread or task) and communicates via messages/`call_from_thread`. Consequences:

- The operation engine reports progress as data (`OpProgress`); the progress dialog renders it.
- Filesystem watchers, PTY readers, and LLM streams are producers; widgets are consumers.
- Cancellation is a flag checked at safe boundaries (file chunk, plan step, stream event) — never a thread kill.

## Panel system

A panel renders an immutable listing snapshot: `list[FileEntry]` + sort + view mode + filter state. User actions produce *intents* (navigate, sort, select); the panel controller applies them by requesting a new snapshot from `fs` and swapping it in. This keeps sorting/selection pure and unit-testable, and it is why auto-refresh (v1) is cheap: a watcher event just triggers the same snapshot-swap path with cursor/selection preservation rules.

**Selection** is the input contract of every file operation: operations consume *selection-else-cursor*, and deselect processed entries on success. `..` is unselectable by invariant.

**View modes** (Brief/Full/Wide) are column layout definitions — data, not subclasses — anticipating v2 custom columns.

## File operations engine

```
walk → OpPlan (entries, byte total) → worker executes step-by-step
                                        │ progress events → ProgressDialog
                                        │ conflict?  → ConflictPolicy (dialog, sticky "All")
                                        │ error?     → RecoveryPolicy (v1: retry/skip/…)
                                        └ cancel flag checked at chunk boundaries
```

Invariants: copy-onto-itself refused at plan time; same-filesystem move degrades to `rename()`; cross-device move = copy + verified delete; metadata preserved via `copystat`; symlinks copied as links. The engine is UI-free — policies are injected, so the whole matrix is testable against tmpfs fixtures without a running app.

## Console, PTY, and cd-sync

The command line is a normal Textual widget; *execution* is not. `Enter` hands the terminal to the child through a PTY with passthrough (the `script(1)` model): raw stdin/stdout proxying gives full interactivity (vim, htop, ctrl-C to the child), while the proxy tees output into a bounded ring buffer that backs `Ctrl+O` recall. On exit: "Press any key" (when there was output), panels restore and both refresh.

`cd` never spawns: it is parsed (quotes, `~`) and applied to the active panel. The prompt always shows the active panel's directory — cd-sync is an invariant, not a feature.

## Viewer and editor

The viewer's contract is *instant at any size*: windowed reads/mmap, `End` seeks — it never loads a file whole. The editor's contract is *trust*: dirty-close guard, external-change guard, EOL and trailing-newline preservation, binary and >10 MB redirect to the viewer. Both get their own keymap context (key-bar labels switch with them). `$EDITOR` via suspend/resume is the permanent escape hatch and the scope guard against editor creep.

## Dialog kit and theme

Every modal is built from one kit: framed window, title, content, button row; `Tab`/arrows focus, hotkey letters, `Enter` default, `Esc` cancel, stacking. The audit rule "zero ad-hoc modal code" keeps interaction uniform — including AI palette and agent permission dialogs, which are deliberately ordinary dialogs.

The default theme is the exact FAR palette (source: `colormix.cpp`/`palette.cpp`, confirmed against a live FAR screenshot):

| Element | Colors |
|---|---|
| Panel background / text | `#00ffff` on `#000080` |
| Panel borders | `#00ffff` on `#000080` |
| Active / inactive path bar | `#000000` on `#008080` / `#00ffff` on `#000080` |
| Column headers | `#ffff00` on `#000080` |
| Cursor row | `#000000` on `#008080` |
| Selected files | `#ffff00` on `#000080` |
| Directories | `#ffffff` on `#000080` |
| Key bar number / label | `#c0c0c0` on `#000000` / `#000000` on `#008080` |
| Dialogs / dialog inputs | `#000000` on `#c0c0c0` / `#000000` on `#008080` |

Plain text only — no emoji, no badges: `\` marks directories, `~` symlinks, space for files. All of this lives in theme files; nothing in widget code.

## Persistence

Two stores with a clear split:

- **`config.toml`** (user-authored, versionable): keybinding overrides, theme choice, behavior flags, associations, AI settings. Read at startup, never written by the app.
- **`state.db`** (SQLite, WAL, app-owned): per-panel path/sort/view, hidden toggle, window state, histories (v1), positions (v2). Schema-versioned with migrations; writes debounced with a final flush on exit; corrupt/missing DB recreates silently — startup is never blocked by state.

Credentials live in neither: `ANTHROPIC_API_KEY` env or the OS keychain.

## Platform layer

`platform/` is the only OS-conditional package: mounts/locations, trash, clipboard (pyperclip + OSC 52 for SSH), keychain access, open-by-association, PTY specifics (conpty on Windows). Everything above it is platform-neutral. POSIX (macOS + Linux) is first-class; Windows is best-effort and may lag.

## AI layer

```
palette / sidebar / smart-select / explain
            │ (context builder: OS, shell, cwd, selection names, capped listings)
        LLMClient  ←— the only seam that imports the Anthropic SDK
            │ streaming, structured outputs, prompt caching (v1), count_tokens (v1)
        Anthropic API   (default model: claude-opus-5)
```

Rules the whole layer obeys:

- **The seam.** Core code depends on `LLMClient`, never the SDK. Tests mock the seam; CI makes zero paid calls.
- **Offline degradation.** No AI object is constructed until an AI feature is invoked; unconfigured entry points show a setup dialog.
- **Confirm before run.** Generated commands render with an explanation and a danger level (recursive delete, `sudo`, `dd`, pipe-to-shell → red warning); execution only via explicit Run, through the same console pipeline as typed commands.
- **Structured outputs** for anything the app consumes programmatically (palette result, v1 selection predicates) — parsed and validated, never regex-scraped from prose.
- **Cost guardrails (v1).** `count_tokens` preflight on large contexts; a per-session budget with a visible meter and a hard stop.
- **Context is minimal by default.** v0 sends names and capped listings, never file contents; v1's sidebar reads contents on demand with size caps and prompt-caches the static prefix.

## Claude Code integration

Three tiers, shipped in order, sharing the principle that *the agent's power is gated by the user's explicit consent*:

1. **Suspend/attach (v0.8).** `Ctrl+K` hands the real terminal to `claude` in the active panel's directory; on exit the TUI resumes and panels refresh. Zero protocol surface — maximum robustness.
2. **Headless runner (v1.10).** `claude -p "<task>" --output-format stream-json` on the selection/cwd; a task pane renders the event stream live; output lands in the viewer; cancel kills the process group.
3. **Agent SDK embedding (v1.10).** `claude-agent-sdk`'s `query(prompt, options)` with the working dir pinned to the active panel; the transcript pane streams assistant text and tool activity; **SDK permission callbacks surface as dialog-kit TUI dialogs** (allow/deny, per-session scoping) — the agent edits nothing without approval. Panel watchers make the agent's edits visible as they happen.

The v2 direction (diff review pane, session manager, an MCP server exposing panel state to any agent) builds on tier 3 and is deliberately out of scope until v1 ships.

## Package layout (target)

```
mycom/
├── app.py            # App shell, screens, startup/shutdown
├── config.py         # TOML settings (user-authored)
├── state.py          # SQLite state store (WAL, migrations)
├── keymap.py         # Command/keymap registry → bindings, key bar, menus
├── theme.py          # Theme loading; theme data files alongside
├── platform/         # ONLY OS-conditional code (posix / windows / darwin)
├── fs/               # Snapshots, scanning, formatting, watchers (v1)
├── panels/           # FilePanel, views, selection, path bar, footer
├── fileops/          # Operation engine, plans, policies (conflict/recovery)
├── console/          # Command line, cd-sync, PTY runner, ring buffer
├── viewer/           # Windowed viewer (+ hex/encodings/search, v1)
├── editor/           # TextArea editor, $EDITOR escape hatch
├── widgets/          # Dialog kit, key bar, shared widgets
├── ai/               # LLMClient seam, palette, sidebar (v1), guardrails (v1)
├── claude_code/      # Launcher (v0), headless runner + SDK embed (v1)
└── utils/            # Pure helpers
```

Migration from the pre-pivot codebase: `panels/`, `widgets/`, `operations/sort.py`, and `utils/fs.py` carry over (sort moves into `fs/`/`panels` semantics unchanged); `mycom/llm/` and `mycom/plugins/` (empty scaffolds of the old concept) are removed — the plugin system is superseded by the v2 plugin API decision, and AI lives in `ai/`. Dependencies: `pyte` is dropped (the PTY passthrough model doesn't emulate), `anthropic` moves behind the seam, `claude-agent-sdk`, `watchdog`, `send2trash`, `pyperclip`, `charset-normalizer`, `pygments` arrive with their phases as declared dependencies or extras.

## Testing and CI

- **Unit tests on pure cores:** sorting, masks, selection invariants, plan builder, conflict/recovery state machines, EOL handling, danger classifier, structured-output schemas — no Textual required.
- **Pilot-driven integration tests:** acceptance criteria are exercised through key presses (`Pilot.press`), not by calling panel methods — the v0.1 lesson: tests that bypass the keyboard certify features that don't exist.
- **Filesystem fixtures over mocks** for fileops (tmpfs trees, huge sparse files, permission traps).
- **No paid calls in CI:** every AI test runs against a mock `LLMClient`; every Claude Code test against a scripted fake binary or mock transport. Real-API and real-agent runs are a manual pre-release checklist.
- **Determinism:** injected clocks for debounce/ETA logic; no real sleeps in tests.
- Lint (`ruff`) and tests gate every phase release; each phase ships the tests that encode its DoD (see [roadmap.md](roadmap.md)).
