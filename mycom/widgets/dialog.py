"""Modal dialog widgets for user interaction."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ProgressBar


class ConfirmDialog(ModalScreen[bool]):
    """Modal Yes/No confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }
    ConfirmDialog > Vertical {
        width: 50;
        height: auto;
        border: thick $dialog-fg;
        background: $dialog-bg;
        color: $dialog-fg;
        padding: 1 2;
    }
    ConfirmDialog Label {
        width: 1fr;
        text-align: center;
        margin: 1 0;
        color: $dialog-fg;
    }
    ConfirmDialog Horizontal {
        width: 1fr;
        height: auto;
        align: center middle;
    }
    ConfirmDialog Button {
        margin: 0 2;
        background: $dialog-bg;
        color: $dialog-fg;
    }
    """

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._message)
            with Horizontal():
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", variant="default", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def key_escape(self) -> None:
        self.dismiss(False)

    def key_enter(self) -> None:
        self.dismiss(True)


class InputDialog(ModalScreen[str | None]):
    """Modal text input dialog."""

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }
    InputDialog > Vertical {
        width: 60;
        height: auto;
        border: thick $dialog-fg;
        background: $dialog-bg;
        color: $dialog-fg;
        padding: 1 2;
    }
    InputDialog Label {
        margin: 1 0;
        color: $dialog-fg;
    }
    InputDialog Input {
        margin: 1 0;
        background: $dialog-input-bg;
        color: $dialog-input-fg;
    }
    InputDialog Horizontal {
        width: 1fr;
        height: auto;
        align: center middle;
    }
    InputDialog Button {
        margin: 0 2;
        background: $dialog-bg;
        color: $dialog-fg;
    }
    """

    def __init__(self, prompt: str, default: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._prompt = prompt
        self._default = default

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._prompt)
            yield Input(value=self._default, id="input")
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            input_widget = self.query_one("#input", Input)
            self.dismiss(input_widget.value)
        else:
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)


class ErrorDialog(ModalScreen[None]):
    """Modal error message with a single OK button.

    Ad-hoc for v0.1 (same ModalScreen pattern as ConfirmDialog); rebuilt on
    the dialog kit in v0.2 along with the others.
    """

    DEFAULT_CSS = """
    ErrorDialog {
        align: center middle;
    }
    ErrorDialog > Vertical {
        width: 60;
        height: auto;
        border: thick $dialog-fg;
        background: $dialog-bg;
        color: $dialog-fg;
        padding: 1 2;
    }
    ErrorDialog Label {
        width: 1fr;
        text-align: center;
        margin: 1 0;
        color: $dialog-fg;
    }
    ErrorDialog Horizontal {
        width: 1fr;
        height: auto;
        align: center middle;
    }
    ErrorDialog Button {
        margin: 0 2;
        background: $dialog-bg;
        color: $dialog-fg;
    }
    """

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._message)
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)

    def key_enter(self) -> None:
        self.dismiss(None)


class ProgressDialog(ModalScreen[None]):
    """Modal progress indicator dialog."""

    DEFAULT_CSS = """
    ProgressDialog {
        align: center middle;
    }
    ProgressDialog > Vertical {
        width: 50;
        height: auto;
        border: thick $dialog-fg;
        background: $dialog-bg;
        color: $dialog-fg;
        padding: 1 2;
    }
    ProgressDialog Label {
        width: 1fr;
        text-align: center;
        margin: 1 0;
        color: $dialog-fg;
    }
    ProgressDialog ProgressBar {
        margin: 1 0;
    }
    """

    def __init__(self, message: str = "Working...", total: float = 100, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message
        self._total = total

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._message)
            yield ProgressBar(total=self._total, id="progress")

    def update_progress(self, value: float) -> None:
        bar = self.query_one("#progress", ProgressBar)
        bar.update(progress=value)
