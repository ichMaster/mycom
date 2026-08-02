"""MyCom — A modern dual-panel TUI file manager."""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal

from mycom.config import GeneralConfig, load_config
from mycom.keymap import Keymap
from mycom.logging_setup import configure_logging
from mycom.panels.file_browser import FileBrowserPanel
from mycom.panels.views import ViewMode
from mycom.state import PanelState, StateDB
from mycom.theme import FAR_CLASSIC_THEME
from mycom.widgets.dialog import InputDialog
from mycom.widgets.header import AppHeader
from mycom.widgets.status_bar import StatusBar

logger = logging.getLogger(__name__)

# Actions that must intercept a key before Textual's own widget-level bindings
# see it (DataTable claims "enter" for select_cursor; Tab is the framework's
# default focus-cycling key) — handled in on_key, not App.bind.
_INTERCEPTED_ACTIONS = frozenset({"switch_panel", "open", "go_up"})

_RESIZE_STEPS = (30, 50, 70)

_SAVE_DEBOUNCE_SECONDS = 0.5


def _resolve_startup_path(path: Path) -> Path:
    """A saved/configured path that no longer exists (or isn't a directory)
    falls back to the nearest existing ancestor, then $HOME.

    The filesystem root always exists, so a naive "walk up until is_dir()"
    would silently return "/" for a fully-vanished path instead of ever
    reaching the documented $HOME fallback — treat reaching the root without
    finding a real ancestor as exhausting the search.
    """
    candidate = path
    while candidate != candidate.parent and not candidate.is_dir():
        candidate = candidate.parent
    if candidate == candidate.parent:  # walked all the way to "/"
        return Path.home()
    return candidate


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
            self._schedule_save()

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
                self._schedule_save()
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
        try:
            self._state_db: StateDB | None = StateDB()
        except Exception:
            logger.warning("Could not open state DB — persistence disabled", exc_info=True)
            self._state_db = None
        self._save_timer = None
        for key, action, label in self._keymap.bindings_for_context("panel"):
            if action in _INTERCEPTED_ACTIONS:
                continue
            self.bind(key, action, description=label)
        self._left_panel: FileBrowserPanel | None = None
        self._right_panel: FileBrowserPanel | None = None
        self._active_side: str = "left"
        self._resize_index: int = _RESIZE_STEPS.index(50)
        self._show_hidden: bool = False  # re-derived from config/state in compose()
        self._pending_view_modes: dict[str, ViewMode] = {}

    def _app_state(self, key: str, default: str | None = None) -> str | None:
        if self._state_db is None:
            return default
        return self._state_db.get_app_state(key, default=default)

    def compose(self) -> ComposeResult:
        general = self._config.general

        saved_hidden = self._app_state("show_hidden")
        self._show_hidden = (
            saved_hidden == "true" if saved_hidden is not None else general.show_hidden
        )

        saved_active_side = self._app_state("active_side")
        if saved_active_side in ("left", "right"):
            self._active_side = saved_active_side

        saved_resize = self._app_state("resize_index")
        if saved_resize is not None and saved_resize.isdigit():
            index = int(saved_resize)
            if 0 <= index < len(_RESIZE_STEPS):
                self._resize_index = index

        yield AppHeader()
        with Horizontal(id="panel-container"):
            self._left_panel = self._build_panel("left", "left-panel", general)
            self._right_panel = self._build_panel("right", "right-panel", general)
            yield self._left_panel
            yield self._right_panel
        yield StatusBar(keymap=self._keymap, scope="panel")

    def _build_panel(self, side: str, widget_id: str, general: GeneralConfig) -> FileBrowserPanel:
        saved: PanelState | None = self._state_db.get_panel_state(side) if self._state_db else None
        if saved is not None:
            start_path = _resolve_startup_path(Path(saved.path))
            sort_field = saved.sort_field
            sort_ascending = saved.sort_ascending
            with contextlib.suppress(ValueError):
                self._pending_view_modes[widget_id] = ViewMode(saved.view_mode)
        else:
            start_path = Path.cwd()
            sort_field = general.default_sort
            sort_ascending = general.default_sort_direction == "asc"
        return FileBrowserPanel(
            start_path=start_path,
            id=widget_id,
            show_hidden=self._show_hidden,
            sort_field=sort_field,
            sort_ascending=sort_ascending,
        )

    def on_mount(self) -> None:
        self.active_panel.activate()
        for panel in (self._left_panel, self._right_panel):
            mode = self._pending_view_modes.get(panel.id or "")
            if mode is not None:
                panel.set_view_mode(mode)
        self._pending_view_modes.clear()
        self._apply_panel_widths()

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
        self._schedule_save()

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
        self._schedule_save()

    def action_view_brief(self) -> None:
        self.active_panel.set_view_mode(ViewMode.BRIEF)
        self._schedule_save()

    def action_view_full(self) -> None:
        self.active_panel.set_view_mode(ViewMode.FULL)
        self._schedule_save()

    def action_view_wide(self) -> None:
        self.active_panel.set_view_mode(ViewMode.WIDE)
        self._schedule_save()

    def action_sort_name(self) -> None:
        self.active_panel.set_sort("name")
        self._schedule_save()

    def action_sort_ext(self) -> None:
        self.active_panel.set_sort("extension")
        self._schedule_save()

    def action_sort_mtime(self) -> None:
        self.active_panel.set_sort("date")
        self._schedule_save()

    def action_sort_size(self) -> None:
        self.active_panel.set_sort("size")
        self._schedule_save()

    def action_select_toggle(self) -> None:
        self.active_panel.toggle_selection_at_cursor()

    def action_select_mask(self) -> None:
        self._open_mask_dialog(select=True)

    def action_deselect_mask(self) -> None:
        self._open_mask_dialog(select=False)

    def action_select_invert(self) -> None:
        self.active_panel.invert_selection()

    def action_toggle_hidden(self) -> None:
        """Ctrl+H: global toggle — both panels update from a single keypress."""
        self._show_hidden = not self._show_hidden
        self._left_panel.set_show_hidden(self._show_hidden)
        self._right_panel.set_show_hidden(self._show_hidden)
        self._schedule_save()

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
        self._schedule_save()

    def action_resize_shrink(self) -> None:
        self._resize_index = max(self._resize_index - 1, 0)
        self._apply_panel_widths()
        self._schedule_save()

    def _apply_panel_widths(self) -> None:
        pct = _RESIZE_STEPS[self._resize_index]
        self.active_panel.styles.width = f"{pct}%"
        self.inactive_panel.styles.width = "1fr"

    def _schedule_save(self) -> None:
        if self._state_db is None:
            return
        if self._save_timer is not None:
            self._save_timer.stop()
        self._save_timer = self.set_timer(_SAVE_DEBOUNCE_SECONDS, self._flush_state)

    def _flush_state(self) -> None:
        if self._state_db is None:
            return
        self._save_timer = None
        try:
            for side, panel in (("left", self._left_panel), ("right", self._right_panel)):
                if panel is None:
                    continue
                self._state_db.save_panel_state(
                    side,
                    str(panel.current_path),
                    panel.sort_field,
                    panel.sort_ascending,
                    panel.view_mode.value,
                )
            self._state_db.save_app_state("show_hidden", "true" if self._show_hidden else "false")
            self._state_db.save_app_state("active_side", self._active_side)
            self._state_db.save_app_state("resize_index", str(self._resize_index))
        except Exception:
            # A save failure (locked DB, full disk, read-only FS, ...) must
            # never block quitting or crash into the panic screen — same
            # graceful-degradation posture as __init__'s StateDB() try/except.
            logger.warning("Failed to save state — continuing without it", exc_info=True)

    async def action_quit(self) -> None:
        if self._save_timer is not None:
            self._save_timer.stop()
            self._save_timer = None
        self._flush_state()
        await super().action_quit()


def main():
    app = MyComApp()
    app.run()


if __name__ == "__main__":
    main()
