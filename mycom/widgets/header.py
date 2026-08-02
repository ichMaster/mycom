"""Application header widget."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static


class AppHeader(Widget):
    """Top bar showing application title."""

    DEFAULT_CSS = """
    AppHeader {
        dock: top;
        height: 1;
        background: $pathbar-active-bg;
        color: $pathbar-active-fg;
        content-align: center middle;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._label = Static("MyCom")

    def compose(self):
        yield self._label
