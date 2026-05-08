# Phase 1 — Foundation Tasks

## 1. Project Scaffold

### 1.1 Package structure

| # | Task | Issue |
|---|------|-------|
| 1 | Create `mycom/` root with `pyproject.toml` (setuptools, Python 3.11+; dependencies: `textual>=0.80`, `pyte`, `anthropic`, `tomli`; dev dependencies via `[dev]` extra: `pytest`, `pytest-cov`, `pytest-asyncio`; entry point: `mycom = "mycom.app:main"`) | MC-001 |
| 2 | Create `mycom/` source package with `__init__.py` and version string | MC-001 |
| 3 | Create sub-packages: `panels/`, `operations/`, `plugins/`, `plugins/viewer/`, `plugins/editor/`, `widgets/`, `llm/`, `utils/` | MC-001 |
| 4 | Create `README.md` with project description, install instructions, and usage | MC-001 |
| 5 | Create `.gitignore` for Python, venv, IDE files | MC-001 |
| 6 | Create `tests/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/` | MC-001 |

### 1.2 Configuration

| # | Task | Issue |
|---|------|-------|
| 1 | Create default config file `~/.config/mycom/config.toml` schema definition | MC-002 |
| 2 | Implement `mycom/config.py` — TOML config loader with defaults, supporting: config file > defaults | MC-002 |
| 3 | Define config schema: `show_hidden`, `confirm_delete`, `default_sort`, `default_sort_direction` | MC-002 |
| 4 | Define keybinding config section: `copy`, `move`, `delete`, `rename`, `view`, `edit`, `mkdir`, `terminal_toggle`, `llm_toggle`, `quit` | MC-002 |
| 5 | Define LLM config section: `api_key_env`, `model`, `max_context_files` | MC-002 |
| 6 | Define plugin config section: `viewers` (extension → plugin name map), `editors` (extension → plugin name map) | MC-002 |

### 1.3 Key binding definitions

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `mycom/utils/keys.py` — key binding registry that maps action names to key sequences | MC-002 |
| 2 | Define default F-key bindings: F1=help, F3=view, F4=edit, F5=copy, F6=move, F7=mkdir, F8=delete, F10=quit | MC-002 |
| 3 | Define navigation keys: Tab=switch panel, Enter=open, Backspace=go up, Home/End=first/last file | MC-002 |
| 4 | Define mode switching keys: Ctrl+T=terminal toggle, Ctrl+L=LLM chat toggle | MC-002 |
| 5 | Support loading custom bindings from config file and merging with defaults | MC-002 |

---

## 2. Core Widgets

### 2.1 File list widget (`mycom/widgets/file_list.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `FileList` Textual widget based on `DataTable` | MC-003 |
| 2 | Display columns: icon/type indicator, name, size (human-readable), date modified, permissions | MC-003 |
| 3 | `..` entry at top of every listing (except root `/`) | MC-003 |
| 4 | Directories listed before files | MC-003 |
| 5 | Current selection highlight with distinct active/inactive panel styling | MC-003 |
| 6 | Handle empty directories gracefully | MC-003 |
| 7 | Lazy loading — only stat files visible in viewport for large directories | MC-003 |

### 2.2 Status bar (`mycom/widgets/status_bar.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `StatusBar` Textual widget displayed at the bottom of the screen | MC-003 |
| 2 | Display F-key hints: F1 Help, F3 View, F4 Edit, F5 Copy, F6 Move, F7 MkDir, F8 Delete, F10 Quit | MC-003 |
| 3 | Hints are clickable (mouse support) and reflect current keybinding config | MC-003 |
| 4 | Highlight active function key on press | MC-003 |

### 2.3 Path bar (`mycom/widgets/path_bar.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `PathBar` widget showing the current directory path for each panel | MC-003 |
| 2 | Truncate long paths from the left, preserving the trailing directory components | MC-003 |
| 3 | Visual indicator for active vs inactive panel (bold/dim or color) | MC-003 |

### 2.4 Dialog widgets (`mycom/widgets/dialog.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `ConfirmDialog` — modal Yes/No dialog for destructive operations | MC-003 |
| 2 | Implement `InputDialog` — modal text input for rename, mkdir, go-to-path | MC-003 |
| 3 | Implement `ProgressDialog` — modal progress bar for file operations | MC-003 |
| 4 | All dialogs are keyboard navigable (Tab between buttons, Enter to confirm, Escape to cancel) | MC-003 |

---

## 3. Panel System

### 3.1 Base panel interface (`mycom/panels/base.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Define `BasePanel` abstract class extending Textual `Widget` | MC-004 |
| 2 | Define panel mode enum: `FILE_BROWSER`, `TERMINAL`, `LLM_CHAT` | MC-004 |
| 3 | Abstract methods: `activate()`, `deactivate()`, `get_current_path()`, `get_selected_files()` | MC-004 |
| 4 | Panel header with mode indicator and title | MC-004 |

