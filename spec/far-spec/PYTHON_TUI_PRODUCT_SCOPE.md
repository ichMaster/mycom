# Feature Scope: Python TUI File Manager with LLM & Claude Code Integration

Feature inventory derived from the Far Manager codebase (`far/`, `plugins/`), regrouped and prioritized for a new cross-platform **Python TUI** product. Far itself is Windows-only C++; this document maps its functionality to a Python/POSIX+Windows reality and adds the two new differentiator modules: **LLM integration** and **Claude Code CLI integration**.

## Legend

| Field | Values |
|---|---|
| **Criticality** | 🔴 Core — without it the product is not a dual-panel file manager · 🟠 High — expected by any orthodox-FM user · 🟡 Medium — distinguishes a mature product · 🟢 Low — niche / power-user |
| **Priority** | P0 = MVP · P1 = first public release · P2 = mature product · P3 = later / opportunistic · ✖ = out of scope |
| **Size** | S / M / L / XL — rough implementation effort |

---

## 1. Dual-Panel Core (source: `panel.cpp`, `filelist.cpp`, `treelist.cpp`, `qview.cpp`, `infolist.cpp`, `hilight.cpp`, `dizlist.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Two side-by-side panels, Tab switching, swap, resize | 🔴 Core | P0 | M | The identity of the product |
| File list with column views (brief / medium / full / wide) | 🔴 Core | P0 | M | Start with 2–3 fixed modes |
| Sorting: name, ext, size, mtime; ascending/descending | 🔴 Core | P0 | S | |
| Extended sorting: ctime/atime, owner, numeric, natural, case-sens | 🟡 Medium | P2 | S | Far supports ~14 modes; long tail |
| Selection: Ins/Space, `+`/`-` by mask, invert, select-all | 🔴 Core | P0 | S | Selection model drives all file ops |
| Quick search (type-to-jump, Alt+letter) | 🟠 High | P1 | S | |
| Hidden/system files toggle | 🟠 High | P0 | S | Dotfiles on POSIX |
| Custom column configuration | 🟡 Medium | P2 | M | Far allows fully custom column sets |
| File highlighting by mask/attributes (color groups) | 🟠 High | P1 | M | Big part of the "Far look"; config-driven |
| Sort groups | 🟢 Low | P3 | M | Rarely used even in Far |
| Tree panel (directory tree navigation) | 🟡 Medium | P2 | M | |
| Info panel (drive/dir summary) | 🟢 Low | P3 | S | |
| Quick view panel (Ctrl+Q preview) | 🟠 High | P1 | M | Preview text/images-as-ascii/dir size |
| File descriptions (`descript.ion` / diz) | 🟢 Low | P3 | M | Legacy feature; consider dropping |
| Drives / locations menu (Alt+F1/F2) | 🟠 High | P1 | M | POSIX: mount points, ~, bookmarks; Win: drives |
| Free space / totals in panel footer | 🟠 High | P1 | S | |
| Auto-refresh on FS change | 🟠 High | P1 | M | Far: `filesystemwatcher` → Python: `watchdog` |
| Directory shortcuts (Ctrl+0..9) | 🟡 Medium | P2 | S | |

## 2. File Operations (source: `copy.cpp`, `delete.cpp`, `mkdir.cpp`, `setattr.cpp`, `flink.cpp`, `fileowner.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Copy / Move (F5/F6) with progress, ETA, speed | 🔴 Core | P0 | L | Progress dialog + cancel; the hardest MVP piece to get right |
| Rename (Shift+F6, and F6 to same dir) | 🔴 Core | P0 | S | |
| Delete (F8) with confirmation | 🔴 Core | P0 | S | |
| Delete to trash vs permanent | 🟠 High | P1 | S | `send2trash` on all platforms |
| Mkdir (F7), including nested paths | 🔴 Core | P0 | S | |
| Conflict resolution: overwrite / skip / rename / all | 🔴 Core | P0 | M | |
| Error recovery: retry / skip / skip all / cancel | 🟠 High | P1 | M | Far is exemplary here |
| Attributes / permissions dialog (chmod/chown on POSIX) | 🟠 High | P1 | M | Far's setattr → POSIX mode bits + owner |
| Symlink / hardlink creation | 🟡 Medium | P2 | S | Far also does junctions/reparse — Windows-only |
| Background / queued operations | 🟡 Medium | P2 | L | Far does synchronous; you can do better with asyncio |
| Wipe (secure delete) | 🟢 Low | ✖ | M | Questionable value on SSDs |
| Preserve timestamps/owner on copy | 🟡 Medium | P1 | S | `shutil.copystat` |
| Multi-file rename by pattern | 🟡 Medium | P2 | M | Not in Far core; frequent user wish — good LLM tie-in |

