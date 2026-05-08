# Phase 1 — GitHub Issues

## Issues Summary Table

| # | ID | Title | Size | Stage | Dependencies |
|---|---|---|---|---|---|
| 1 | MC-001 | Project scaffold and package structure | S | 1 — Scaffold | -- |
| 2 | MC-002 | Configuration and key bindings | S | 1 — Scaffold | MC-001 |
| 3 | MC-003 | Core widgets | M | 2 — Widgets | MC-001 |
| 4 | MC-004 | Panel system and file browser panel | M | 3 — Panels | MC-003 |
| 5 | MC-005 | Application shell and dual-panel layout | M | 4 — App Shell | MC-004, MC-002 |
| 6 | MC-006 | File navigation, quick filter, and sorting | M | 5 — Navigation | MC-005 |
| 7 | MC-007 | Filesystem utilities | S | 6 — Utilities | MC-001 |
| 8 | MC-008 | Test suite and fixtures | M | 7 — Testing | MC-006, MC-007 |

**Size legend:** S = 1–2 days, M = 3–5 days

---

## Dependency Tree

```
            MC-001 (scaffold)
                |
        +-------+-------+
        v       v       v
    MC-002  MC-003  MC-007
    (config) (widgets) (fs utils)
        |       |       |
        |   MC-004      |
        |   (panels)    |
        |       |       |
        +---v---+       |
          MC-005        |
          (app shell)   |
              |         |
          MC-006        |
          (navigation)  |
              |         |
              +----+----+
                   |
               MC-008
               (tests)
```

**Parallelization hints:**

- MC-002, MC-003, and MC-007 can all run in parallel after MC-001
- MC-007 has no dependency on the widget/panel chain and can be built early
- MC-008 depends on both the navigation chain and filesystem utilities

---

## Stage 1 — Scaffold

### MC-001 — Project scaffold and package structure

**Description:**
Set up the `mycom` Python package with build configuration, directory structure, and entry point. This is the foundation that all other issues build on.

**What needs to be done:**
- Create `pyproject.toml` with:
  - Python 3.11+ requirement
  - Dependencies: `textual>=0.80`, `pyte`, `anthropic`, `tomli` (for Python <3.11 TOML support, or `tomllib` stdlib)
  - Dev dependencies via `[dev]` extra: `pytest`, `pytest-cov`, `pytest-asyncio`, `textual-dev`
  - Console script entry point: `mycom = "mycom.app:main"`
