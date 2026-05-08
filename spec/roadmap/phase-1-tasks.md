# Phase 1 — Foundation Tasks

## 1. Project Scaffold

### 1.1 Package structure

| # | Task | Issue |
|---|------|-------|
| 1 | Initialize project with `uv init`, configure `pyproject.toml` (Python 3.11+; dependencies: `textual>=0.80`, `pyte>=0.8`, `anthropic>=0.40`; dev group: `pytest`, `pytest-cov`, `pytest-asyncio`, `textual-dev`, `ruff`; docs group: `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`, `mkdocs-gen-files`, `mkdocs-literate-nav`; entry point: `mycom = "mycom.app:main"`) | MC-001 |
| 2 | Create `mycom/` source package with `__init__.py` containing `__version__ = "0.1.0"` | MC-001 |
| 3 | Create sub-packages with `__init__.py`: `panels/`, `operations/`, `plugins/`, `plugins/viewer/`, `plugins/editor/`, `widgets/`, `llm/`, `utils/` | MC-001 |
| 4 | Create `tests/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/` | MC-001 |
| 5 | Run `uv lock` to generate lockfile | MC-001 |
| 6 | Create `VERSION` file with `0.1.0` | MC-001 |
| 7 | Create `RELEASE.txt` with initial entry | MC-001 |

### 1.2 Documentation scaffold

| # | Task | Issue |
|---|------|-------|
| 1 | Create `mkdocs.yml` with material theme, mkdocstrings plugin, and nav structure | MC-001 |
| 2 | Create `docs/index.md` — project overview and quick start | MC-001 |
| 3 | Create `docs/getting-started.md` — installation with `uv`, first run | MC-001 |
| 4 | Verify `uv run mkdocs build` succeeds | MC-001 |

### 1.3 Unit tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/unit/test_scaffold.py` — verify all sub-packages import, `__version__` is set | MC-001 |
| 2 | Verify `uv run pytest` exits 0 | MC-001 |

---

## 2. Configuration

### 2.1 Configuration loader (`mycom/config.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Create default config file `~/.config/mycom/config.toml` schema definition | MC-002 |
| 2 | Implement `mycom/config.py` — TOML config loader with defaults, supporting: config file > defaults | MC-002 |
| 3 | Define config schema: `show_hidden`, `confirm_delete`, `default_sort`, `default_sort_direction` | MC-002 |
| 4 | Define keybinding config section: `copy`, `move`, `delete`, `rename`, `view`, `edit`, `mkdir`, `terminal_toggle`, `llm_toggle`, `quit` | MC-002 |
| 5 | Define LLM config section: `api_key_env`, `model`, `max_context_files` | MC-002 |
| 6 | Define plugin config section: `viewers` (extension → plugin name map), `editors` (extension → plugin name map) | MC-002 |

### 2.2 Key binding definitions (`mycom/utils/keys.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement key binding registry that maps action names to key sequences | MC-002 |
| 2 | Define default F-key bindings: F1=help, F3=view, F4=edit, F5=copy, F6=move, F7=mkdir, F8=delete, F10=quit | MC-002 |
| 3 | Define navigation keys: Tab=switch panel, Enter=open, Backspace=go up, Home/End=first/last file | MC-002 |
| 4 | Define mode switching keys: Ctrl+T=terminal toggle, Ctrl+L=LLM chat toggle | MC-002 |
| 5 | Support loading custom bindings from config file and merging with defaults | MC-002 |

### 2.3 Unit tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/unit/test_config.py` — config loading, defaults, custom values, missing file handling, unknown keys ignored | MC-002 |
| 2 | `tests/unit/test_keys.py` — key binding registry, default bindings, custom overrides from config | MC-002 |
| 3 | Create `tests/fixtures/config.toml` — sample configuration for testing | MC-002 |

### 2.4 Documentation

| # | Task | Issue |
|---|------|-------|
| 1 | Create `docs/configuration.md` — config file format, all sections, example config | MC-002 |
| 2 | Create `docs/keybindings.md` — default key bindings table, how to customize | MC-002 |

---

## 3. Core Widgets

### 3.1 File list widget (`mycom/widgets/file_list.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `FileList` Textual widget based on `DataTable` | MC-003 |
| 2 | Display columns: icon/type indicator, name, size (human-readable), date modified, permissions | MC-003 |
| 3 | `..` entry at top of every listing (except root `/`) | MC-003 |
| 4 | Directories listed before files | MC-003 |
| 5 | Current selection highlight with distinct active/inactive panel styling | MC-003 |
| 6 | Handle empty directories gracefully | MC-003 |
| 7 | Lazy loading — only stat files visible in viewport for large directories | MC-003 |

### 3.2 Status bar (`mycom/widgets/status_bar.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `StatusBar` Textual widget displayed at the bottom of the screen | MC-003 |
| 2 | Display F-key hints: F1 Help, F3 View, F4 Edit, F5 Copy, F6 Move, F7 MkDir, F8 Delete, F10 Quit | MC-003 |
| 3 | Hints are clickable (mouse support) and reflect current keybinding config | MC-003 |
| 4 | Highlight active function key on press | MC-003 |

