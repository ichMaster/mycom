"""File browser panel composing PathBar and FileList."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult

from mycom.operations.sort import sort_entries
from mycom.panels.base import BasePanel, PanelMode
from mycom.utils.fs import FileEntry, format_date, format_permissions, format_size, list_directory
from mycom.widgets.file_list import FileList
from mycom.widgets.path_bar import PathBar


class FileBrowserPanel(BasePanel):
    """Dual-panel file browser combining a path bar and file list."""

    DEFAULT_CSS = """
    FileBrowserPanel {
        height: 1fr;
        border: solid $secondary;
        layout: vertical;
    }
    FileBrowserPanel.active {
        border: solid $primary;
    }
    """

    def __init__(self, start_path: Path | None = None, **kwargs) -> None:
        super().__init__(mode=PanelMode.FILE_BROWSER, **kwargs)
        self._current_path = start_path or Path.cwd()
        self._path_bar = PathBar(path=self._current_path)
        self._file_list = FileList()
        self._show_hidden = False
        self._entries: list[FileEntry] = []
        self._sort_field = "name"
        self._sort_ascending = True
        self._filter_text = ""

    def compose(self) -> ComposeResult:
        yield self._path_bar
        yield self._file_list

    def on_mount(self) -> None:
        self.refresh_listing()

    def refresh_listing(self) -> None:
        """Reload the directory listing from the filesystem."""
        self._entries = list_directory(self._current_path, show_hidden=self._show_hidden)
        sorted_entries = sort_entries(self._entries, self._sort_field, self._sort_ascending)
        if self._filter_text:
            ft = self._filter_text.lower()
            sorted_entries = [e for e in sorted_entries if ft in e.name.lower()]
        display_entries = [
            {
                "name": e.name,
                "size": format_size(e.size) if not e.is_dir else "",
                "modified": format_date(e.modified),
                "permissions": format_permissions(e.permissions),
                "is_dir": e.is_dir,
                "is_symlink": e.is_symlink,
            }
            for e in sorted_entries
        ]
        self._file_list.load_directory(display_entries, self._current_path)
        self._path_bar.path = self._current_path

    def navigate_to(self, path: Path) -> None:
        """Navigate to a new directory."""
        self._current_path = path.resolve()
        self.refresh_listing()

    def navigate_up(self) -> None:
        """Navigate to the parent directory."""
        parent = self._current_path.parent
        if parent != self._current_path:
            self.navigate_to(parent)

    @property
    def current_path(self) -> Path:
        return self._current_path

    def get_current_path(self) -> Path:
        return self._current_path

    def get_selected_files(self) -> list[Path]:
        name = self._file_list.selected_name
        if name and name != "__parent__":
            return [self._current_path / name]
        return []

    @property
    def file_list(self) -> FileList:
        return self._file_list

    def activate(self) -> None:
        super().activate()
        self._path_bar.set_active(True)

    def deactivate(self) -> None:
        super().deactivate()
        self._path_bar.set_active(False)

    def set_sort(self, field: str) -> None:
        """Set sort field. If same field, toggle direction."""
        if self._sort_field == field:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_field = field
            self._sort_ascending = True
        self.refresh_listing()

    @property
    def sort_field(self) -> str:
        return self._sort_field

    @property
    def sort_ascending(self) -> bool:
        return self._sort_ascending

    def set_filter(self, text: str) -> None:
        """Set the quick filter text."""
        self._filter_text = text
        self.refresh_listing()

    def clear_filter(self) -> None:
        """Clear the quick filter."""
        self._filter_text = ""
        self.refresh_listing()

    @property
    def filter_text(self) -> str:
        return self._filter_text
