# Feature Coverage — MyCom

Traceability matrix between the FAR-derived feature inventory in
[far-spec/PYTHON_TUI_PRODUCT_SCOPE.md](far-spec/PYTHON_TUI_PRODUCT_SCOPE.md) and the phases in
[roadmap.md](roadmap.md). Two views: **Part 1** audits that every scope feature has an owner
(a `vA.B` phase, v2+, or an explicit out-of-scope mark); **Part 2** inverts it into per-phase
test checklists — when a phase's release is cut, open its checklist and tick features as you
verify them.

Rules of this document:

- **Feature names are verbatim** from PYTHON_TUI_PRODUCT_SCOPE.md — do not rename them here.
- **F#** is the feature's number exactly as in the detailed specs — `F0.x` from
  [far-spec/PYTHON_TUI_PHASE0_SPEC.md](far-spec/PYTHON_TUI_PHASE0_SPEC.md), `F1.x` from
  [far-spec/PYTHON_TUI_PHASE1_SPEC.md](far-spec/PYTHON_TUI_PHASE1_SPEC.md), `F2.x` from
  [far-spec/PYTHON_TUI_PHASE2_SPEC.md](far-spec/PYTHON_TUI_PHASE2_SPEC.md). A scope row that maps
  to two spec features lists both (e.g. `F1.10+F1.22`).
- **Priority** is the scope file's priority (P0 = MVP, P1 = first public release, P2 = mature,
  P3 = later, ✖ = out of scope).
- **Phase** is where the roadmap delivers the feature. `v2+` = specified in the PHASE2 spec or
  scope §13, deliberately unscheduled. Items marked *(partial)* or *(pulled forward)* are
  explained in Part 3.
- **Tested** is yours: `[ ]` → `[x]` as you verify a shipped feature by hand against its F-section
  acceptance criteria. P2+/✖ rows have `—`.
- **Maintenance:** any roadmap change that moves a feature updates this file in the same commit.

---

## Part 1 — Coverage matrix (by scope section)

