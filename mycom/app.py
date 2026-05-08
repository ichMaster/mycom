"""MyCom — A modern dual-panel TUI file manager."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal

from mycom.config import load_config
from mycom.panels.file_browser import FileBrowserPanel
from mycom.utils.keys import KeyBindings
from mycom.widgets.header import AppHeader
from mycom.widgets.status_bar import StatusBar


class MyComApp(App):
    """MyCom dual-panel file manager application."""

    TITLE = "MyCom"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("f10", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def on_key(self, event) -> None:
        if event.key == "tab":
            event.prevent_default()
            event.stop()
            self.action_switch_panel()

    def __init__(self) -> None:
        super().__init__()
        self._config = load_config()
        self._keybindings = KeyBindings(self._config.keybindings)
        self._left_panel: FileBrowserPanel | None = None
        self._right_panel: FileBrowserPanel | None = None
        self._active_side: str = "left"

    def compose(self) -> ComposeResult:
        yield AppHeader()
        with Horizontal(id="panel-container"):
            self._left_panel = FileBrowserPanel(start_path=Path.cwd(), id="left-panel")
            self._right_panel = FileBrowserPanel(start_path=Path.cwd(), id="right-panel")
            yield self._left_panel
            yield self._right_panel
        yield StatusBar()

    def on_mount(self) -> None:
        self.active_panel.activate()

    @property
    def active_panel(self) -> FileBrowserPanel:
        if self._active_side == "left":
            return self._left_panel  # type: ignore[return-value]
        return self._right_panel  # type: ignore[return-value]

    @property
    def inactive_panel(self) -> FileBrowserPanel:
        if self._active_side == "left":
            return self._right_panel  # type: ignore[return-value]
        return self._left_panel  # type: ignore[return-value]

    def action_switch_panel(self) -> None:
        self.active_panel.deactivate()
        self._active_side = "right" if self._active_side == "left" else "left"
        self.active_panel.activate()
        self.active_panel.file_list.focus()


def main():
    app = MyComApp()
    app.run()


if __name__ == "__main__":
    main()
