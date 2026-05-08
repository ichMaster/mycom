"""Key binding registry mapping action names to Textual key identifiers."""

from __future__ import annotations

DEFAULTS: dict[str, str] = {
    "help": "f1",
    "view": "f3",
    "edit": "f4",
    "copy": "f5",
    "move": "f6",
    "mkdir": "f7",
    "delete": "f8",
    "quit": "f10",
    "switch_panel": "tab",
    "open": "enter",
    "go_up": "backspace",
    "first": "home",
    "last": "end",
    "terminal_toggle": "ctrl+t",
    "llm_toggle": "ctrl+l",
}


class KeyBindings:
    """Resolves action names to key sequences, with config overrides."""

    def __init__(self, overrides: dict[str, str] | None = None) -> None:
        self._bindings = dict(DEFAULTS)
        if overrides:
            for action, key in overrides.items():
                if action in self._bindings:
                    self._bindings[action] = key

    def get(self, action: str) -> str | None:
        """Return the key sequence for a given action name."""
        return self._bindings.get(action)

    def all(self) -> dict[str, str]:
        """Return a copy of all current bindings."""
        return dict(self._bindings)

    def actions_for_key(self, key: str) -> list[str]:
        """Return all actions bound to a given key."""
        return [a for a, k in self._bindings.items() if k == key]
