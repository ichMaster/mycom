"""File browser panel composing PathBar and FileList."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Static

from mycom.operations.sort import SORT_FIELDS, sort_entries
from mycom.panels.base import BasePanel, PanelMode
from mycom.panels.views import ViewMode
from mycom.utils.fs import FileEntry, format_date, format_permissions, format_size, list_directory
from mycom.widgets.dialog import ErrorDialog
from mycom.widgets.file_list import FileList
from mycom.widgets.path_bar import PathBar

logger = logging.getLogger(__name__)


class FileBrowserPanel(BasePanel):
    """Dual-panel file browser combining a path bar and file list."""

    DEFAULT_CSS = """
    FileBrowserPanel {
        height: 1fr;
        border: solid $panel-border;
        layout: vertical;
        background: $panel-bg;
    }
    FileBrowserPanel.active {
        border: solid $panel-border;
    }
    FileBrowserPanel > .footer {
        height: 1;
        background: $panel-bg;
        color: $panel-fg;
    }
    """

    def __init__(
        self,
        start_path: Path | None = None,
        show_hidden: bool = False,
        sort_field: str = "name",
        sort_ascending: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(mode=PanelMode.FILE_BROWSER, **kwargs)
        self._current_path = start_path or Path.cwd()
        self._path_bar = PathBar(path=self._current_path)
        self._file_list = FileList()
        self._footer = Static("", classes="footer")
        self._show_hidden = show_hidden
        self._entries: list[FileEntry] = []
        if sort_field not in SORT_FIELDS:
            logger.warning(
                "Unrecognized default_sort %r, falling back to 'name'", sort_field
            )
            sort_field = "name"
        self._sort_field = sort_field
        self._sort_ascending = sort_ascending
        self._filter_text = ""
        self._selected: set[str] = set()

    def compose(self) -> ComposeResult:
        yield self._path_bar
        yield self._file_list
        yield self._footer

    def on_mount(self) -> None:
        self._file_list.set_sort_indicator(self._sort_field, self._sort_ascending)
        self.refresh_listing()

    def on_data_table_cell_highlighted(self, event) -> None:
        self._update_footer()

    def on_data_table_row_highlighted(self, event) -> None:
        self._update_footer()

    def _update_footer(self) -> None:
        count = len(self._entries)
        text = f"{count} item{'s' if count != 1 else ''}  "
        if self._selected:
            total_bytes = sum(e.size for e in self._entries if e.name in self._selected)
            text += f"{len(self._selected)} selected ({format_size(total_bytes)})"
        else:
            text += "0 selected"
        name = self._file_list.selected_name
        if name:
            text += f"  {name}"
        if not self.is_active:
            # Placeholder — no real shutil.disk_usage query yet (decision:
            # feature-coverage.md Part 3). Not real data; don't wire a
            # consumer to this expecting an actual free-space figure.
            text += "  -- free"
        self._footer.update(text)

    def refresh_listing(self) -> None:
        """Reload the directory listing from the current path.

        On EACCES, ENOENT (vanished), or ENOTDIR (replaced by a file), keeps
        the previous listing and path, and shows an error dialog instead of
        silently displaying an empty panel.
        """
        try:
            entries = list_directory(
                self._current_path, show_hidden=self._show_hidden, strict=True
            )
        except OSError as exc:
            self._show_error(f"Cannot open {self._current_path}: {exc.strerror or exc}")
            return
        self._entries = entries
        self._render_entries()

    def _render_entries(self) -> None:
        sorted_entries = sort_entries(self._entries, self._sort_field, self._sort_ascending)
        if self._filter_text:
            ft = self._filter_text.lower()
            sorted_entries = [e for e in sorted_entries if ft in e.name.lower()]
        display_entries = [
            {
                "name": e.name,
                "size": "<DIR>" if e.is_dir else format_size(e.size),
                "modified": format_date(e.modified),
                "permissions": format_permissions(e.permissions),
                "is_dir": e.is_dir,
                "is_symlink": e.is_symlink,
            }
            for e in sorted_entries
        ]
        self._file_list.load_directory(
            display_entries, self._current_path, selected=frozenset(self._selected)
        )
        self._path_bar.path = self._current_path
        self._update_footer()

    def set_view_mode(self, mode: ViewMode) -> None:
        """Switch this panel's view mode (Brief/Full/Wide)."""
        self._file_list.set_view_mode(mode)
        self._update_footer()

    @property
    def view_mode(self) -> ViewMode:
        return self._file_list.view_mode

    def _show_error(self, message: str) -> None:
        # Widget.app raises NoActiveAppError (not None) when unmounted.
        if self.is_mounted:
            self.app.push_screen(ErrorDialog(message))

    def navigate_to(self, path: Path) -> None:
        """Navigate to a new directory. Stays on the previous path if it
        can't be opened (EACCES, vanished, replaced by a file, …)."""
        target = path.resolve()
        try:
            entries = list_directory(target, show_hidden=self._show_hidden, strict=True)
        except OSError as exc:
            self._show_error(f"Cannot open {target}: {exc.strerror or exc}")
            return
        self._current_path = target
        self._entries = entries
        self._selected.clear()
        self._render_entries()

    def navigate_up(self) -> None:
        """Navigate up; cursor lands on the directory just left, on success."""
        parent = self._current_path.parent
        if parent == self._current_path:
            return
        child_name = self._current_path.name
        self.navigate_to(parent)
        if self._current_path == parent:
            self._file_list.select_by_name(child_name)

    @property
    def current_path(self) -> Path:
        return self._current_path

    def get_current_path(self) -> Path:
        return self._current_path

    def get_selected_files(self) -> list[Path]:
        """Selection-else-cursor: the input contract file operations (v0.4) consume."""
        if self._selected:
            return [self._current_path / name for name in self._selected]
        name = self._file_list.selected_name
        if name and name != "..":
            return [self._current_path / name]
        return []

    def deselect(self, names: Iterable[str]) -> None:
        """Remove the given names from the selection (operations call this on success)."""
        for name in names:
            self._selected.discard(name)
        self._render_entries()

    @property
    def selected_names(self) -> frozenset[str]:
        return frozenset(self._selected)

    def replace_selection(self, names: Iterable[str]) -> None:
        """Overwrite the selection outright (e.g. Ctrl+U swapping it between panels)."""
        self._selected = set(names)
        self._render_entries()

    def toggle_selection_at_cursor(self) -> None:
        """Ins/Space: toggle the cursor entry's selection and move the cursor down."""
        name = self._file_list.selected_name
        if name is None:
            return
        if name != "..":
            if name in self._selected:
                self._selected.discard(name)
            else:
                self._selected.add(name)
        # Determine the next cursor target from the current (pre-rerender) layout,
        # then restore it by name after _render_entries() rebuilds the table.
        self._file_list.action_cursor_down()
        next_name = self._file_list.selected_name
        self._render_entries()
        if next_name:
            self._file_list.select_by_name(next_name)

    @property
    def file_list(self) -> FileList:
        return self._file_list

    def activate(self) -> None:
        super().activate()
        self._path_bar.set_active(True)
        self._update_footer()

    def deactivate(self) -> None:
        super().deactivate()
        self._path_bar.set_active(False)
        self._update_footer()

    def set_sort(self, field: str) -> None:
        """Set sort field. If same field, toggle direction."""
        if self._sort_field == field:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_field = field
            self._sort_ascending = True
        self._file_list.set_sort_indicator(self._sort_field, self._sort_ascending)
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
