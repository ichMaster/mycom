"""Command and keymap registry: action -> key(s) -> context -> label.

The single source of truth for key bindings. Feeds Textual's runtime bindings
(`App.bind`) now, and will feed the key bar / F9 menus in later phases — so
labels can never drift from actual bindings.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    """One bindable action: its key(s), the context it applies in, and its label."""

    action: str
    keys: tuple[str, ...]
    context: str
    label: str


DEFAULT_COMMANDS: tuple[Command, ...] = (
    Command("help", ("f1",), "panel", "Help"),
    Command("view", ("f3",), "panel", "View"),
    Command("edit", ("f4",), "panel", "Edit"),
    Command("copy", ("f5",), "panel", "Copy"),
    Command("move", ("f6",), "panel", "RenMov"),
    Command("mkdir", ("f7",), "panel", "MkDir"),
    Command("delete", ("f8",), "panel", "Delete"),
    Command("quit", ("f10",), "panel", "Quit"),
    Command("switch_panel", ("tab",), "panel", "Switch"),
    Command("open", ("enter",), "panel", "Open"),
    Command("go_up", ("backspace",), "panel", "Up"),
    Command("first", ("home",), "panel", "First"),
    Command("last", ("end",), "panel", "Last"),
    Command("panel_swap", ("ctrl+u",), "panel", "Swap"),
    Command("resize_grow", ("ctrl+right",), "panel", "Grow"),
    Command("resize_shrink", ("ctrl+left",), "panel", "Shrink"),
    Command("view_brief", ("ctrl+1",), "panel", "Brief"),
    Command("view_full", ("ctrl+2",), "panel", "Full"),
    Command("view_wide", ("ctrl+3",), "panel", "Wide"),
    Command("sort_name", ("ctrl+f3",), "panel", "SortName"),
    Command("sort_ext", ("ctrl+f4",), "panel", "SortExt"),
    Command("sort_mtime", ("ctrl+f5",), "panel", "SortTime"),
    Command("sort_size", ("ctrl+f6",), "panel", "SortSize"),
)


class Keymap:
    """Resolves actions to key sequences, with config overrides, per context."""

    def __init__(
        self,
        overrides: dict[str, str] | None = None,
        commands: tuple[Command, ...] = DEFAULT_COMMANDS,
    ) -> None:
        self._commands: dict[str, Command] = {c.action: c for c in commands}
        if overrides:
            for action, key in overrides.items():
                cmd = self._commands.get(action)
                if cmd is not None:
                    self._commands[action] = Command(cmd.action, (key,), cmd.context, cmd.label)

    def resolve(self, action: str) -> str | None:
        """Return the primary key sequence bound to an action, if any."""
        cmd = self._commands.get(action)
        if cmd is None or not cmd.keys:
            return None
        return cmd.keys[0]

    def actions_for_key(self, key: str, context: str | None = None) -> list[str]:
        """Return every action bound to a key, optionally scoped to a context."""
        return [
            c.action
            for c in self._commands.values()
            if key in c.keys and (context is None or c.context == context)
        ]

    def bindings_for_context(self, context: str) -> list[tuple[str, str, str]]:
        """Return (key, action, label) triples for every key bound in a context."""
        result: list[tuple[str, str, str]] = []
        for c in self._commands.values():
            if c.context != context:
                continue
            for key in c.keys:
                result.append((key, c.action, c.label))
        return result

    def all(self) -> dict[str, str]:
        """Return a copy of the primary key for every bound action."""
        return {action: cmd.keys[0] for action, cmd in self._commands.items() if cmd.keys}
