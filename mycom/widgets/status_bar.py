"""Status bar widget showing F-key hints."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static

HINT_ITEMS = [
    ("f1", "Help"),
    ("f3", "View"),
    ("f4", "Edit"),
    ("f5", "Copy"),
    ("f6", "Move"),
    ("f7", "MkDir"),
    ("f8", "Delete"),
    ("f10", "Quit"),
]


class StatusBar(Widget):
    """Bottom bar displaying F-key action hints."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: #000000;
    }
    StatusBar Horizontal {
        width: 1fr;
        height: 1;
        background: #000000;
    }
    StatusBar .hint-key {
        color: #c0c0c0;
        background: #000000;
        padding: 0 0;
    }
    StatusBar .hint-label {
        color: #000000;
        background: #008080;
        padding: 0 1;
    }
    """

    def __init__(self, hints: list[tuple[str, str]] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._hints = hints or HINT_ITEMS

    def compose(self) -> ComposeResult:
        with Horizontal():
            for key, label in self._hints:
                yield Static(key.upper(), classes="hint-key")
                yield Static(label, classes="hint-label")

    @property
    def hints(self) -> list[tuple[str, str]]:
        return list(self._hints)