### 3.3 Path bar (`mycom/widgets/path_bar.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `PathBar` widget showing the current directory path for each panel | MC-003 |
| 2 | Truncate long paths from the left, preserving the trailing directory components | MC-003 |
| 3 | Visual indicator for active vs inactive panel (bold/dim or color) | MC-003 |

### 3.4 Dialog widgets (`mycom/widgets/dialog.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `ConfirmDialog` — modal Yes/No dialog for destructive operations | MC-003 |
| 2 | Implement `InputDialog` — modal text input for rename, mkdir, go-to-path | MC-003 |
| 3 | Implement `ProgressDialog` — modal progress bar for file operations | MC-003 |
| 4 | All dialogs are keyboard navigable (Tab between buttons, Enter to confirm, Escape to cancel) | MC-003 |

### 3.5 Unit tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/unit/test_widgets.py` — FileList rendering with columns, dirs-before-files, empty dir, `..` entry | MC-003 |
| 2 | `tests/unit/test_status_bar.py` — StatusBar displays correct F-key hints | MC-003 |
| 3 | `tests/unit/test_path_bar.py` — PathBar truncation, active/inactive state | MC-003 |
| 4 | `tests/unit/test_dialogs.py` — ConfirmDialog returns True/False, InputDialog returns text/None, Escape cancels | MC-003 |

### 3.6 Documentation

| # | Task | Issue |
|---|------|-------|
| 1 | Create `docs/widgets.md` — widget catalog with descriptions and screenshots | MC-003 |

---

## 4. Filesystem Helpers

### 4.1 Filesystem utilities (`mycom/utils/fs.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | `FileEntry` dataclass: name, path, is_dir, is_symlink, size, modified, permissions | MC-004 |
| 2 | `list_directory(path, show_hidden) → list[FileEntry]` — stat each entry, return structured list | MC-004 |
| 3 | `format_size(bytes) → str` — human-readable file sizes (B, KB, MB, GB) | MC-004 |
| 4 | `format_date(timestamp) → str` — formatted date for display | MC-004 |
| 5 | `format_permissions(mode) → str` — rwx permission string | MC-004 |
| 6 | Handle `PermissionError` and `OSError` gracefully in all functions | MC-004 |

### 4.2 Unit tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/unit/test_fs.py` — list_directory with known fixture tree, hidden files toggle | MC-004 |
| 2 | `tests/unit/test_fs.py` — format_size boundary values (0 B, 1023 B, 1.0 KB, 1.5 MB, 2.3 GB) | MC-004 |
| 3 | `tests/unit/test_fs.py` — format_date, format_permissions output | MC-004 |
| 4 | `tests/unit/test_fs.py` — broken symlinks, PermissionError handling | MC-004 |
| 5 | Create `tests/fixtures/sample_tree/` — directory tree with files, subdirs, symlinks, hidden files | MC-004 |

### 4.3 Documentation

| # | Task | Issue |
|---|------|-------|
| 1 | Add API reference for `mycom.utils.fs` via mkdocstrings (docstrings in source) | MC-004 |

---

## 5. Panel System

### 5.1 Base panel interface (`mycom/panels/base.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Define `BasePanel` abstract class extending Textual `Widget` | MC-005 |
| 2 | Define panel mode enum: `FILE_BROWSER`, `TERMINAL`, `LLM_CHAT` | MC-005 |
| 3 | Abstract methods: `activate()`, `deactivate()`, `get_current_path()`, `get_selected_files()` | MC-005 |
| 4 | Panel header with mode indicator and title | MC-005 |

### 5.2 File browser panel (`mycom/panels/file_browser.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `FileBrowserPanel` extending `BasePanel` | MC-005 |
| 2 | Compose `PathBar` + `FileList` widgets vertically | MC-005 |
| 3 | Initialize with a starting directory (default: home directory or CWD) | MC-005 |
| 4 | Expose `current_path` property synced with `PathBar` | MC-005 |
| 5 | Expose `selected_files` property returning list of selected file paths | MC-005 |
| 6 | Active/inactive visual state (border color or header highlight) | MC-005 |

### 5.3 Unit tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/unit/test_panels.py` — FileBrowserPanel renders with PathBar + FileList | MC-005 |
| 2 | `tests/unit/test_panels.py` — activate/deactivate toggle visual state | MC-005 |
| 3 | `tests/unit/test_panels.py` — get_current_path, get_selected_files return correct values | MC-005 |

### 5.4 Documentation

| # | Task | Issue |
|---|------|-------|
| 1 | Create `docs/panels.md` — panel system overview, panel modes, switching behavior | MC-005 |

---

## 6. Application Shell

