"""Path bar widget showing current directory."""

from __future__ import annotations

from pathlib import Path

from textual.widget import Widget
from textual.widgets import Static


class PathBar(Widget):
    """Displays the current directory path, truncating from the left if needed."""

    DEFAULT_CSS = """
    PathBar {
        height: 1;
        background: $pathbar-active-bg;
        color: $pathbar-active-fg;
        padding: 0 1;
    }
    PathBar.inactive {
        background: $pathbar-inactive-bg;
        color: $pathbar-inactive-fg;
    }
    """

    def __init__(self, path: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = path or Path.cwd()
        self._label = Static(str(self._path))

    def compose(self):
        yield self._label

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, value: Path) -> None:
        self._path = value
        self._label.update(self._truncate(str(value)))

    def set_active(self, active: bool) -> None:
        """Toggle active/inactive visual state."""
        if active:
            self.remove_class("inactive")
        else:
            self.add_class("inactive")

    def _truncate(self, text: str, max_width: int = 60) -> str:
        if len(text) <= max_width:
            return text
        return "..." + text[-(max_width - 3) :]