## 3. Command Line & Program Execution (source: `cmdline.cpp`, `execute.cpp`, `usermenu.cpp`, `filetype.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Embedded command line under panels | 🔴 Core | P0 | M | `prompt_toolkit`-style editing |
| Run command, panels hide, show output, return | 🔴 Core | P0 | L | PTY handling; trickier on Windows (winpty/conpty) |
| cd sync: panel follows shell cwd and vice versa | 🔴 Core | P0 | S | |
| Command history (persistent, Alt+F8) | 🟠 High | P1 | S | |
| Ctrl+Enter — insert file name; Ctrl+F — full path | 🟠 High | P1 | S | Muscle memory of every Far user |
| Tab completion (files, commands) | 🟠 High | P1 | M | |
| Enter on file → open by association | 🟠 High | P1 | M | Configurable associations + OS default open |
| User menu (F2) — custom commands | 🟡 Medium | P2 | M | |
| Environment variable expansion | 🟡 Medium | P1 | S | |

## 4. Built-in Viewer (source: `viewer.cpp`, `encoding.cpp`, `uchardet.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Text view (F3), instant open of huge files | 🔴 Core | P0 | M | mmap/chunked reads — never load whole file |
| Hex / dump mode | 🟠 High | P1 | M | |
| Encoding selection + auto-detect | 🟠 High | P1 | M | `charset-normalizer` replaces uchardet |
| Wrap / unwrap, tab width | 🟠 High | P1 | S | |
| Search: text / regex / hex, F7/Shift+F7 | 🟠 High | P1 | M | |
| Go to position / percent / offset | 🟡 Medium | P2 | S | |
| Remember position per file | 🟡 Medium | P2 | S | Far: `poscache` in SQLite |
| Syntax highlighting in viewer | 🟡 Medium | P2 | M | Not in Far core (Colorer plugin); trivial with `pygments` — do it |

## 5. Built-in Editor (source: `editor.cpp`, `fileedit.cpp`, `RegExp.cpp`, `xlat.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Edit (F4), save (F2), save-as (Shift+F2) | 🔴 Core | P0 | L | Decide early: build vs embed an existing widget (Textual `TextArea`) |
| Undo / redo | 🔴 Core | P0 | M | |
| Search / replace with regex | 🟠 High | P1 | M | |
| Stream + columnar (rectangular) block selection | 🟡 Medium | P2 | M | Columnar blocks are a beloved Far feature |
| Encodings + EOL (LF/CRLF) handling on open/save | 🟠 High | P1 | M | |
| Syntax highlighting | 🟠 High | P1 | M | `pygments`/`tree-sitter`; Far needs a plugin for this — ship it built-in |
| Modified-file guard on close / external change detection | 🟠 High | P1 | S | |
| Open in external editor ($EDITOR) | 🟠 High | P1 | S | Cheap escape hatch, reduces pressure on internal editor |
| Xlat (fix text typed in wrong keyboard layout) | 🟢 Low | P3 | S | Beloved in RU/UA community — cheap to add |

## 6. Search & Filtering (source: `findfile.cpp`, `filefilter.cpp`, `filemasks.cpp`, `scantree.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Find file (Alt+F7): masks, subdirs, content search | 🟠 High | P1 | L | Results → temp panel or jump-to |
| File masks language (`*.py,*.md\|*test*`, exclude masks) | 🟠 High | P1 | M | Reused by selection, highlighting, filters, associations |
| Panel filter (Ctrl+I) — show subset by mask/date/size | 🟡 Medium | P2 | M | |
| Content search with encoding awareness / regex | 🟡 Medium | P1 | M | Consider delegating to `ripgrep` if present |
| Semantic / fuzzy search | 🟡 Medium | P2 | M | New — LLM module tie-in |

## 7. Configuration, History, Persistence (source: `configdb.cpp`, `sqlitedb.cpp`, `history.cpp`, `config.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Settings persistence (SQLite, like Far — stdlib `sqlite3`) | 🔴 Core | P0 | M | One DB: settings, histories, positions, plugin data |
| Settings UI (options dialogs) | 🟠 High | P1 | L | Start with a config file + minimal dialog |
| Histories: commands, folders, viewed/edited files, dialog inputs | 🟠 High | P1 | M | With pinning and search, like Far |
| Config export/import (portable profile) | 🟡 Medium | P2 | S | Far does XML; use TOML/JSON |
| Color scheme / theming | 🟡 Medium | P1 | M | Terminal 256/truecolor; ship "Far classic blue" theme |
| Keybinding customization | 🟡 Medium | P2 | M | Ship Far-compatible defaults |

