"""File list widget based on Textual DataTable, driven by ViewMode column specs."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import DataTable
from textual.widgets.data_table import RowDoesNotExist

from mycom.panels.views import FIELD_HEADERS, VIEW_SPECS, ViewMode
from mycom.theme import SELECTED_FG

_MIN_BRIEF_COLUMN_WIDTH = 22
_NAME_TRUNCATE_WIDTH = 40
_BRIEF_TRUNCATE_WIDTH = _MIN_BRIEF_COLUMN_WIDTH - 2

# Which displayed column carries the sort glyph for a given sort field.
# "extension" has no dedicated column — its glyph rides on Name.
_SORT_COLUMN_FOR_FIELD = {
    "name": "name",
    "extension": "name",
    "date": "modified",
    "size": "size",
}


def truncate_name(text: str, max_width: int) -> str:
    """Truncate to at most max_width codepoints, appending an ellipsis."""
    if len(text) <= max_width:
        return text
    if max_width <= 1:
        return text[:max_width]
    return text[: max_width - 1] + "…"


def _icon(entry: dict) -> str:
    if entry.get("is_symlink"):
        return "~"
    if entry.get("is_dir"):
        return "\\"
    return " "


def _bare_name(raw: str) -> str:
    """Strip a Brief-grid cell's leading icon char, except for the literal ".."."""
    return raw if raw == ".." else raw[1:]


def _highlight_if_selected(text: str, name: str, selected: frozenset[str]) -> str:
    if name not in selected:
        return text
    return f"[{SELECTED_FG}]{text}[/{SELECTED_FG}]"


class FileList(DataTable):
    """Displays a directory listing; column layout driven by ViewMode (data, not subclasses)."""

    DEFAULT_CSS = """
    FileList {
        height: 1fr;
        background: $panel-bg;
        color: $panel-fg;
    }
    FileList > .datatable--header {
        background: $panel-bg;
        color: $header-fg;
    }
    FileList > .datatable--cursor {
        background: $cursor-bg;
        color: $cursor-fg;
    }
    FileList > .datatable--even-row {
        background: $panel-bg;
    }
    FileList > .datatable--odd-row {
        background: $panel-bg;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_path: Path = Path.cwd()
        self._entries: list[dict] = []
        self._view_mode: ViewMode = ViewMode.FULL
        self._brief_columns: int = 1
        self._brief_names: list[str] = []  # icon+name (or "..") in grid reading order
        self._sort_field: str | None = None
        self._sort_ascending: bool = True
        self._selected_names: frozenset[str] = frozenset()
        self.cursor_type = "row"
        self.zebra_stripes = False

    def on_mount(self) -> None:
        self._rebuild_columns()

    @property
    def view_mode(self) -> ViewMode:
        return self._view_mode

    def set_view_mode(self, mode: ViewMode) -> None:
        """Switch view mode and re-render the current entries."""
        if mode is self._view_mode:
            return
        self._view_mode = mode
        self._rebuild_columns()
        self.load_directory(self._entries, self._current_path, selected=self._selected_names)

    def set_sort_indicator(self, field: str, ascending: bool) -> None:
        """Record the active sort field/direction and refresh header glyphs.

        Rebuilds (and thus clears) columns — callers reload entries right after.
        """
        self._sort_field = field
        self._sort_ascending = ascending
        self._rebuild_columns()

    def _rebuild_columns(self) -> None:
        self.clear(columns=True)
        if self._view_mode is ViewMode.BRIEF:
            width = max(self.size.width, _MIN_BRIEF_COLUMN_WIDTH)
            self._brief_columns = max(1, width // _MIN_BRIEF_COLUMN_WIDTH)
            for i in range(self._brief_columns):
                self.add_column("", key=f"col{i}")
        else:
            self._brief_columns = 1
            spec = VIEW_SPECS[self._view_mode]
            self.add_column("", key="icon")
            glyph_column = _SORT_COLUMN_FOR_FIELD.get(self._sort_field or "")
            glyph = " ▲" if self._sort_ascending else " ▼"
            for field in spec.fields:
                label = FIELD_HEADERS[field]
                if field == glyph_column:
                    label += glyph
                self.add_column(label, key=field)

    def load_directory(
        self,
        entries: list[dict],
        path: Path,
        selected: frozenset[str] | None = None,
    ) -> None:
        """Load file entries into the table.

        Args:
            entries: List of dicts with keys: name, size, modified, permissions, is_dir, is_symlink
            path: The directory path these entries belong to.
            selected: Names to render highlighted (yellow). `None` keeps whatever
                was last set (internal reloads from set_view_mode/set_sort_indicator
                don't have a fresh set to pass and must not silently clear it).
        """
        self._current_path = path
        self._entries = entries
        if selected is not None:
            self._selected_names = selected
        if self._view_mode is ViewMode.BRIEF:
            self._load_brief(entries, path)
        else:
            self._load_columns(entries, path)

    def _ordered(self, entries: list[dict]) -> list[dict]:
        dirs = [e for e in entries if e.get("is_dir")]
        files = [e for e in entries if not e.get("is_dir")]
        return dirs + files

    def _load_columns(self, entries: list[dict], path: Path) -> None:
        self.clear()
        spec = VIEW_SPECS[self._view_mode]
        if path != Path("/"):
            blanks = ["" if f != "name" else ".." for f in spec.fields]
            self.add_row("..", *blanks, key="..")
        for entry in self._ordered(entries):
            cells = [_icon(entry)]
            for field in spec.fields:
                value = entry.get(field, "")
                if field == "name":
                    value = truncate_name(str(value), _NAME_TRUNCATE_WIDTH)
                    value = _highlight_if_selected(value, entry["name"], self._selected_names)
                cells.append(value)
            self.add_row(*cells, key=entry["name"])

    def _load_brief(self, entries: list[dict], path: Path) -> None:
        self.clear()
        names: list[str] = []
        if path != Path("/"):
            names.append("..")
        for entry in self._ordered(entries):
            names.append(_icon(entry) + entry["name"])
        self._brief_names = names

        cols = self._brief_columns
        num_rows = -(-len(names) // cols) if names else 0
        for r in range(num_rows):
            cells = []
            for c in range(cols):
                idx = r * cols + c
                if idx < len(names):
                    raw = names[idx]
                    cell = truncate_name(raw, _BRIEF_TRUNCATE_WIDTH)
                    cell = _highlight_if_selected(cell, _bare_name(raw), self._selected_names)
                else:
                    cell = ""
                cells.append(cell)
            self.add_row(*cells)

    @property
    def current_path(self) -> Path:
        return self._current_path

    @property
    def selected_name(self) -> str | None:
        """Return the name of the currently highlighted entry."""
        if self.row_count == 0:
            return None
        if self._view_mode is ViewMode.BRIEF:
            row, col = self.cursor_coordinate
            idx = row * self._brief_columns + col
            if not (0 <= idx < len(self._brief_names)):
                return None
            return _bare_name(self._brief_names[idx])
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        return str(row_key.value) if row_key.value is not None else None

    def select_by_name(self, name: str) -> None:
        """Move the cursor to the row/cell for `name`; falls back to the first entry."""
        if self.row_count == 0:
            return
        if self._view_mode is ViewMode.BRIEF:
            idx = 0
            for i, raw in enumerate(self._brief_names):
                if _bare_name(raw) == name:
                    idx = i
                    break
            cols = self._brief_columns
            self.move_cursor(row=idx // cols, column=idx % cols)
            return
        try:
            row_index = self.get_row_index(name)
        except RowDoesNotExist:
            row_index = 0
        self.move_cursor(row=row_index)