- Create `mycom/` source package with `__init__.py` containing `__version__`
- Create sub-packages with `__init__.py`: `panels/`, `operations/`, `plugins/`, `plugins/viewer/`, `plugins/editor/`, `widgets/`, `llm/`, `utils/`
- Create `tests/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- Create `README.md` and `.gitignore`

**Dependencies:** None

**Expected result:**
A clean Python package that installs via `pip install -e ".[dev]"` and runs `mycom` from the command line (even if it only shows a placeholder screen).

**Acceptance criteria:**
- [ ] `pip install -e ".[dev]"` exits 0
- [ ] `mycom` command launches (placeholder Textual app is fine)
- [ ] All sub-packages import without errors: `from mycom.panels import base`, `from mycom.widgets import file_list`, etc.
- [ ] `pytest` runs with 0 errors (even if 0 tests)
- [ ] `.gitignore` covers `__pycache__/`, `.venv/`, `*.egg-info/`, `.mypy_cache/`

---

### MC-002 — Configuration and key bindings

**Description:**
Implement TOML-based configuration loading and the key binding registry. All user-customizable settings flow through this module.

**What needs to be done:**
- Implement `mycom/config.py`:
  - Load config from `~/.config/mycom/config.toml` if it exists
  - Merge with built-in defaults for any missing keys
  - Config sections: `[general]`, `[keybindings]`, `[llm]`, `[plugins.viewers]`, `[plugins.editors]`
- Implement `mycom/utils/keys.py`:
  - `KeyBindings` class that maps action names to Textual key identifiers
  - Default bindings: F1=help, F3=view, F4=edit, F5=copy, F6=move, F7=mkdir, F8=delete, F10=quit, Tab=switch_panel, Enter=open, Backspace=go_up, Ctrl+T=terminal_toggle, Ctrl+L=llm_toggle
  - Load overrides from config `[keybindings]` section
- Create a sample `config.toml` in `tests/fixtures/` for testing

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

---

## Stage 2 — Widgets

### MC-003 — Core widgets

**Description:**
Build the reusable Textual widgets that compose the file manager UI: file list table, status bar, path bar, and modal dialogs.

**What needs to be done:**

**File list widget (`mycom/widgets/file_list.py`):**
- Textual `DataTable`-based widget displaying: type indicator, name, size, date, permissions
- `..` entry at top of every listing (except root `/`)
- Directories listed before files
- Current selection highlight with distinct active/inactive styling
- Handle empty directories

**Status bar (`mycom/widgets/status_bar.py`):**
- Bottom-of-screen widget showing F-key hints
- Hints reflect configured keybindings
- Clickable hints (mouse support)

**Path bar (`mycom/widgets/path_bar.py`):**
- Shows current directory path per panel
- Truncates long paths from the left
- Active/inactive visual distinction

**Dialogs (`mycom/widgets/dialog.py`):**
- `ConfirmDialog` — modal Yes/No for destructive operations
- `InputDialog` — modal text input for rename, mkdir, go-to-path
- `ProgressDialog` — modal progress indicator for file operations
- All keyboard navigable (Tab, Enter, Escape)

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

---

## Stage 3 — Panels

### MC-004 — Panel system and file browser panel

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

**Dependencies:** MC-003

**Expected result:**
A self-contained file browser panel widget that can be placed anywhere in the Textual layout and independently navigated.

**Acceptance criteria:**
- [ ] `FileBrowserPanel` renders directory listing with path bar
- [ ] `activate()` / `deactivate()` toggle visual state (border, focus)
- [ ] `get_current_path()` returns the panel's working directory
- [ ] `get_selected_files()` returns highlighted file paths
- [ ] `BasePanel` interface is implementable by future terminal and LLM panels
- [ ] Panel works standalone in a Textual test app

---

## Stage 4 — App Shell

### MC-005 — Application shell and dual-panel layout

**Description:**
Wire together two file browser panels, the status bar, and an app header into the main MyCom application with working panel switching.

**What needs to be done:**

**Main application (`mycom/app.py`):**
- `MyComApp` extending `textual.App`
- Layout: header → two `FileBrowserPanel` side-by-side (50/50 horizontal split) → `StatusBar`
- Track active panel (left or right), default left on startup
- Tab key switches active panel, updating visual state on both panels
- Load config on startup
- `main()` function as the entry point
- Textual CSS file (`mycom/app.tcss`) for layout and theming

**App header (`mycom/widgets/header.py`):**
- "MyCom" title
- Current time display (optional, auto-updating)

**Dependencies:** MC-004, MC-002

**Expected result:**
Running `mycom` launches a dual-panel file manager that displays the current directory in both panels and allows switching between them with Tab.

**Acceptance criteria:**
- [ ] `mycom` launches and renders two side-by-side panels
- [ ] Both panels show the current directory listing on startup
- [ ] Tab key switches the active panel — visual indicator updates
- [ ] Status bar displays F-key hints at the bottom
- [ ] App header shows "MyCom" title
- [ ] Terminal resize reflows panels correctly
- [ ] F10 or Ctrl+Q exits the application
- [ ] Config is loaded from TOML on startup

---

## Stage 5 — Navigation

### MC-006 — File navigation, quick filter, and sorting

**Description:**
Implement all navigation interactions: entering directories, going up, keyboard movement, quick filtering, and column sorting.

**What needs to be done:**

**Directory navigation:**
- Enter key on directory → navigate into it, update `FileList` and `PathBar`
- Enter on `..` or Backspace → navigate to parent directory
- Arrow keys (Up/Down) → move cursor in `FileList`
- Home → first entry, End → last entry
- Page Up / Page Down → scroll by visible page height
- Handle permission denied → show message, stay in current dir
- Follow symlinks for navigation, display symlink indicator

**Quick filter:**
- Typing alphanumeric characters activates inline filter
- File list filters in real-time (case-insensitive substring match)
- Escape clears filter, Enter navigates to selection and clears filter
- Filter bar appears above status bar when active

**Sorting (`mycom/operations/sort.py`):**
- Sort by name, size, date, extension
- Toggle sort direction on repeated activation
- Sort indicator (▲/▼) in column header
- Directories always before files regardless of sort field

**Dependencies:** MC-005

**Expected result:**
Full keyboard-driven file navigation with filtering and sorting — the core interaction loop of the file manager.

**Acceptance criteria:**
- [ ] Enter navigates into directories and Backspace goes up
- [ ] Arrow keys, Home, End, Page Up, Page Down all work correctly
- [ ] Permission denied shows an error message, does not crash
- [ ] Quick filter narrows file list in real-time as user types
- [ ] Escape clears filter and restores full listing
- [ ] Sorting works for all 4 fields with direction toggle
- [ ] Directories remain above files in every sort mode
- [ ] Sort indicator visible in active column header

---

## Stage 6 — Utilities

### MC-007 — Filesystem utilities

**Description:**
Implement the low-level filesystem helper functions used by the file list widget and file browser panel. These are pure functions with no Textual dependency.

**What needs to be done:**

**`mycom/utils/fs.py`:**
- `FileEntry` dataclass: `name`, `path`, `is_dir`, `is_symlink`, `size`, `modified`, `permissions`
- `list_directory(path, show_hidden) → list[FileEntry]` — stat each entry, return structured list
- `format_size(bytes) → str` — human-readable sizes: B, KB, MB, GB, TB
- `format_date(timestamp) → str` — formatted modification date
- `format_permissions(mode) → str` — rwx permission string
- Graceful handling of `PermissionError` and `OSError` in all functions

**Dependencies:** MC-001

**Expected result:**
A set of battle-tested filesystem helpers that handle edge cases (broken symlinks, permission errors, special files) without crashing.

**Acceptance criteria:**
- [ ] `list_directory` returns correct entries for a known test directory
- [ ] Hidden files included when `show_hidden=True`, excluded otherwise
- [ ] `format_size` produces correct output: 0 B, 1023 B, 1.0 KB, 1.5 MB, 2.3 GB
- [ ] `format_date` produces a readable date string
- [ ] `format_permissions` matches `ls -l` output format (e.g., `rwxr-xr-x`)
- [ ] Broken symlinks don't crash `list_directory` — they appear with an error indicator
- [ ] `PermissionError` on a directory returns an empty list, not an exception

---

## Stage 7 — Testing

### MC-008 — Test suite and fixtures

**Description:**
Create test fixtures and write unit + integration tests covering the full Phase 1 scope. Validate that the foundation is solid before building file operations and advanced features on top.

**What needs to be done:**

**Fixtures:**
- `tests/fixtures/sample_tree/` — directory structure with files, subdirectories, symlinks, hidden files for navigation testing
- `tests/fixtures/config.toml` — sample configuration for config loading tests

**Unit tests:**
- `test_config.py` — config loading, defaults, custom values, missing file, unknown keys ignored
- `test_keys.py` — key binding registry, default bindings, custom overrides from config
- `test_fs.py` — `list_directory`, `format_size`, `format_date`, `format_permissions`, error handling
- `test_sort.py` — sort by name/size/date/extension, ascending/descending, directories-first invariant

**Integration tests (Textual pilot):**
- `test_app.py` — app starts, renders dual panels, Tab switches active panel, F10 quits
- `test_navigation.py` — enter directory, go up, quick filter, sort toggle
- `test_widgets.py` — file list rendering, status bar display, dialog keyboard navigation

**Dependencies:** MC-006, MC-007

**Expected result:**
A comprehensive test suite that validates the Phase 1 foundation — config, filesystem helpers, widgets, navigation, and the overall app shell.

**Acceptance criteria:**
- [ ] All unit tests pass
- [ ] Integration tests verify app startup and dual-panel rendering
- [ ] Navigation tests confirm enter, go-up, filter, and sort behaviors
- [ ] Dialog tests confirm keyboard interaction (Tab, Enter, Escape)
- [ ] `pytest` runs clean with no warnings
- [ ] `pytest --cov` shows coverage for all `mycom/` modules

---

## Phase 1 scope notes

**Total effort:** ~3–4 weeks for a single developer, ~2 weeks with parallel tracks.

**Critical path:** MC-001 → MC-003 → MC-004 → MC-005 → MC-006 → MC-008

**Parallel tracks:**
- Track A (widgets + panels): MC-003 → MC-004 → MC-005 → MC-006
- Track B (config): MC-002 — can proceed independently after MC-001, merges at MC-005
- Track C (utilities): MC-007 — can proceed independently after MC-001, merges at MC-008

**Companion documents:**
- `phase-1-tasks.md` — detailed task tables per substage
- `architecture.md` — system architecture and project structure
- `mission.md` — project goals and principles
- `roadmap.md` — full 8-phase roadmap