## 8. UI Framework & Window Management (source: `manager.cpp`, `window.cpp`, `dialog.cpp`, `vmenu2.cpp`, `keybar.cpp`, `help.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Key bar (F1..F12 hints at bottom, Ctrl/Alt/Shift aware) | 🟠 High | P0 | S | Instant Far familiarity |
| Modal dialog engine (Far look: double-frame, hotkeys) | 🔴 Core | P0 | M | Textual gives most of this |
| Menus (F9 menu bar, popup menus) | 🟠 High | P1 | M | |
| Window stack: multiple editors/viewers open, F12 switcher | 🟡 Medium | P2 | M | Far's Manager; nice but not MVP |
| Mouse support | 🟡 Medium | P1 | S | Mostly free in Textual |
| Built-in help system (F1, context help) | 🟡 Medium | P2 | M | Markdown instead of `.hlf` |
| Localized UI (en + uk at minimum) | 🟡 Medium | P2 | M | Far generates `.lng` from a template; use gettext |
| Macros / automation (Far: Lua via LuaMacro) | 🟢 Low | P3 | XL | In Python product: user Python snippets bound to keys — much cheaper than Far's macro engine |
| Screen grabber, screensaver, desktop background | 🟢 Low | ✖ | — | Console-era relics |

## 9. Plugins & Extensibility (source: `plugins.cpp`, `plclass.cpp`, `plugapi.cpp`, `plugins/*`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Plugin API (Python entry points: panel providers, commands, hooks) | 🟡 Medium | P2 | L | Design the interfaces early even if shipping later — Far's longevity comes from this |
| Archive browsing as a panel (zip/tar/7z read) | 🟠 High | P1 | M | Far: arclite plugin. Python: `zipfile`/`tarfile`/`libarchive` |
| Archive create/extract operations | 🟠 High | P1 | M | |
| Temp panel (virtual panel of arbitrary files) | 🟡 Medium | P2 | M | Natural target for search results & LLM selections |
| Remote FS: SFTP/FTP as panel | 🟡 Medium | P2 | L | `paramiko`/`fsspec`; Far needs NetBox plugin for this |
| Compare folders / compare files | 🟡 Medium | P2 | M | Far: compare plugin + built-in |
| Process list panel | 🟢 Low | P3 | M | `psutil`; Far: proclist plugin |
| Editor helpers (case change, align, brackets, drawline…) | 🟢 Low | P3 | S | Far ships these as separate plugins; cherry-pick |

## 10. OS Integration (source: `platform.*.cpp`, `elevation.cpp`, `clipboard.cpp`, `network.cpp`, `hotplug.cpp`)

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| System clipboard (copy names/paths/file contents) | 🟠 High | P1 | S | `pyperclip` / OSC 52 for SSH sessions |
| Privilege elevation for protected ops | 🟡 Medium | P2 | M | Far's elevation → `sudo` re-exec or per-op prompt |
| Removable media / mount awareness | 🟢 Low | P3 | M | |
| Network browse (SMB neighborhood) | 🟢 Low | ✖ | L | Windows-era; SFTP panel covers the real need |
| Logging framework (`far.log.*`-style env config) | 🟡 Medium | P1 | S | Python `logging`; invaluable for debugging TUI |

### Explicitly NOT portable / drop from scope
OEM ANSI plugin wrapper (`PluginA.cpp`), WoW64 hook, registry access, NTFS streams/reparse specifics, `vc_crt_fix`, MSI installer, `.hlf`/m4 doc pipeline, ChangelogChecker infra, taskbar progress (replace with terminal progress OSC 9;4 where supported).

---

## 11. NEW: LLM Integration Module

Direct Anthropic API via the official `anthropic` Python SDK (default model `claude-opus-5`, adaptive thinking, streaming). Single API calls / light workflows tier — no agent loop needed here.

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Provider config: API key mgmt (env/keychain), model choice, usage display | 🔴 Core* | P0 | S | *Core for the product's identity |
| AI command palette: natural language → shell command, **confirm-before-run** | 🔴 Core* | P0 | M | The killer demo. Never auto-execute generated commands |
| Explain/summarize file or directory (from viewer or panel) | 🟠 High | P1 | S | Stream into a viewer pane |
| Smart selection: "select all logs older than a week" → mask/selection | 🟠 High | P1 | M | Structured outputs (`output_config.format`) → selection predicate |
| AI rename / multi-rename suggestions | 🟡 Medium | P2 | M | Pairs with §2 pattern rename |
| Chat sidebar with context (current dir, selection, viewed file) | 🟠 High | P1 | L | Prompt caching for the static context prefix |
| AI actions in editor: explain / transform / fix selection | 🟡 Medium | P2 | M | |
| Semantic search over directory contents | 🟡 Medium | P2 | L | |
| Cost guardrails: token counting (`count_tokens`), per-session budget | 🟠 High | P1 | S | |
| Offline degradation (all AI features optional, product fully usable without) | 🔴 Core* | P0 | S | Architectural rule, not a feature |

## 12. NEW: Claude Code Integration Module

