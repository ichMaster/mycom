# Phase 1 — GitHub Issues

## Issues Summary Table

| # | ID | Title | Size | Stage | Dependencies |
|---|---|---|---|---|---|
| 1 | MC-001 | Project scaffold and package structure | S | 1 — Scaffold | -- |
| 2 | MC-002 | Configuration and key bindings | S | 2 — Config | MC-001 |
| 3 | MC-003 | Core widgets | M | 3 — Widgets | MC-001 |
| 4 | MC-004 | Filesystem utilities | S | 4 — Utilities | MC-001 |
| 5 | MC-005 | Panel system and file browser panel | M | 5 — Panels | MC-003, MC-004 |
| 6 | MC-006 | Application shell and dual-panel layout | M | 6 — App Shell | MC-005, MC-002 |
| 7 | MC-007 | File navigation, quick filter, and sorting | M | 7 — Navigation | MC-006 |
| 8 | MC-008 | Documentation site and API reference | S | 8 — Docs | MC-007 |

**Size legend:** S = 1–2 days, M = 3–5 days

**Tooling:** All commands use `uv run` (e.g., `uv run pytest`, `uv run mycom`, `uv run mkdocs build`).

---

## Dependency Tree

```
            MC-001 (scaffold)
                |
        +-------+-------+
        v       v       v
    MC-002  MC-003  MC-004
    (config) (widgets) (fs utils)
        |       |       |
        |       +---+---+
        |           v
        |       MC-005
        |       (panels)
        |           |
        +-----+-----+
              v
          MC-006
          (app shell)
              |
          MC-007
          (navigation)
              |
          MC-008
          (docs)
```

**Parallelization hints:**

- MC-002, MC-003, and MC-004 can all run in parallel after MC-001
- MC-005 merges the widget and fs utility tracks
- MC-008 (docs) comes last since it documents all other modules

---

## Stage 1 — Scaffold

### MC-001 — Project scaffold and package structure

**Description:**
Set up the `mycom` Python package with `uv`, build configuration, directory structure, entry point, and documentation scaffold. This is the foundation that all other issues build on.

**What needs to be done:**
- `pyproject.toml` with:
  - Python 3.11+ requirement
  - Dependencies: `textual>=0.80`, `pyte>=0.8`, `anthropic>=0.40`
  - Dev dependency group: `pytest`, `pytest-cov`, `pytest-asyncio`, `textual-dev`, `ruff`
  - Docs dependency group: `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`, `mkdocs-gen-files`, `mkdocs-literate-nav`
  - Console script entry point: `mycom = "mycom.app:main"`
