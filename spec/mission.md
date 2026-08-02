# Mission — MyCom

## In one sentence

MyCom is a keyboard-first, dual-panel TUI file manager in the spirit of FAR Manager — written in Python on Textual, cross-platform, with two built-in differentiators no orthodox file manager has: an AI command palette and first-class Claude Code integration.

## What we are building

A faithful heir to the orthodox file manager: two panels, F-key operations, a command line under the panels, a built-in viewer and editor, the classic Far-blue look — everything a FAR or Midnight Commander user's muscle memory expects, running natively on macOS and Linux (Windows best-effort). The feature scope is not invented: it is derived from a systematic scan of the real FAR Manager codebase ([far-spec/PYTHON_TUI_PRODUCT_SCOPE.md](far-spec/PYTHON_TUI_PRODUCT_SCOPE.md)), regrouped and re-prioritized for a Python/POSIX reality.

On top of that proven core, two new modules — the actual reason this product exists:

1. **LLM integration** — an AI command palette (natural language → shell command, never auto-executed), later a context-aware chat sidebar, explain/summarize, and smart selection. Direct Anthropic API, streaming, structured outputs.
2. **Claude Code integration** — from "open Claude Code in this directory" (one keystroke, panels refresh when the agent exits) to a headless task runner and full Agent SDK embedding with TUI permission prompts.

The product is 100 % functional without an API key or network. AI is a layer, not a dependency.

## For whom

- Developers and system administrators who live in the terminal.
- FAR Manager / Midnight Commander users who want the same muscle memory on macOS and Linux.
- Power users who want files, shell, and an AI agent in one workspace instead of three windows.

## Principles

- **It feels like Far.** Default keys mirror FAR (`F5` copy, `Ins` select, `Ctrl+U` swap); the default theme is the exact FAR palette taken from `colormix.cpp`/`palette.cpp`; the key bar, dialogs, and panel footers follow FAR's layout. Familiarity is a feature.
- **Keyboard first.** Every function is reachable without a mouse; the mouse is optional everywhere.
- **No data loss, ever.** Source files stay untouched until an operation fully completes; cancel is always safe; conflicts always ask.
- **The UI never freezes.** One async event loop owns all UI mutation (the single-writer rule); anything over 100 ms runs as a worker with visible progress and a reachable Cancel.
- **Offline degradation.** Every AI entry point is optional. No key → a setup dialog, never a traceback. No network traffic unless an AI feature is explicitly invoked.
- **Confirm before run.** A generated shell command is never executed without an explicit user action; destructive patterns are flagged red before Run is even possible. The same rule governs the embedded agent: Claude Code's tool use surfaces as TUI permission dialogs.
- **Data-driven, never hard-coded.** Masks, highlighting, associations, menus, keymaps, and colors live in data (config + theme files), not in code — the lesson of FAR's longevity.
- **Build vs embed.** FAR's editor and viewer are ~20k LOC each; we do not rebuild them. Textual's `TextArea` plus a `$EDITOR` escape hatch set the bar, and the saved effort goes into the AI modules.
- **Platform isolation.** One `platform/` package is the only place OS-conditional code lives — FAR's own architecture lesson.
- **Core before chrome.** SQLite persistence, the masks engine, and the dialog kit are foundations shared by many features; they are built once, early, and reused everywhere.

## Non-goals

- **Not a FAR port.** No C++ internals, no Windows-era relics: SMB neighborhood browse, screen saver / grabber, secure wipe, OEM plugin compatibility, registry access, NTFS streams are all explicitly out of scope.
- **Not an IDE and not a terminal multiplexer.** The console surface runs commands and full-screen programs; tmux does the rest.
- **No plugin marketplace yet.** A public plugin API is a maturity-phase (v2+) topic; v0–v1 ship built-in capability only (archives via stdlib, not plugins).
- **No Windows first-class support in v0–v1.** POSIX (macOS + Linux) is first-class; Windows is best-effort via conpty and is allowed to lag.
- **Not a general AI chat app.** The AI features exist to manipulate files and run commands in context — not to replace a chat client.

## Glossary

- **Orthodox file manager** — the two-panel, keyboard-driven file manager school founded by Norton Commander and perfected by FAR.
- **Active / passive panel** — the panel with the cursor vs. the other one; file operations default their target to the passive panel's directory.
- **Selection** — the explicitly marked set of files (`Ins`, mask select); operations act on the selection when non-empty, else on the cursor file.
- **File masks** — FAR's pattern language (`*.py;*.md|*test*`) reused by selection, highlighting, filters, and find-file (v1).
- **Key bar** — the bottom row of 10 F-key slots with context-sensitive labels, generated from the keymap so labels can never drift from bindings.
- **Console surface** — the full-screen output view a command runs in; `Ctrl+O` recalls the last output after returning to panels.
- **cd-sync** — the invariant that the command line's working directory always equals the active panel's directory, in both directions.
- **Dialog kit** — the one reusable modal engine (frame, title, inputs, buttons, hotkeys) every dialog is built on; zero ad-hoc modal code.
- **Far-classic theme** — the default palette lifted from FAR's source: blue panels `#000080`, cyan frames `#00ffff`, grey dialogs `#c0c0c0`, yellow selection `#ffff00`.
- **State DB** — the single SQLite database (WAL) holding panel state, histories, and positions; distinct from the user-authored TOML settings file.
- **LLMClient seam** — the thin interface between the core and the Anthropic SDK; everything AI goes through it, so tests mock it and no paid call ever runs in CI.
- **AI command palette** — `Ctrl+Space`: natural-language intent → proposed shell command + explanation + danger level, with Run / Edit / Copy / Cancel.
- **Smart selection** — natural language → a selection predicate ("select all logs older than a week"), via structured outputs (v1).
- **Chat sidebar** — the context-aware Claude chat pane that knows the current directory, selection, and viewed file (v1).
- **Claude Code** — Anthropic's CLI coding agent (`claude`); MyCom launches it in the active directory (v0), drives it headlessly (`claude -p`, v1), and embeds it via the Agent SDK (v1).
- **Permission prompt** — the TUI dialog surfacing an embedded agent's tool-use request (edit file, run command) for explicit user approval.