Two integration paths, both worth having:
1. **CLI subprocess** — spawn `claude` interactively in an embedded terminal pane (PTY), or headless `claude -p` with JSON/stream-JSON output for programmatic tasks.
2. **Claude Agent SDK for Python** (`claude-agent-sdk`) — the Claude Code harness as a library (`query(prompt, options)`): built-in file/bash/search tools, sessions, hooks, permission callbacks — best for deep, native embedding.

| Feature | Criticality | Priority | Size | Notes |
|---|---|---|---|---|
| Launch Claude Code in current panel dir (embedded PTY pane or external terminal) | 🔴 Core* | P0 | M | Cheapest possible integration, immediate value |
| Headless task runner: `claude -p "..."` on selection, output to viewer | 🟠 High | P1 | M | `--output-format stream-json` → live progress |
| Agent SDK embedding: prompt box → agent works in cwd, streamed transcript pane | 🟠 High | P1 | L | The deep integration; supersedes headless runner UX |
| Pass context: send selected files / panel state into the session | 🟠 High | P1 | M | |
| Permission prompts surfaced as TUI dialogs (SDK permission callbacks) | 🟠 High | P1 | M | Critical for trust; maps to Far-style confirm dialogs |
| Live diff review pane for changes Claude makes | 🟡 Medium | P2 | L | Panels auto-refresh via watchdog as the agent edits |
| Session manager panel: list / resume / fork past sessions | 🟡 Medium | P2 | M | |
| Background tasks + notification when done | 🟡 Medium | P2 | M | |
| Git worktree helper for agent isolation | 🟢 Low | P3 | M | |
| MCP server exposing panel state to any agent | 🟢 Low | P3 | L | Interesting future direction |

---

## 13. Recommended Scope by Phase

**Phase 0 — MVP (the "it feels like Far" bar + one wow feature):**
Dual panels, navigation, sorting, selection · F5/F6/F7/F8 with progress and conflicts · command line with cd-sync and execution · viewer (text) · editor (basic, or $EDITOR) · key bar, dialogs, Far-blue theme · SQLite persistence · **AI command palette** · **"Open Claude Code here"**.

**Phase 1 — first public release:**
Quick view, quick search, highlighting, drives menu, auto-refresh · trash, attributes, error recovery · histories + completion · hex mode, encodings, search in viewer/editor, syntax highlighting · Alt+F7 find file, masks · archives read/write · clipboard · themes · **chat sidebar, explain/summarize, smart selection, cost guardrails** · **headless Claude runner → Agent SDK embedding with TUI permission prompts**.

**Phase 2 — maturity:**
Filters, custom columns, tree/info panels, window stack (F12), settings UI, keybindings, compare, temp panel, SFTP, plugin API, background ops · **AI rename, editor AI actions, semantic search** · **diff review pane, session manager**.

**Phase 3 / opportunistic:** sort groups, diz, xlat, process panel, Python "macros", localization beyond en/uk, MCP surface.

**Out of scope:** wipe, SMB browse, screensaver/grabber/desktop, ANSI plugin compat, all Windows-internals listed in §10.

---

## 14. Technology Notes

| Concern | Far Manager | Recommended Python |
|---|---|---|
| TUI framework | Hand-rolled console engine (`scrbuf`, `interf`) | **Textual** (rich rendering, CSS-like styling, async) — or `prompt_toolkit` if you want lower-level control; Textual recommended |
| Persistence | SQLite (vendored) | stdlib `sqlite3` |
| FS watching | `filesystemwatcher.cpp` | `watchdog` |
| Encoding detect | vendored uchardet | `charset-normalizer` |
| Regex | own `RegExp.cpp` | stdlib `re` / `regex` |
| Archives | arclite (7z.dll) | `zipfile`, `tarfile`, `py7zr`/`libarchive-c` |
| Scripting | Lua (LuaJIT + LuaFAR) | Python itself (user snippets), entry-point plugins |
| LLM | — | `anthropic` SDK: `claude-opus-5`, adaptive thinking, streaming, prompt caching, structured outputs |
| Agent | — | `claude` CLI (interactive/headless) + `claude-agent-sdk` (docs: code.claude.com/docs/en/agent-sdk) |
| Trash | Recycle Bin API | `send2trash` |
| Clipboard | Win32 | `pyperclip` + OSC 52 fallback |

**Key architectural lessons to copy from Far:** deferred window-manager commits (`Manager::Commit`) → in Python, a single async event loop owns all UI mutation; platform isolation layer (`platform.*`) → keep one `platform/` package as the only place OS-conditional code lives; everything user-visible is data-driven (masks, highlighting, associations, menus) — never hard-code.

**Key trap to avoid:** Far's editor/viewer are ~20k LOC each. Do not rebuild them fully — set the MVP bar at "good enough + $EDITOR escape hatch" and invest the saved effort in the LLM/Claude modules, which are the actual reason this product exists.
