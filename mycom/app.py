"""MyCom — A modern dual-panel TUI file manager."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal

from mycom.config import load_config
from mycom.keymap import Keymap
from mycom.logging_setup import configure_logging
from mycom.panels.file_browser import FileBrowserPanel
from mycom.widgets.header import AppHeader
from mycom.widgets.status_bar import StatusBar

# Actions that must intercept a key before Textual's own widget-level bindings
# see it (DataTable claims "enter" for select_cursor; Tab is the framework's
# default focus-cycling key) — handled in on_key, not App.bind.
_INTERCEPTED_ACTIONS = frozenset({"switch_panel", "open", "go_up"})

_RESIZE_STEPS = (30, 50, 70)


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
        configure_logging()
        self._config = load_config()
        self._keymap = Keymap(self._config.keybindings)
        for key, action, label in self._keymap.bindings_for_context("panel"):
            if action in _INTERCEPTED_ACTIONS:
                continue
            self.bind(key, action, description=label)
        self._left_panel: FileBrowserPanel | None = None
        self._right_panel: FileBrowserPanel | None = None
        self._active_side: str = "left"
        self._resize_index: int = _RESIZE_STEPS.index(50)

    def compose(self) -> ComposeResult:
        general = self._config.general
        panel_kwargs = {
            "show_hidden": general.show_hidden,
            "sort_field": general.default_sort,
            "sort_ascending": general.default_sort_direction == "asc",
        }
        yield AppHeader()
        with Horizontal(id="panel-container"):
            self._left_panel = FileBrowserPanel(
                start_path=Path.cwd(), id="left-panel", **panel_kwargs
            )
            self._right_panel = FileBrowserPanel(
                start_path=Path.cwd(), id="right-panel", **panel_kwargs
            )
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

    def action_panel_swap(self) -> None:
        """Swap both panels' paths and cursor positions (Ctrl+U).

        Selections are not swapped — the selection model doesn't exist yet
        (lands in v0.3).
        """
        left, right = self._left_panel, self._right_panel
        left_path, right_path = left.current_path, right.current_path
        left_cursor = left.file_list.selected_name
        right_cursor = right.file_list.selected_name
        left.navigate_to(right_path)
        right.navigate_to(left_path)
        if right_cursor is not None:
            left.file_list.select_by_name(right_cursor)
        if left_cursor is not None:
            right.file_list.select_by_name(left_cursor)

    def action_resize_grow(self) -> None:
        self._resize_index = min(self._resize_index + 1, len(_RESIZE_STEPS) - 1)
        self._apply_panel_widths()

    def action_resize_shrink(self) -> None:
        self._resize_index = max(self._resize_index - 1, 0)
        self._apply_panel_widths()

    def _apply_panel_widths(self) -> None:
        pct = _RESIZE_STEPS[self._resize_index]
        self.active_panel.styles.width = f"{pct}%"
        self.inactive_panel.styles.width = "1fr"


def main():
    app = MyComApp()
    app.run()


if __name__ == "__main__":
    main()