### §1 Dual-Panel Core

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.1 | Two side-by-side panels, Tab switching, swap, resize | P0 | v0.1 *(incl. resize `Ctrl+Left/Right` — decision, Part 3 #2)* | [ ] |
| F0.2 | File list with column views (brief / medium / full / wide) | P0 | v0.1 (Brief/Full/Wide) | [ ] |
| F0.3 | Sorting: name, ext, size, mtime; ascending/descending | P0 | v0.1 | [ ] |
| F2.2 | Extended sorting: ctime/atime, owner, numeric, natural, case-sens | P2 | v2+ | — |
| F0.4 | Selection: Ins/Space, `+`/`-` by mask, invert, select-all | P0 | v0.3 *(incl. Space; select-all = mask `*` — decision, Part 3 #3)* | [ ] |
| F1.1 | Quick search (type-to-jump, Alt+letter) | P1 | v1.1 | [ ] |
| F0.5 | Hidden/system files toggle | P0 | v0.3 | [ ] |
| F2.3 | Custom column configuration | P2 | v2+ | — |
| F1.2 | File highlighting by mask/attributes (color groups) | P1 | v1.1 | [ ] |
| — | Sort groups | P3 | v2+ / opportunistic | — |
| F2.4 | Tree panel (directory tree navigation) | P2 | v2+ | — |
| F2.5 | Info panel (drive/dir summary) | P3 | v2+ | — |
| F1.3 | Quick view panel (Ctrl+Q preview) | P1 | v1.5 | [ ] |
| — | File descriptions (`descript.ion` / diz) | P3 | v2+ / likely dropped | — |
| F1.4 | Drives / locations menu (Alt+F1/F2) | P1 | v1.2 | [ ] |
| F1.5 | Free space / totals in panel footer | P1 | v1.1 *(placeholder from v0.2)* | [ ] |
| F1.6 | Auto-refresh on FS change | P1 | v1.2 | [ ] |
| F2.6 | Directory shortcuts (Ctrl+0..9) | P2 | v2+ *(read-only list appears in F1.4 menu)* | — |

### §2 File Operations

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.6 | Copy / Move (F5/F6) with progress, ETA, speed | P0 | v0.4 | [ ] |
| F0.9 | Rename (Shift+F6, and F6 to same dir) | P0 | v0.4 | [ ] |
| F0.8 | Delete (F8) with confirmation | P0 | v0.4 (permanent in v0; trash arrives v1.3) | [ ] |
| F1.7 | Delete to trash vs permanent | P1 | v1.3 | [ ] |
| F0.7 | Mkdir (F7), including nested paths | P0 | v0.4 | [ ] |
| F0.10 | Conflict resolution: overwrite / skip / rename / all | P0 | v0.4 | [ ] |
| F1.8 | Error recovery: retry / skip / skip all / cancel | P1 | v1.3 | [ ] |
| F1.9 | Attributes / permissions dialog (chmod/chown on POSIX) | P1 | v1.3 | [ ] |
| F2.8 | Symlink / hardlink creation | P2 | v2+ | — |
| F2.7 | Background / queued operations | P2 | v2+ | — |
| — | Wipe (secure delete) | ✖ | out of scope | — |
| F0.6 | Preserve timestamps/owner on copy | P1 | v0.4 *(pulled forward; re-verified in v1.3)* | [ ] |
| F2.9 | Multi-file rename by pattern | P2 | v2+ | — |

### §3 Command Line & Program Execution

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.11 | Embedded command line under panels | P0 | v0.5 | [ ] |
| F0.11 | Run command, panels hide, show output, return | P0 | v0.5 | [ ] |
| F0.11 | cd sync: panel follows shell cwd and vice versa | P0 | v0.5 | [ ] |
| F1.10 | Command history (persistent, Alt+F8) | P1 | v1.4 | [ ] |
| F1.11 | Ctrl+Enter — insert file name; Ctrl+F — full path | P1 | v1.4 | [ ] |
| F1.12 | Tab completion (files, commands) | P1 | v1.4 | [ ] |
| F1.13 | Enter on file → open by association | P1 | v1.4 *(`.zip` rule verifiable after v1.7 — see Part 3)* | [ ] |
| F2.13 | User menu (F2) — custom commands | P2 | v2+ | — |
| F1.11 | Environment variable expansion | P1 | v1.4 | [ ] |

### §4 Built-in Viewer

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.12 | Text view (F3), instant open of huge files | P0 | v0.6 | [ ] |
| F1.14 | Hex / dump mode | P1 | v1.5 | [ ] |
| F1.15 | Encoding selection + auto-detect | P1 | v1.5 | [ ] |
| F0.12 | Wrap / unwrap, tab width | P1 | v0.6 wrap; v1.5 tab width *(decision, Part 3 #4)* | [ ] |
| F1.16 | Search: text / regex / hex, F7/Shift+F7 | P1 | v1.5 | [ ] |
| F2.17 | Go to position / percent / offset | P2 | v2+ | — |
| F2.17 | Remember position per file | P2 | v2+ *(session-scoped encoding memory in F1.15)* | — |
| F2.17 | Syntax highlighting in viewer | P2 | v1.5 *(pulled forward)* | [ ] |

### §5 Built-in Editor

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.13 | Edit (F4), save (F2), save-as (Shift+F2) | P0 | v0.6 | [ ] |
| F0.13 | Undo / redo | P0 | v0.6 | [ ] |
| F1.17 | Search / replace with regex | P1 | v1.5 | [ ] |
| F2.18 | Stream + columnar (rectangular) block selection | P2 | v2+ | — |
| F0.13+F1.18 | Encodings + EOL (LF/CRLF) handling on open/save | P1 | v0.6 EOL; v1.5 encodings *(split — see Part 3)* | [ ] |
| F1.19 | Syntax highlighting | P1 | v1.5 | [ ] |
| F0.13 | Modified-file guard on close / external change detection | P1 | v0.6 *(pulled forward)* | [ ] |
| F0.13 | Open in external editor ($EDITOR) | P1 | v0.6 *(pulled forward)* | [ ] |
| — | Xlat (fix text typed in wrong keyboard layout) | P3 | v2+ / opportunistic | — |

### §6 Search & Filtering

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F1.21 | Find file (Alt+F7): masks, subdirs, content search | P1 | v1.6 | [ ] |
| F1.20 | File masks language (`*.py,*.md\|*test*`, exclude masks) | P1 | v1.1 | [ ] |
| F2.1 | Panel filter (Ctrl+I) — show subset by mask/date/size | P2 | v2+ | — |
| F1.21 | Content search with encoding awareness / regex | P1 | v1.6 | [ ] |
| F2.26 | Semantic / fuzzy search | P2 | v2+ | — |

### §7 Configuration, History, Persistence

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.16 | Settings persistence (SQLite, like Far — stdlib `sqlite3`) | P0 | v0.3 | [ ] |
| F2.10 | Settings UI (options dialogs) | P1→P2 | v2+ *(resolved — see Part 3: P1 = config file + F1.23 theme picker)* | — |
| F1.10+F1.22 | Histories: commands, folders, viewed/edited files, dialog inputs | P1 | v1.4 | [ ] |
| F2.12 | Config export/import (portable profile) | P2 | v2+ | — |
| F0.15+F1.23 | Color scheme / theming | P1 | v1.8 *(Far-classic default from v0.2)* | [ ] |
| F2.11 | Keybinding customization | P2 | v0.1 config overrides *(partial)*; full editor v2+ | — |

### §8 UI Framework & Window Management

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.14 | Key bar (F1..F12 hints at bottom, Ctrl/Alt/Shift aware) | P0 | v0.2 | [ ] |
| F0.15 | Modal dialog engine (Far look: double-frame, hotkeys) | P0 | v0.2 | [ ] |
| F1.24 | Menus (F9 menu bar, popup menus) | P1 | v1.8 | [ ] |
| F2.14 | Window stack: multiple editors/viewers open, F12 switcher | P2 | v2+ | — |
| F1.25 | Mouse support | P1 | v1.2 *(key-bar clicks from v0.2)* | [ ] |
| F2.15 | Built-in help system (F1, context help) | P2 | v1.8 keymap reference *(partial)*; full help v2+ | — |
| F2.16 | Localized UI (en + uk at minimum) | P2 | v2+ | — |
| — | Macros / automation (Far: Lua via LuaMacro) | P3 | v2+ / opportunistic | — |
| — | Screen grabber, screensaver, desktop background | ✖ | out of scope | — |

### §9 Plugins & Extensibility

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F2.19 | Plugin API (Python entry points: panel providers, commands, hooks) | P2 | v2+ | — |
| F1.28 | Archive browsing as a panel (zip/tar/7z read) | P1 | v1.7 | [ ] |
| F1.29 | Archive create/extract operations | P1 | v1.7 | [ ] |
| F2.20 | Temp panel (virtual panel of arbitrary files) | P2 | v2+ *(F1.21 keeps a list dialog in P1)* | — |
| F2.21 | Remote FS: SFTP/FTP as panel | P2 | v2+ | — |
| F2.22 | Compare folders / compare files | P2 | v2+ | — |
| — | Process list panel | P3 | v2+ / opportunistic | — |
| — | Editor helpers (case change, align, brackets, drawline…) | P3 | v2+ / opportunistic | — |

### §10 OS Integration

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F1.26 | System clipboard (copy names/paths/file contents) | P1 | v1.2 | [ ] |
| F2.23 | Privilege elevation for protected ops | P2 | v2+ *(owner change greyed in F1.9 with hint)* | — |
| — | Removable media / mount awareness | P3 | v2+ / opportunistic | — |
| — | Network browse (SMB neighborhood) | ✖ | out of scope | — |
| F1.27 | Logging framework (`far.log.*`-style env config) | P1 | v0.1 foundation *(pulled forward; full criteria — see Part 3)* | [ ] |

### §11 LLM Integration Module

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.17 | Provider config: API key mgmt (env/keychain), model choice, usage display | P0 | v0.7 *(usage display = F1.30 footer, v1.9 — see Part 3)* | [ ] |
| F0.18 | AI command palette: natural language → shell command, confirm-before-run | P0 | v0.7 | [ ] |
| F1.31 | Explain/summarize file or directory (from viewer or panel) | P1 | v1.9 | [ ] |
| F1.32 | Smart selection: "select all logs older than a week" → mask/selection | P1 | v1.9 | [ ] |
| F2.24 | AI rename / multi-rename suggestions | P2 | v2+ | — |
| F1.33 | Chat sidebar with context (current dir, selection, viewed file) | P1 | v1.9 | [ ] |
| F2.25 | AI actions in editor: explain / transform / fix selection | P2 | v2+ | — |
| F2.26 | Semantic search over directory contents | P2 | v2+ | — |
| F1.30 | Cost guardrails: token counting (`count_tokens`), per-session budget | P1 | v1.9 *(spec adds per-day budgets — see Part 3)* | [ ] |
| F0.17 | Offline degradation (all AI features optional, product fully usable without) | P0 | v0.7 (architectural rule, re-tested at the v1 exit gate) | [ ] |

### §12 Claude Code Integration Module

| F# | Feature | Priority | Phase | Tested |
|----|---------|----------|-------|--------|
| F0.19 | Launch Claude Code in current panel dir (embedded PTY pane or external terminal) | P0 | v0.8 | [ ] |
| F1.34 | Headless task runner: `claude -p "..."` on selection, output to viewer | P1 | v1.10 | [ ] |
| F1.35 | Agent SDK embedding: prompt box → agent works in cwd, streamed transcript pane | P1 | v1.10 | [ ] |
| F1.36 | Pass context: send selected files / panel state into the session | P1 | v1.10 | [ ] |
| F1.37 | Permission prompts surfaced as TUI dialogs (SDK permission callbacks) | P1 | v1.10 | [ ] |
| F2.27 | Live diff review pane for changes Claude makes | P2 | v2+ | — |
| F2.28 | Session manager panel: list / resume / fork past sessions | P2 | v2+ *(F1.35 persists transcripts as groundwork)* | — |
| F2.29 | Background tasks + notification when done | P2 | v2+ *(F1.34 is foreground-modal in P1)* | — |
| — | Git worktree helper for agent isolation | P3 | v2+ / opportunistic | — |
| — | MCP server exposing panel state to any agent | P3 | v2+ / opportunistic | — |

**Audit result:** all **14 P0** features are owned by v0 phases; all **31 P1** scope rows are
owned by v0/v1 phases and every one maps to a numbered spec feature (`F0.x` pulled forward or
`F1.1–F1.37`). All 37 features of the PHASE1 spec are covered: F1.1/F1.2/F1.5/F1.20 → v1.1 ·
F1.4/F1.6/F1.25/F1.26 → v1.2 · F1.7/F1.8/F1.9 → v1.3 · F1.10–F1.13, F1.22 → v1.4 ·
F1.3, F1.14–F1.19 → v1.5 · F1.21 → v1.6 · F1.28/F1.29 → v1.7 · F1.23/F1.24 → v1.8 ·
F1.30–F1.33 → v1.9 · F1.34–F1.37 → v1.10 · F1.27 → v0.1 (foundation). The former "Settings UI"
gap is resolved by the PHASE1 spec (see Part 3 #1), and the three unowned fragments — panel
resize, `Space`/select-all, viewer tab width — were resolved by decision on 2026-08-02 (Part 3
#2–#4). Every P2/P3 feature has a documented home; ✖ items are explicitly out. **No open
coverage gaps remain.**

---

## Part 2 — Per-phase test checklists

Open the shipped phase's list; tick a feature only after verifying it by hand against the
acceptance criteria of its `F0.x` / `F1.x` section in the far-spec files.

### v0.1 — Panel core retrofit (release 0.1.1)
- [ ] F0.1 — Two side-by-side panels, Tab switching, swap, resize
- [ ] F0.2 — File list with column views (brief / medium / full / wide)
- [ ] F0.3 — Sorting: name, ext, size, mtime; ascending/descending
- [ ] F1.27 — Logging framework — foundation part *(full criteria: v1 exit gate)*

### v0.2 — Dialog kit, Far theme, key bar (0.2.0)
- [ ] F0.14 — Key bar (F1..F12 hints at bottom, Ctrl/Alt/Shift aware)
- [ ] F0.15 — Modal dialog engine (Far look: double-frame, hotkeys)
- [ ] F0.15 — Color scheme / theming — Far-classic default only *(theme system: v1.8)*

### v0.3 — Selection, hidden files, persistence (0.3.0)
- [ ] F0.4 — Selection: Ins/Space, `+`/`-` by mask, invert, select-all
- [ ] F0.5 — Hidden/system files toggle
- [ ] F0.16 — Settings persistence (SQLite, like Far — stdlib `sqlite3`)

### v0.4 — File operations (0.4.0)
- [ ] F0.6 — Copy / Move (F5/F6) with progress, ETA, speed
- [ ] F0.6 — Preserve timestamps/owner on copy
- [ ] F0.7 — Mkdir (F7), including nested paths
- [ ] F0.8 — Delete (F8) with confirmation *(permanent; trash: v1.3)*
- [ ] F0.9 — Rename (Shift+F6, and F6 to same dir)
- [ ] F0.10 — Conflict resolution: overwrite / skip / rename / all

### v0.5 — Command line, execution, cd-sync (0.5.0)
- [ ] F0.11 — Embedded command line under panels
- [ ] F0.11 — Run command, panels hide, show output, return
- [ ] F0.11 — cd sync: panel follows shell cwd and vice versa

### v0.6 — Viewer and editor (0.6.0)
- [ ] F0.12 — Text view (F3), instant open of huge files
- [ ] F0.12 — Wrap / unwrap *(tab width: v1.5)*
- [ ] F0.13 — Edit (F4), save (F2), save-as (Shift+F2)
- [ ] F0.13 — Undo / redo
- [ ] F0.13 — Encodings + EOL (LF/CRLF) handling on open/save — EOL part *(encodings: v1.5)*
- [ ] F0.13 — Modified-file guard on close / external change detection
- [ ] F0.13 — Open in external editor ($EDITOR)

### v0.7 — AI foundation (0.7.0)
- [ ] F0.17 — Provider config: API key mgmt (env/keychain), model choice *(usage display: v1.9)*
- [ ] F0.17 — Offline degradation (all AI features optional, product fully usable without)
- [ ] F0.18 — AI command palette: natural language → shell command, confirm-before-run

### v0.8 — Open Claude Code here (0.8.0 = MVP)
- [ ] F0.19 — Launch Claude Code in current panel dir (embedded PTY pane or external terminal)

### v1.1 — Masks, quick search, highlighting (1.1.0)
- [ ] F1.20 — File masks language (`*.py,*.md|*test*`, exclude masks)
- [ ] F1.1 — Quick search (type-to-jump, Alt+letter)
- [ ] F1.2 — File highlighting by mask/attributes (color groups)
- [ ] F1.5 — Free space / totals in panel footer

### v1.2 — Drives, auto-refresh, clipboard, mouse (1.2.0)
- [ ] F1.4 — Drives / locations menu (Alt+F1/F2)
- [ ] F1.6 — Auto-refresh on FS change
- [ ] F1.26 — System clipboard (copy names/paths/file contents)
- [ ] F1.25 — Mouse support

### v1.3 — Resilient file operations (1.3.0)
- [ ] F1.7 — Delete to trash vs permanent
- [ ] F1.8 — Error recovery: retry / skip / skip all / cancel
- [ ] F1.9 — Attributes / permissions dialog (chmod/chown on POSIX)
- [ ] F0.6 — Preserve timestamps/owner on copy — re-verified with pinned tests

### v1.4 — Histories, completion, command-line niceties (1.4.0)
- [ ] F1.10 — Command history (persistent, Alt+F8)
- [ ] F1.22 — Histories: folders, viewed/edited files, dialog inputs (Alt+F12, Alt+F11, Ctrl+Down)
- [ ] F1.12 — Tab completion (files, commands)
- [ ] F1.11 — Ctrl+Enter — insert file name; Ctrl+F — full path; environment variable expansion
- [ ] F1.13 — Enter on file → open by association *(`.zip` → archive rule: re-check after v1.7)*

### v1.5 — Viewer and editor II (1.5.0)
- [ ] F1.14 — Hex / dump mode
- [ ] F1.15 — Encoding selection + auto-detect (viewer)
- [ ] F1.16 — Search: text / regex / hex, F7/Shift+F7 (viewer)
- [ ] F1.17 — Search / replace with regex (editor)
- [ ] F1.18 — Encodings & EOL controls (editor) — encodings part
- [ ] F1.19 — Syntax highlighting (editor)
- [ ] F2.17 — Syntax highlighting in viewer *(pulled forward)*
- [ ] F1.3 — Quick view panel (Ctrl+Q preview)
- [ ] F0.12 — Wrap / unwrap, tab width — tab width part

### v1.6 — Find file and content search (1.6.0)
- [ ] F1.21 — Find file (Alt+F7): masks, subdirs, content search (incl. encoding-aware / regex, `rg` delegation)

### v1.7 — Archives (1.7.0)
- [ ] F1.28 — Archive browsing as a panel (zip/tar/7z read)
- [ ] F1.29 — Archive create/extract operations
- [ ] F1.13 — Enter on `.zip` → archive panel association *(deferred criterion from v1.4)*

### v1.8 — Menus and theming (1.8.0)
- [ ] F1.24 — Menus (F9 menu bar, popup menus)
- [ ] F1.23 — Color scheme / theming (Far classic, Dark modern, Light; F9 → Options → Theme picker)
- [ ] F2.15 — Built-in help system (F1) — keymap reference *(partial; full help: v2+)*

### v1.9 — AI II (1.9.0)
- [ ] F1.33 — Chat sidebar with context (current dir, selection, viewed file)
- [ ] F1.31 — Explain/summarize file or directory (from viewer or panel)
- [ ] F1.32 — Smart selection: "select all logs older than a week" → mask/selection
- [ ] F1.30 — Cost guardrails: token counting (`count_tokens`), per-session + per-day budgets, usage footer
- [ ] F0.17 — Provider config — usage display part (the F1.30 footer)

### v1.10 — Claude Code II (1.10.0 = first public release)
- [ ] F1.34 — Headless task runner: `claude -p "..."` on selection, output to viewer
- [ ] F1.35 — Agent SDK embedding: prompt box → agent works in cwd, streamed transcript pane
- [ ] F1.36 — Pass context: send selected files / panel state into the session
- [ ] F1.37 — Permission prompts surfaced as TUI dialogs (SDK permission callbacks)
- [ ] F1.27 — Logging framework — full criteria (rotation, crash handler, AI/key redaction)
- [ ] Phase 1 exit checklist (PHASE1 spec): no P0 regressions · ≥ 3 external testers · clean run
      with no API key / no `claude` / no network · packaging (`pipx` + Homebrew formula) ·
      release notes state the F1.7 trash change and Windows limitations

---

## Part 3 — Gaps and deviations from the scope file

Honest deltas between the far-spec files and the current roadmap. Each needs either a roadmap
amendment or a conscious acceptance:

1. **Settings UI — RESOLVED by the PHASE1 spec.** The scope table marked "Settings UI" P1, but
   PYTHON_TUI_PHASE1_SPEC.md contains no settings-UI feature: P1 ships hand-edited TOML config
   plus the `F9 → Options → Theme` picker (F1.23); the full Settings UI is F2.10 (P2). The
   roadmap (config from v0.1, theme picker in v1.8, settings UI in v2+) matches the P1 spec —
   no change needed.
2. **Panel resize — RESOLVED (decision, 2026-08-02).** Not in F0.1's criteria or any F1.x;
   **added to v0.1** by decision: `Ctrl+Left`/`Ctrl+Right` shift the split (30/50/70), persisted
   with panel state. Roadmap v0.1 updated; carry into v0.1's issues.
3. **`Space` select and select-all — RESOLVED (decision, 2026-08-02).** `Space` **added to v0.3**
   as a second toggle key alongside `Ins`; a separate select-all key is **not** added — mask `*`
   is the accepted select-all path. Roadmap v0.3 updated; carry into v0.3's issues.
4. **Viewer tab width — RESOLVED (decision, 2026-08-02).** Absent from F0.12 and F1.14–F1.16;
   **kept in v1.5** as an explicit task (configurable, default 8). Roadmap v1.5 updated; carry
   into v1.5's issues.
5. **Usage display — confirmed as F1.30.** The F0.17 scope row's "usage display" is delivered by
   F1.30's usage footer (`session: 41k tok · ~$0.31`) in v1.9. Accepted split; v0.7 testing must
   not expect it.
6. **F1.27 exceeds the v0.1 logging foundation.** v0.1 ships structured env-configurable logging;
   F1.27 additionally requires rotation, subsystem loggers, a crash handler with report file, a
   `--log-level` flag, and AI prompt/key redaction. Owned here as: foundation v0.1, full F1.27
   criteria verified at the v1 exit gate (checklist under v1.10). The redaction criteria become
   testable from v0.7 (first AI phase) — carry them in v0.7's issues too.
7. **F1.30 extends the roadmap wording.** Roadmap v1.9 says "per-session token budget"; F1.30
   requires per-session **and per-day** budgets, persisted in the DB, plus the usage footer in
   every AI surface. The spec is authoritative — generate v1.9 issues from F1.30, not the
   roadmap sentence.
8. **F1.13 sequencing.** The association rule "`.zip` → archive panel" (an F1.13 acceptance
   criterion, v1.4) is only verifiable after F1.28 lands in v1.7 — the criterion appears in both
   phases' checklists; tick it in v1.7.
9. **Phase 1 exit gate additions.** The PHASE1 spec's release gate adds items beyond the roadmap's
   v1.10 tasks: ≥ 3 external testers on the daily-driver workflow, a **Homebrew formula**
   alongside `pipx`, and release notes calling out the F1.7 trash-default change. Reflected in
   the v1.10 checklist; add them to v1.10's issues when generated.
10. **Pulled forward (positive deviations):** logging foundation (F1.27 → v0.1), `$EDITOR` +
    editor guards (F0.13 → v0.6), EOL preservation (F0.13 → v0.6), preserve timestamps
    (F0.6 → v0.4), syntax highlighting in viewer (F2.17 part → v1.5), key-bar mouse clicks
    (F1.25 part → v0.2 via F0.14).
11. **Split deliveries:** *Encodings + EOL* (F0.13 EOL v0.6, F1.18 encodings v1.5); *theming*
    (F0.15 default v0.2, F1.23 system v1.8); *help* (keymap reference v1.8, full F2.15 v2+);
    *keybinding customization* (config overrides v0.1, full F2.11 editor v2+); *mouse* (key-bar
    clicks v0.2, full F1.25 v1.2); *histories* (F1.10 commands + F1.22 folders/files/inputs, both
    v1.4). Their checklist entries appear in the relevant phases with the part named.
