"""Status bar (key bar) widget: 10 slots generated from the keymap registry."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static

from mycom.keymap import Keymap


class _KeyBarSlot(Static):
    """One clickable half (number or label) of a key-bar slot."""

    def __init__(self, text: str, action: str, **kwargs) -> None:
        super().__init__(text, **kwargs)
        self._action = action

    async def on_click(self, event) -> None:
        if self._action:
            await self.app.run_action(self._action)


class StatusBar(Widget):
    """Bottom bar: 10 labeled key-bar slots (F0.14).

    Generated from `Keymap.key_bar_slots(scope)` — labels can never drift
    from actual bindings, because they're read from the same registry that
    creates the binding. Unassigned slots render empty, not stale. Clicking
    a slot runs the same action its key would (`App.run_action`).
    """

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $keybar-number-bg;
    }
    StatusBar Horizontal {
        width: 1fr;
        height: 1;
        background: $keybar-number-bg;
    }
    StatusBar .hint-key {
        color: $keybar-number-fg;
        background: $keybar-number-bg;
        padding: 0 0;
    }
    StatusBar .hint-label {
        color: $keybar-label-fg;
        background: $keybar-label-bg;
        padding: 0 1;
    }
    """

    def __init__(self, keymap: Keymap | None = None, scope: str = "panel", **kwargs) -> None:
        # NOTE: the keymap-context parameter is named `scope`, not `context` —
        # a Widget.__init__ parameter whose name contains "context" hangs
        # Textual's mount machinery in this version (reproduced in isolation;
        # unrelated to any of this widget's own logic). Do not rename back.
        super().__init__(**kwargs)
        self._keymap = keymap
        self._scope = scope

    def compose(self) -> ComposeResult:
        with Horizontal():
            for slot, action, _key_label, action_label in self._slots():
                yield _KeyBarSlot(str(slot), action, classes="hint-key")
                yield _KeyBarSlot(action_label, action, classes="hint-label")

    def _slots(self) -> list[tuple[int, str, str, str]]:
        if self._keymap is None:
            return [(slot, "", "", "") for slot in range(1, 11)]
        return self._keymap.key_bar_slots(self._scope)

    @property
    def keymap(self) -> Keymap | None:
        return self._keymap

    @property
    def scope(self) -> str:
        return self._scope