- `mycom/` source package with `__init__.py` containing `__version__ = "0.1.0"`
- Sub-packages with `__init__.py`: `panels/`, `operations/`, `plugins/`, `plugins/viewer/`, `plugins/editor/`, `widgets/`, `llm/`, `utils/`
- `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- `VERSION` file, `RELEASE.txt`
- `uv lock` to generate lockfile
- `mkdocs.yml` with material theme and basic nav
- `docs/index.md` and `docs/getting-started.md` stubs

**Unit tests:**
- `tests/unit/test_scaffold.py` — all sub-packages import, `__version__` is set

**Dependencies:** None

**Expected result:**
A clean Python package managed by `uv` that installs and runs from the command line, with a documentation site that builds.

**Acceptance criteria:**
- [ ] `uv sync --all-groups` exits 0
- [ ] `uv run mycom` launches (placeholder Textual app is fine)
- [ ] All sub-packages import without errors
- [ ] `uv run pytest` exits 0 with at least 1 passing test
- [ ] `uv run mkdocs build` exits 0
- [ ] `uv.lock` is committed and reproducible

---

## Stage 2 — Config

### MC-002 — Configuration and key bindings

**Description:**
Implement TOML-based configuration loading and the key binding registry. All user-customizable settings flow through this module.

**What needs to be done:**
- `mycom/config.py`:
  - Load config from `~/.config/mycom/config.toml` if it exists
  - Merge with built-in defaults for any missing keys
  - Config sections: `[general]`, `[keybindings]`, `[llm]`, `[plugins.viewers]`, `[plugins.editors]`
- `mycom/utils/keys.py`:
  - `KeyBindings` class mapping action names to Textual key identifiers
  - Default bindings: F1=help, F3=view, F4=edit, F5=copy, F6=move, F7=mkdir, F8=delete, F10=quit, Tab=switch_panel, Enter=open, Backspace=go_up, Ctrl+T=terminal_toggle, Ctrl+L=llm_toggle
  - Load overrides from config `[keybindings]` section

**Unit tests:**
- `tests/unit/test_config.py` — config loading, defaults, custom values, missing file, unknown keys ignored
- `tests/unit/test_keys.py` — key binding registry, default bindings, custom overrides
- `tests/fixtures/config.toml` — sample config for testing

**Documentation:**
- `docs/configuration.md` — config file format, all sections, example
- `docs/keybindings.md` — default bindings table, how to customize

**Dependencies:** MC-001

**Expected result:**
Configuration is loaded once at startup and accessible throughout the app. Key bindings are configurable without code changes.

**Acceptance criteria:**
- [ ] App starts with no config file (defaults used)
- [ ] App reads `~/.config/mycom/config.toml` when present
- [ ] Unknown config keys are ignored (forward compatibility)
- [ ] `KeyBindings` resolves action names to key sequences
- [ ] Custom keybinding in config overrides the default
- [ ] Config is immutable after loading (no mutation at runtime)
- [ ] `uv run pytest tests/unit/test_config.py tests/unit/test_keys.py` — all pass
- [ ] `docs/configuration.md` and `docs/keybindings.md` render in mkdocs

---

## Stage 3 — Widgets

### MC-003 — Core widgets

**Description:**
Build the reusable Textual widgets that compose the file manager UI: file list table, status bar, path bar, and modal dialogs.

**What needs to be done:**

**File list widget (`mycom/widgets/file_list.py`):**
- Textual `DataTable`-based widget displaying: type indicator, name, size, date, permissions
- `..` entry at top (except root `/`)
- Directories before files
- Active/inactive styling
- Handle empty directories

**Status bar (`mycom/widgets/status_bar.py`):**
- F-key hints, clickable, reflect keybinding config

**Path bar (`mycom/widgets/path_bar.py`):**
- Current directory path, long path truncation, active/inactive state

**Dialogs (`mycom/widgets/dialog.py`):**
- `ConfirmDialog` — modal Yes/No
- `InputDialog` — modal text input
- `ProgressDialog` — modal progress indicator
- All keyboard navigable

**Unit tests:**
- `tests/unit/test_widgets.py` — FileList rendering, dirs-before-files, empty dir, `..` entry
- `tests/unit/test_status_bar.py` — StatusBar F-key hints
- `tests/unit/test_path_bar.py` — truncation, active/inactive
- `tests/unit/test_dialogs.py` — ConfirmDialog True/False, InputDialog text/None, Escape cancel

**Documentation:**
- `docs/widgets.md` — widget catalog with descriptions

**Dependencies:** MC-001

**Expected result:**
A set of composable, styled widgets ready to be assembled into panels and the main app layout.

**Acceptance criteria:**
- [ ] `FileList` renders a directory listing with all 5 columns
- [ ] `FileList` sorts directories before files
- [ ] `StatusBar` displays correct F-key hints from keybinding config
- [ ] `PathBar` truncates paths longer than available width
- [ ] `ConfirmDialog` returns True/False based on user choice
- [ ] `InputDialog` returns entered text or None on cancel
- [ ] All widgets render without errors in a Textual test harness
- [ ] `uv run pytest tests/unit/test_widgets.py tests/unit/test_status_bar.py tests/unit/test_path_bar.py tests/unit/test_dialogs.py` — all pass

---

## Stage 4 — Utilities

### MC-004 — Filesystem utilities

**Description:**
Implement the low-level filesystem helper functions used by the file list widget and file browser panel. These are pure functions with no Textual dependency.

**What needs to be done:**

**`mycom/utils/fs.py`:**
- `FileEntry` dataclass: `name`, `path`, `is_dir`, `is_symlink`, `size`, `modified`, `permissions`
- `list_directory(path, show_hidden) → list[FileEntry]` — stat each entry, return structured list
- `format_size(bytes) → str` — human-readable sizes: B, KB, MB, GB, TB
- `format_date(timestamp) → str` — formatted modification date
- `format_permissions(mode) → str` — rwx permission string
- Graceful handling of `PermissionError` and `OSError`

**Unit tests:**
- `tests/unit/test_fs.py` — list_directory with known fixture tree, hidden files toggle, format_size boundary values, format_date, format_permissions, broken symlinks, PermissionError
- `tests/fixtures/sample_tree/` — directory tree with files, subdirs, symlinks, hidden files

**Documentation:**
- Add docstrings to all public functions for mkdocstrings API reference

**Dependencies:** MC-001

**Expected result:**
A set of battle-tested filesystem helpers that handle edge cases (broken symlinks, permission errors, special files) without crashing.

**Acceptance criteria:**
- [ ] `list_directory` returns correct entries for a known test directory
- [ ] Hidden files included when `show_hidden=True`, excluded otherwise
- [ ] `format_size` correct: 0 B, 1023 B, 1.0 KB, 1.5 MB, 2.3 GB
- [ ] `format_permissions` matches `ls -l` format (e.g., `rwxr-xr-x`)
- [ ] Broken symlinks don't crash — appear with error indicator
- [ ] `PermissionError` returns empty list, not exception
- [ ] `uv run pytest tests/unit/test_fs.py` — all pass

---

## Stage 5 — Panels

### MC-005 — Panel system and file browser panel

**Description:**
Define the base panel interface that all panel modes (file browser, terminal, LLM chat) will implement, and build the file browser panel as the first concrete implementation.

**What needs to be done:**

**Base panel (`mycom/panels/base.py`):**
- `PanelMode` enum: `FILE_BROWSER`, `TERMINAL`, `LLM_CHAT`
- `BasePanel` abstract class extending Textual `Widget`
- Abstract methods: `activate()`, `deactivate()`, `get_current_path()`, `get_selected_files()`
- Panel border/header showing mode and title

**File browser panel (`mycom/panels/file_browser.py`):**
- Composes `PathBar` + `FileList` vertically
- Initializes with starting directory (CWD or home)
- `current_path` property synced with `PathBar`
- `selected_files` property returning list of selected `Path` objects
- Active/inactive visual state via border color

**Unit tests:**
- `tests/unit/test_panels.py` — renders with PathBar + FileList, activate/deactivate toggle, get_current_path, get_selected_files

**Documentation:**
- `docs/panels.md` — panel system overview, modes, switching behavior

**Dependencies:** MC-003, MC-004

**Expected result:**
A self-contained file browser panel widget that can be placed anywhere in the Textual layout and independently navigated.

**Acceptance criteria:**
- [ ] `FileBrowserPanel` renders directory listing with path bar
- [ ] `activate()` / `deactivate()` toggle visual state
- [ ] `get_current_path()` returns the panel's working directory
- [ ] `get_selected_files()` returns highlighted file paths
- [ ] `BasePanel` interface is implementable by future terminal and LLM panels
- [ ] `uv run pytest tests/unit/test_panels.py` — all pass

---

## Stage 6 — App Shell

### MC-006 — Application shell and dual-panel layout

**Description:**
Wire together two file browser panels, the status bar, and an app header into the main MyCom application with working panel switching.

**What needs to be done:**

**Main application (`mycom/app.py`):**
- `MyComApp` extending `textual.App`
- Layout: header → two `FileBrowserPanel` side-by-side (50/50 horizontal split) → `StatusBar`
- Track active panel (left or right), default left on startup
- Tab key switches active panel, updating visual state
- Load config on startup
- `main()` entry point function
- Textual CSS file (`mycom/app.tcss`)

**App header (`mycom/widgets/header.py`):**
- "MyCom" title, current time display

**Integration tests:**
- `tests/integration/test_app.py` — app starts, dual panels render, Tab switches, F10 quits, resize reflows

**Documentation:**
- `docs/architecture.md` — app shell layout diagram, component relationships
- Update `docs/getting-started.md` — add usage instructions

**Dependencies:** MC-005, MC-002

**Expected result:**
Running `uv run mycom` launches a dual-panel file manager that displays the current directory in both panels and allows switching between them with Tab.

**Acceptance criteria:**
- [ ] `uv run mycom` launches and renders two side-by-side panels
- [ ] Both panels show the current directory listing on startup
- [ ] Tab key switches the active panel — visual indicator updates
- [ ] Status bar displays F-key hints at the bottom
- [ ] App header shows "MyCom" title
- [ ] Terminal resize reflows panels correctly
- [ ] F10 or Ctrl+Q exits the application
- [ ] Config is loaded from TOML on startup
- [ ] `uv run pytest tests/integration/test_app.py` — all pass

---

## Stage 7 — Navigation

### MC-007 — File navigation, quick filter, and sorting

**Description:**
Implement all navigation interactions: entering directories, going up, keyboard movement, quick filtering, and column sorting.

**What needs to be done:**

**Directory navigation:**
- Enter on directory → navigate in, update FileList and PathBar
- Enter on `..` or Backspace → parent directory
- Arrow keys, Home, End, Page Up, Page Down
- Permission denied → error message, stay in current dir
- Symlinks → follow, display indicator

**Quick filter:**
- Typing activates inline filter, real-time case-insensitive substring
- Escape clears, Enter navigates and clears

**Sorting (`mycom/operations/sort.py`):**
- Sort by name, size, date, extension
- Direction toggle, sort indicator (▲/▼)
- Directories always first

**Unit tests:**
- `tests/unit/test_sort.py` — sort by all fields, ascending/descending, dirs-first invariant

**Integration tests:**
- `tests/integration/test_navigation.py` — enter dir, go up, Home/End, quick filter, sort toggle, permission denied

**Documentation:**
- `docs/navigation.md` — navigation keys, quick filter, sorting

**Dependencies:** MC-006

**Expected result:**
Full keyboard-driven file navigation with filtering and sorting — the core interaction loop of the file manager.

**Acceptance criteria:**
- [ ] Enter navigates into directories and Backspace goes up
- [ ] Arrow keys, Home, End, Page Up, Page Down all work
- [ ] Permission denied shows error, does not crash
- [ ] Quick filter narrows file list in real-time
- [ ] Escape clears filter and restores full listing
- [ ] Sorting works for all 4 fields with direction toggle
- [ ] Directories remain above files in every sort mode
- [ ] Sort indicator visible in active column header
- [ ] `uv run pytest tests/unit/test_sort.py tests/integration/test_navigation.py` — all pass

---

## Stage 8 — Docs

### MC-008 — Documentation site and API reference

**Description:**
Finalize the MkDocs documentation site with auto-generated API reference from source docstrings and polished user guide pages.

**What needs to be done:**

**API reference generation:**
- Configure `mkdocs-gen-files` to auto-generate API reference pages from `mycom/` source
- Configure `mkdocs-literate-nav` for automatic navigation
- Ensure all public classes and functions have docstrings

**User guide pages:**
- Finalize `docs/index.md` — project overview, features, installation
- Finalize `docs/getting-started.md` — install via `uv`, first run, basic usage
- Create `docs/development.md` — dev setup with `uv`, running tests, linting, building docs
- Review and finalize all docs pages from previous issues

**Dependencies:** MC-007

**Expected result:**
A complete, buildable documentation site covering installation, usage, configuration, navigation, and API reference.

**Acceptance criteria:**
- [ ] `uv run mkdocs build --strict` exits 0 with no warnings
- [ ] API reference pages generated for all `mycom/` modules
- [ ] Navigation structure is complete: index, getting started, configuration, keybindings, navigation, panels, widgets, architecture, development, API reference
- [ ] `uv run mkdocs serve` renders correctly in browser
- [ ] All code examples in docs use `uv run` commands

---

## Phase 1 scope notes

**Total effort:** ~3–4 weeks for a single developer, ~2 weeks with parallel tracks.

**Critical path:** MC-001 → MC-003 → MC-005 → MC-006 → MC-007 → MC-008

**Parallel tracks:**
- Track A (widgets): MC-003 → MC-005 → MC-006 → MC-007
- Track B (config): MC-002 — can proceed independently after MC-001, merges at MC-006
- Track C (utilities): MC-004 — can proceed independently after MC-001, merges at MC-005

**Each issue includes:**
- Implementation
- Unit tests (validated with `uv run pytest`)
- Documentation page (validated with `uv run mkdocs build`)

**Companion documents:**
- `phase-1-tasks.md` — detailed task tables per substage
- `architecture.md` — system architecture and project structure
- `mission.md` — project goals and principles
- `roadmap.md` — full 8-phase roadmap
