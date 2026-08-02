"""File list widget based on Textual DataTable."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import DataTable
from textual.widgets.data_table import RowDoesNotExist


class FileList(DataTable):
    """Displays a directory listing with columns for type, name, size, date, permissions."""

    DEFAULT_CSS = """
    FileList {
        height: 1fr;
        background: #000080;
        color: #00ffff;
    }
    FileList > .datatable--header {
        background: #000080;
        color: #ffff00;
    }
    FileList > .datatable--cursor {
        background: #008080;
        color: #000000;
    }
    FileList > .datatable--even-row {
        background: #000080;
    }
    FileList > .datatable--odd-row {
        background: #000080;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_path: Path = Path.cwd()
        self._entries: list[dict] = []
        self.cursor_type = "row"
        self.zebra_stripes = False

    def on_mount(self) -> None:
        self.add_columns("", "Name", "Size", "Modified", "Perms")

    def load_directory(self, entries: list[dict], path: Path) -> None:
        """Load file entries into the table.

        Args:
            entries: List of dicts with keys: name, size, modified, permissions, is_dir, is_symlink
            path: The directory path these entries belong to.
        """
        self._current_path = path
        self._entries = entries
        self.clear()

        if path != Path("/"):
            self.add_row("..", "..", "", "", "", key="__parent__")

        dirs = [e for e in entries if e.get("is_dir")]
        files = [e for e in entries if not e.get("is_dir")]

        for entry in dirs + files:
            if entry.get("is_symlink"):
                icon = "~"
            elif entry.get("is_dir"):
                icon = "\\"
            else:
                icon = " "
            self.add_row(
                icon,
                entry["name"],
                entry.get("size", ""),
                entry.get("modified", ""),
                entry.get("permissions", ""),
                key=entry["name"],
            )

    @property
    def current_path(self) -> Path:
        return self._current_path

    def select_by_name(self, name: str) -> None:
        """Move the cursor to the row keyed by `name`; falls back to row 0."""
        if self.row_count == 0:
            return
        try:
            row_index = self.get_row_index(name)
        except RowDoesNotExist:
            row_index = 0
        self.move_cursor(row=row_index)

    @property
    def selected_name(self) -> str | None:
        """Return the name of the currently highlighted entry."""
        if self.row_count == 0:
            return None
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        return str(row_key.value)
