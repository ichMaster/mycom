"""Modal dialog widgets for user interaction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ProgressBar

DialogResult = TypeVar("DialogResult")


@dataclass(frozen=True)
class DialogButton:
    """One button in a DialogKit's button row."""

    label: str
    id: str
    hotkey: str | None = None
    default: bool = False
    variant: str = "default"


class DialogKit(ModalScreen[DialogResult], Generic[DialogResult]):
    """The one reusable modal engine every dialog is built on (F0.15).

    Framed window: title, message, subclass-supplied body widgets
    (`compose_body`), and a button row. `Tab`/`Shift+Tab` cycle focus via
    Textual's default focus chain; `Left`/`Up`/`Right`/`Down` additionally
    cycle focus between buttons when an `Input` isn't focused (arrows edit
    text there instead). A button's hotkey letter (underlined in its label)
    activates it on a bare keypress when no `Input` is focused, or on
    `Alt+letter` unconditionally. `Enter` activates the default button;
    `Esc` dismisses with `cancel_result`. Dialogs stack — this is Textual's
    native `ModalScreen` behavior; the kit doesn't interfere with it.
    """

    DEFAULT_CSS = """
    DialogKit {
        align: center middle;
    }
    DialogKit > Vertical {
        width: auto;
        min-width: 40;
        height: auto;
        border: thick $dialog-fg;
        background: $dialog-bg;
        color: $dialog-fg;
        padding: 1 2;
    }
    DialogKit .dialog-title {
        text-style: bold;
        width: 1fr;
        text-align: center;
    }
    DialogKit .dialog-message {
        width: 1fr;
        text-align: center;
        margin: 1 0;
    }
    DialogKit .dialog-buttons {
        width: 1fr;
        height: auto;
        align: center middle;
    }
    DialogKit Button {
        margin: 0 2;
        background: $dialog-bg;
        color: $dialog-fg;
    }
    """

    def __init__(
        self,
        *,
        title: str = "",
        message: str = "",
        buttons: tuple[DialogButton, ...] = (),
        cancel_result: DialogResult | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._message = message
        self._buttons = buttons
        self._cancel_result = cancel_result

    def compose(self) -> ComposeResult:
        with Vertical():
            if self._title:
                yield Label(self._title, classes="dialog-title")
            if self._message:
                yield Label(self._message, classes="dialog-message")
            yield from self.compose_body()
            with Horizontal(classes="dialog-buttons"):
                for button in self._buttons:
                    yield Button(self._button_label(button), id=button.id, variant=button.variant)

    def compose_body(self) -> ComposeResult:
        """Override to yield extra widgets between the message and the buttons."""
        yield from ()

    def _button_label(self, button: DialogButton) -> str:
        if not button.hotkey:
            return button.label
        idx = button.label.lower().find(button.hotkey.lower())
        if idx == -1:
            return button.label
        before, letter, after = button.label[:idx], button.label[idx], button.label[idx + 1 :]
        return f"{before}[underline]{letter}[/underline]{after}"

    def _result_for(self, button_id: str) -> DialogResult:
        """Map a pressed/activated button id to the dismiss value. Override in subclasses."""
        raise NotImplementedError

    def _activate(self, button_id: str) -> None:
        self.dismiss(self._result_for(button_id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id is not None:
            self._activate(event.button.id)

    def on_key(self, event) -> None:
        input_focused = isinstance(self.focused, Input)

        if not input_focused:
            if event.key in ("left", "up"):
                event.stop()
                self.focus_previous()
                return
            if event.key in ("right", "down"):
                event.stop()
                self.focus_next()
                return

        for button in self._buttons:
            if not button.hotkey:
                continue
            letter = button.hotkey.lower()
            if event.key == f"alt+{letter}" or (event.key == letter and not input_focused):
                event.stop()
                self._activate(button.id)
                return

    def key_enter(self) -> None:
        default = next((b for b in self._buttons if b.default), None)
        if default is None and self._buttons:
            default = self._buttons[-1]
        if default is not None:
            self._activate(default.id)

    def key_escape(self) -> None:
        self.dismiss(self._cancel_result)


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
