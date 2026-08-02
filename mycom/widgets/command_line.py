"""Command-line prompt under the panels: always shows the active panel's
directory (cd-sync); printable typing routes here; Enter submits."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, Label


class CommandLine(Horizontal):
    """FAR-style prompt: `{cwd} $ ` followed by an `Input`. Submission is a
    message (`CommandLine.Submitted`) — the app decides whether it's a `cd`
    (applied directly, no subprocess) or real execution (v0.5's later
    issues)."""

    DEFAULT_CSS = """
    CommandLine {
        height: 1;
        background: $panel-bg;
        color: $panel-fg;
    }
    CommandLine > #command-prompt {
        width: auto;
        padding: 0 0 0 1;
    }
    CommandLine > #command-input {
        border: none;
        background: $panel-bg;
        color: $panel-fg;
        padding: 0 1 0 0;
        height: 1;
    }
    """

    class Submitted(Message):
        """Posted when the user presses Enter with text in the command line."""

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def __init__(self, cwd: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cwd = cwd

    def compose(self) -> ComposeResult:
        yield Label(self._prompt_text(), id="command-prompt")
        # select_on_focus=False: this Input gains focus mid-keystroke (the
        # first character of a command focuses it, via MyComApp.on_key) —
        # the default select-all-on-focus races that same-tick insertion
        # (focus is a queued message, processed after on_key's synchronous
        # insert_text_at_cursor call returns), so the *next* keystroke was
        # replacing the first character instead of appending after it.
        yield Input(id="command-input", select_on_focus=False)

    def _prompt_text(self) -> str:
        return f"{self._cwd} $ "

    def set_cwd(self, cwd: Path) -> None:
        """cd-sync: the prompt always mirrors the active panel's directory."""
        self._cwd = cwd
        self.query_one("#command-prompt", Label).update(self._prompt_text())

    @property
    def input(self) -> Input:
        return self.query_one("#command-input", Input)

    def focus_input(self) -> None:
        self.input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        text = event.value
        self.input.value = ""
        if text.strip():
            self.post_message(self.Submitted(text))

    def key_escape(self) -> None:
        self.input.value = ""
        panel = getattr(self.app, "active_panel", None)
        if panel is not None:
            panel.file_list.focus()