### 3.2 File browser panel (`mycom/panels/file_browser.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `FileBrowserPanel` extending `BasePanel` | MC-004 |
| 2 | Compose `PathBar` + `FileList` widgets vertically | MC-004 |
| 3 | Initialize with a starting directory (default: home directory or CWD) | MC-004 |
| 4 | Expose `current_path` property synced with `PathBar` | MC-004 |
| 5 | Expose `selected_files` property returning list of selected file paths | MC-004 |
| 6 | Active/inactive visual state (border color or header highlight) | MC-004 |

---

## 4. Application Shell

### 4.1 Main application (`mycom/app.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `MyComApp` extending `textual.App` | MC-005 |
| 2 | Layout: two `FileBrowserPanel` side-by-side (horizontal split, equal width) | MC-005 |
| 3 | Bottom area: `StatusBar` widget | MC-005 |
| 4 | Track active panel (left or right), default to left on startup | MC-005 |
| 5 | Tab key switches active panel — update visual state of both panels | MC-005 |
| 6 | Load configuration on startup from `config.py` | MC-005 |
| 7 | `main()` entry point function that creates and runs the app | MC-005 |
| 8 | CSS styling for the dual-panel layout (Textual CSS file `mycom/app.tcss`) | MC-005 |
| 9 | Handle terminal resize gracefully — panels reflow to fill available space | MC-005 |

### 4.2 Application header (`mycom/widgets/header.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `AppHeader` widget with application title "MyCom" and current time | MC-005 |
| 2 | Display left panel path and right panel path in the header area | MC-005 |

---

## 5. File Navigation

### 5.1 Directory browsing

| # | Task | Issue |
|---|------|-------|
| 1 | Enter key on a directory → navigate into it, update `FileList` and `PathBar` | MC-006 |
| 2 | Enter key on `..` or Backspace → navigate to parent directory | MC-006 |
| 3 | Arrow keys (Up/Down) → move selection cursor in `FileList` | MC-006 |
| 4 | Home key → jump to first entry, End key → jump to last entry | MC-006 |
| 5 | Page Up / Page Down → scroll by visible page height | MC-006 |
| 6 | Handle permission denied errors — show error message, stay in current directory | MC-006 |
| 7 | Handle symlinks — follow symlinks for navigation, display symlink indicator in file list | MC-006 |

### 5.2 Quick filter

| # | Task | Issue |
|---|------|-------|
| 1 | Typing alphanumeric characters activates filter mode — filter bar appears above status bar | MC-006 |
| 2 | File list filters in real-time to show only matching entries (case-insensitive substring) | MC-006 |
| 3 | Escape clears filter and restores full listing | MC-006 |
| 4 | Enter on filtered list navigates to selected entry and clears filter | MC-006 |

### 5.3 Sorting

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `mycom/operations/sort.py` — sort file entries by name, size, date, extension | MC-006 |
| 2 | Clicking column header or pressing Ctrl+F3/F4/F5/F6 cycles sort field | MC-006 |
| 3 | Repeated sort on same field toggles ascending/descending | MC-006 |
| 4 | Sort indicator (▲/▼) displayed in active column header | MC-006 |
| 5 | Directories always sorted before files regardless of sort field | MC-006 |

---

## 6. Filesystem Helpers

### 6.1 Filesystem utilities (`mycom/utils/fs.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | `list_directory(path, show_hidden) → list[FileEntry]` — stat each entry, return structured list | MC-007 |
| 2 | `FileEntry` dataclass: name, path, is_dir, is_symlink, size, modified, permissions | MC-007 |
| 3 | `format_size(bytes) → str` — human-readable file sizes (B, KB, MB, GB) | MC-007 |
| 4 | `format_date(timestamp) → str` — formatted date for display | MC-007 |
| 5 | `format_permissions(mode) → str` — rwx permission string | MC-007 |
| 6 | Handle `PermissionError` and `OSError` gracefully in all functions | MC-007 |

---

## 7. Testing

### 7.1 Test fixtures

| # | Task | Issue |
|---|------|-------|
| 1 | Create `tests/fixtures/sample_tree/` — directory tree with files, subdirs, symlinks, hidden files | MC-008 |
| 2 | Create `tests/fixtures/config.toml` — sample configuration file for testing | MC-008 |

### 7.2 Unit tests

| # | Task | Issue |
|---|------|-------|
| 1 | `test_config.py` — config loading, defaults, custom values, missing file handling | MC-008 |
| 2 | `test_keys.py` — key binding registry, custom overrides, default fallback | MC-008 |
| 3 | `test_fs.py` — list_directory, format_size, format_date, format_permissions, error handling | MC-008 |
| 4 | `test_sort.py` — sort by name, size, date, extension; ascending/descending; dirs-first invariant | MC-008 |

### 7.3 Integration tests

| # | Task | Issue |
|---|------|-------|
| 1 | `test_app.py` — app starts, renders dual panels, tab switches active panel | MC-008 |
| 2 | `test_navigation.py` — enter directory, go up, quick filter, sort toggle | MC-008 |
| 3 | `test_widgets.py` — file list rendering, status bar display, dialog interactions | MC-008 |
