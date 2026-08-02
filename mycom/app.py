"""MyCom — A modern dual-panel TUI file manager."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal

from mycom.config import load_config
from mycom.keymap import Keymap
from mycom.panels.file_browser import FileBrowserPanel
from mycom.widgets.header import AppHeader
from mycom.widgets.status_bar import StatusBar

# Actions that must intercept a key before Textual's own widget-level bindings
# see it (DataTable claims "enter" for select_cursor; Tab is the framework's
# default focus-cycling key) — handled in on_key, not App.bind.
_INTERCEPTED_ACTIONS = frozenset({"switch_panel", "open", "go_up"})


class MyComApp(App):
    """MyCom dual-panel file manager application."""

    TITLE = "MyCom"
    CSS_PATH = "app.tcss"

    def on_key(self, event) -> None:
        actions = self._keymap.actions_for_key(event.key, context="panel")
        if "switch_panel" in actions:
            event.prevent_default()
            event.stop()
            self.action_switch_panel()
        elif "open" in actions:
            self._handle_enter()
        elif "go_up" in actions:
            self.active_panel.navigate_up()

    def _handle_enter(self) -> None:
        panel = self.active_panel
        name = panel.file_list.selected_name
        if name is None:
            return
        if name == "__parent__":
            panel.navigate_up()
            return
        target = panel.current_path / name
        if target.is_dir():
            try:
                panel.navigate_to(target)
            except PermissionError:
                self.notify("Permission denied", severity="error")
        # File open is handled by viewer/editor in later phases

    def __init__(self) -> None:
        super().__init__()
        self._config = load_config()
        self._keymap = Keymap(self._config.keybindings)
        for key, action, label in self._keymap.bindings_for_context("panel"):
            if action in _INTERCEPTED_ACTIONS:
                continue
            self.bind(key, action, description=label)
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
