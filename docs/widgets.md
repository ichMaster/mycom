# Widgets

MyCom is built from composable Textual widgets.

## FileList

`mycom.widgets.file_list.FileList`

A `DataTable`-based widget displaying directory contents with columns:

| Column | Description |
|--------|-------------|
| Icon | 📁 directory, 📄 file, 🔗 symlink |
| Name | File or directory name |
| Size | Human-readable file size |
| Modified | Last modification date |
| Perms | Unix permission string |

Directories are always listed before files. A `..` entry appears at the top of every listing except the root directory.

## StatusBar

`mycom.widgets.status_bar.StatusBar`

A bottom-docked bar showing F-key action hints (F1 Help, F3 View, F4 Edit, etc.). Hints are clickable and reflect the current keybinding configuration.

## PathBar

`mycom.widgets.path_bar.PathBar`

Displays the current directory path for a panel. Long paths are truncated from the left. Supports active/inactive visual states.

## Dialogs

### ConfirmDialog

`mycom.widgets.dialog.ConfirmDialog`

A modal Yes/No dialog for destructive operations. Returns `True` (Yes) or `False` (No/Escape).

### InputDialog

`mycom.widgets.dialog.InputDialog`

A modal text input dialog. Returns the entered text (OK) or `None` (Cancel/Escape).

### ProgressDialog

`mycom.widgets.dialog.ProgressDialog`

A modal progress bar for long-running file operations.

All dialogs are fully keyboard navigable (Tab between buttons, Enter to confirm, Escape to cancel).