### 6.1 Main application (`mycom/app.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `MyComApp` extending `textual.App` | MC-006 |
| 2 | Layout: two `FileBrowserPanel` side-by-side (horizontal split, equal width) | MC-006 |
| 3 | Bottom area: `StatusBar` widget | MC-006 |
| 4 | Track active panel (left or right), default to left on startup | MC-006 |
| 5 | Tab key switches active panel — update visual state of both panels | MC-006 |
| 6 | Load configuration on startup from `config.py` | MC-006 |
| 7 | `main()` entry point function that creates and runs the app | MC-006 |
| 8 | CSS styling for the dual-panel layout (Textual CSS file `mycom/app.tcss`) | MC-006 |
| 9 | Handle terminal resize gracefully — panels reflow to fill available space | MC-006 |

### 6.2 Application header (`mycom/widgets/header.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `AppHeader` widget with application title "MyCom" and current time | MC-006 |
| 2 | Display left panel path and right panel path in the header area | MC-006 |

### 6.3 Integration tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/integration/test_app.py` — app starts via `uv run mycom`, renders dual panels | MC-006 |
| 2 | `tests/integration/test_app.py` — Tab switches active panel, visual indicator updates | MC-006 |
| 3 | `tests/integration/test_app.py` — F10 or Ctrl+Q exits the application | MC-006 |
| 4 | `tests/integration/test_app.py` — terminal resize reflows panels | MC-006 |

### 6.4 Documentation

| # | Task | Issue |
|---|------|-------|
| 1 | Create `docs/architecture.md` — app shell layout diagram, component relationships | MC-006 |
| 2 | Update `docs/getting-started.md` — add screenshot of running app, basic usage | MC-006 |

---

## 7. File Navigation

### 7.1 Directory browsing

| # | Task | Issue |
|---|------|-------|
| 1 | Enter key on a directory → navigate into it, update `FileList` and `PathBar` | MC-007 |
| 2 | Enter key on `..` or Backspace → navigate to parent directory | MC-007 |
| 3 | Arrow keys (Up/Down) → move selection cursor in `FileList` | MC-007 |
| 4 | Home key → jump to first entry, End key → jump to last entry | MC-007 |
| 5 | Page Up / Page Down → scroll by visible page height | MC-007 |
| 6 | Handle permission denied errors — show error message, stay in current directory | MC-007 |
| 7 | Handle symlinks — follow symlinks for navigation, display symlink indicator in file list | MC-007 |

### 7.2 Quick filter

| # | Task | Issue |
|---|------|-------|
| 1 | Typing alphanumeric characters activates filter mode — filter bar appears above status bar | MC-007 |
| 2 | File list filters in real-time to show only matching entries (case-insensitive substring) | MC-007 |
| 3 | Escape clears filter and restores full listing | MC-007 |
| 4 | Enter on filtered list navigates to selected entry and clears filter | MC-007 |

### 7.3 Sorting (`mycom/operations/sort.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Sort file entries by name, size, date, extension | MC-007 |
| 2 | Clicking column header or pressing Ctrl+F3/F4/F5/F6 cycles sort field | MC-007 |
| 3 | Repeated sort on same field toggles ascending/descending | MC-007 |
| 4 | Sort indicator (▲/▼) displayed in active column header | MC-007 |
| 5 | Directories always sorted before files regardless of sort field | MC-007 |

### 7.4 Unit tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/unit/test_sort.py` — sort by name, size, date, extension; ascending/descending; dirs-first invariant | MC-007 |

### 7.5 Integration tests

| # | Task | Issue |
|---|------|-------|
| 1 | `tests/integration/test_navigation.py` — enter directory, go up, Home/End, Page Up/Down | MC-007 |
| 2 | `tests/integration/test_navigation.py` — quick filter narrows list, Escape clears, Enter navigates | MC-007 |
| 3 | `tests/integration/test_navigation.py` — sort toggle, direction change, indicator display | MC-007 |
| 4 | `tests/integration/test_navigation.py` — permission denied shows error, does not crash | MC-007 |

### 7.6 Documentation

| # | Task | Issue |
|---|------|-------|
| 1 | Create `docs/navigation.md` — navigation keys, quick filter usage, sorting behavior | MC-007 |

---

## 8. Documentation Site

### 8.1 API reference generation

| # | Task | Issue |
|---|------|-------|
| 1 | Configure `mkdocs-gen-files` to auto-generate API reference pages from `mycom/` source | MC-008 |
| 2 | Configure `mkdocs-literate-nav` for automatic navigation from generated pages | MC-008 |
| 3 | Add docstrings to all public classes and functions across all Phase 1 modules | MC-008 |

### 8.2 User guide pages

| # | Task | Issue |
|---|------|-------|
| 1 | Finalize `docs/index.md` — project overview, features, installation | MC-008 |
| 2 | Finalize `docs/getting-started.md` — install via `uv`, first run, basic usage | MC-008 |
| 3 | Create `docs/development.md` — dev setup with `uv`, running tests, linting, building docs | MC-008 |
| 4 | Review and finalize all docs pages created in previous issues | MC-008 |

### 8.3 Validation

| # | Task | Issue |
|---|------|-------|
| 1 | `uv run mkdocs build --strict` exits 0 with no warnings | MC-008 |
| 2 | Verify all API reference pages render correctly | MC-008 |
| 3 | Verify navigation structure is complete and logical | MC-008 |
