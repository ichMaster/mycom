"""MyCom — A modern dual-panel TUI file manager."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal

from mycom.config import load_config
from mycom.keymap import Keymap
from mycom.logging_setup import configure_logging
from mycom.panels.file_browser import FileBrowserPanel
from mycom.panels.views import ViewMode
from mycom.theme import FAR_CLASSIC_THEME
from mycom.widgets.dialog import InputDialog
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
        if len(self.screen_stack) > 1:
            # A modal (dialog) is on top — panel-key interception must not
            # leak through to the panel underneath (e.g. Enter dismissing a
            # dialog must not also navigate/go-up the panel behind it).
            return
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
        if name == "..":
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
        self.register_theme(FAR_CLASSIC_THEME)
        self.theme = "far-classic"
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
        yield StatusBar(keymap=self._keymap, scope="panel")

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
        self._apply_panel_widths()

    def action_panel_swap(self) -> None:
        """Swap both panels' paths, cursor positions, and selections (Ctrl+U)."""
        left, right = self._left_panel, self._right_panel
        left_path, right_path = left.current_path, right.current_path
        left_cursor = left.file_list.selected_name
        right_cursor = right.file_list.selected_name
        left_selected, right_selected = left.selected_names, right.selected_names
        left.navigate_to(right_path)
        right.navigate_to(left_path)
        left.replace_selection(right_selected)
        right.replace_selection(left_selected)
        if right_cursor is not None:
            left.file_list.select_by_name(right_cursor)
        if left_cursor is not None:
            right.file_list.select_by_name(left_cursor)

    def action_view_brief(self) -> None:
        self.active_panel.set_view_mode(ViewMode.BRIEF)

    def action_view_full(self) -> None:
        self.active_panel.set_view_mode(ViewMode.FULL)

    def action_view_wide(self) -> None:
        self.active_panel.set_view_mode(ViewMode.WIDE)

    def action_sort_name(self) -> None:
        self.active_panel.set_sort("name")

    def action_sort_ext(self) -> None:
        self.active_panel.set_sort("extension")

    def action_sort_mtime(self) -> None:
        self.active_panel.set_sort("date")

    def action_sort_size(self) -> None:
        self.active_panel.set_sort("size")

    def action_select_toggle(self) -> None:
        self.active_panel.toggle_selection_at_cursor()

    def action_select_mask(self) -> None:
        self._open_mask_dialog(select=True)

    def action_deselect_mask(self) -> None:
        self._open_mask_dialog(select=False)

    def action_select_invert(self) -> None:
        self.active_panel.invert_selection()

    def _open_mask_dialog(self, *, select: bool) -> None:
        panel = self.active_panel
        verb = "Select" if select else "Deselect"

        def on_dismiss(pattern: str | None) -> None:
            if pattern:
                panel.select_by_mask(pattern, select)

        self.push_screen(
            InputDialog(f"{verb} files matching (e.g. *.py;*.md):", default="*"),
            callback=on_dismiss,
        )

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
