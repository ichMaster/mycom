"""Modal dialog widgets for user interaction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ProgressBar

from mycom.fileops.engine import CancelToken, OpProgress
from mycom.utils.fs import format_size

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
        self._check_no_duplicate_hotkeys()

    def _check_no_duplicate_hotkeys(self) -> None:
        seen: set[str] = set()
        for button in self._buttons:
            if not button.hotkey:
                continue
            letter = button.hotkey.lower()
            if letter in seen:
                raise ValueError(
                    f"duplicate DialogButton hotkey {button.hotkey!r} in {type(self).__name__}"
                )
            seen.add(letter)

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

    def _on_escape(self) -> None:
        """Esc behavior — override to customize (default: dismiss with cancel_result).

        Subclasses must override this rather than `on_key` itself: Textual
        dispatches a `Key` message to every class in the MRO that defines
        `on_key`/`_on_key`, not just the most-derived one, so a subclass
        `on_key` calling `super().on_key(event)` runs DialogKit's handling
        TWICE (once explicitly, once via Textual's own independent dispatch),
        double-dismissing the screen. Plain method overrides like this one
        aren't subject to that — normal single-dispatch MRO applies.
        """
        self.dismiss(self._cancel_result)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id is not None:
            self._activate(event.button.id)

    def _cycle_button_focus(self, forward: bool) -> None:
        """Move focus among Button widgets only.

        Textual's generic focus_next()/focus_previous() walk every focusable
        widget, including an Input — once arrow navigation lands there, the
        Input's own key handling claims Left/Right for the text cursor and
        arrows can never move focus away from it again (code review #1).
        """
        buttons = [b for b in self.query(Button) if b.display]
        if not buttons:
            return
        if self.focused in buttons:
            index = (buttons.index(self.focused) + (1 if forward else -1)) % len(buttons)
        else:
            index = 0
        buttons[index].focus()

    def on_key(self, event) -> None:
        # Stop every key this dialog handles from bubbling past it — without
        # this, a modal's Enter/Esc/hotkeys also reach MyComApp.on_key and
        # trigger the panel underneath (e.g. Enter dismissing a dialog would
        # also "open" whatever the panel's cursor was on, clearing state the
        # dialog's own callback had just set).
        input_focused = isinstance(self.focused, Input)

        if event.key == "enter":
            event.stop()
            default = next((b for b in self._buttons if b.default), None)
            if default is None and self._buttons:
                default = self._buttons[-1]
            if default is not None:
                self._activate(default.id)
            return

        if event.key == "escape":
            event.stop()
            self._on_escape()
            return

        if not input_focused:
            if event.key in ("left", "up"):
                event.stop()
                self._cycle_button_focus(forward=False)
                return
            if event.key in ("right", "down"):
                event.stop()
                self._cycle_button_focus(forward=True)
                return

        for button in self._buttons:
            if not button.hotkey:
                continue
            letter = button.hotkey.lower()
            if event.key == f"alt+{letter}" or (event.key == letter and not input_focused):
                event.stop()
                self._activate(button.id)
                return


class ConfirmDialog(DialogKit[bool]):
    """Modal Yes/No confirmation dialog, built on DialogKit."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(
            message=message,
            buttons=(
                DialogButton("Yes", "yes", hotkey="y", default=True, variant="primary"),
                DialogButton("No", "no", hotkey="n"),
            ),
            cancel_result=False,
            **kwargs,
        )

    def _result_for(self, button_id: str) -> bool:
        return button_id == "yes"


class InputDialog(DialogKit[str | None]):
    """Modal text input dialog, built on DialogKit."""

    def __init__(self, prompt: str, default: str = "", **kwargs) -> None:
        super().__init__(
            message=prompt,
            buttons=(
                DialogButton("OK", "ok", hotkey="o", default=True, variant="primary"),
                DialogButton("Cancel", "cancel", hotkey="c"),
            ),
            cancel_result=None,
            **kwargs,
        )
        self._default = default

    def compose_body(self) -> ComposeResult:
        yield Input(value=self._default, id="input")

    def _result_for(self, button_id: str) -> str | None:
        if button_id == "ok":
            return self.query_one("#input", Input).value
        return None


class ErrorDialog(DialogKit[None]):
    """Modal error message with a single OK button, built on DialogKit."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(
            message=message,
            buttons=(DialogButton("OK", "ok", hotkey="o", default=True, variant="primary"),),
            cancel_result=None,
            **kwargs,
        )

    def _result_for(self, button_id: str) -> None:
        return None


class ProgressDialog(DialogKit[None]):
    """Modal progress indicator, built on DialogKit. No buttons — a Cancel
    affordance belongs to the operation engine (v0.4), not invented here."""

    def __init__(self, message: str = "Working...", total: float = 100, **kwargs) -> None:
        super().__init__(message=message, buttons=(), cancel_result=None, **kwargs)
        self._total = total

    def compose_body(self) -> ComposeResult:
        yield ProgressBar(total=self._total, id="progress")

    def update_progress(self, value: float) -> None:
        bar = self.query_one("#progress", ProgressBar)
        bar.update(progress=value)

    def _on_escape(self) -> None:
        # No cancel affordance — dismissing would misleadingly suggest a
        # running operation stopped. See OperationProgressDialog for the real
        # Cancel-button affordance used by copy/move/delete (v0.4).
        pass


class OperationProgressDialog(DialogKit[None]):
    """Progress display for copy/move/delete: current file, a total-bytes
    progress bar, files-done count, speed, ETA, and a Cancel button.

    Progress is reported per plan entry (not per chunk within a file — see
    mycom.fileops.engine), so this shows one real bar (total bytes across the
    whole operation) rather than a separate per-file percentage a single
    large file's entry couldn't fill smoothly anyway.

    Cancel only signals the CancelToken — it does not dismiss the dialog.
    Chunk-boundary cancellation isn't instant, so the driving worker is the
    one that dismisses this once execute_plan actually returns. Esc is a
    deliberate no-op for the same reason as ProgressDialog's.
    """

    def __init__(
        self, cancel_token: CancelToken, *, title: str = "", total_bytes: int = 0, **kwargs
    ) -> None:
        super().__init__(
            title=title,
            buttons=(DialogButton("Cancel", "cancel", hotkey="c", default=True),),
            cancel_result=None,
            **kwargs,
        )
        self._cancel_token = cancel_token
        self._total_bytes = max(total_bytes, 1)

    def compose_body(self) -> ComposeResult:
        yield Label("", id="current-file")
        yield ProgressBar(total=self._total_bytes, id="total-progress", show_eta=False)
        yield Label("", id="stats")

    def update_progress(self, progress: OpProgress) -> None:
        self.query_one("#current-file", Label).update(progress.current_file)
        self.query_one("#total-progress", ProgressBar).update(progress=progress.bytes_done)
        speed = f"{format_size(int(progress.speed_bps))}/s"
        eta = f"{int(progress.eta_seconds)}s" if progress.eta_seconds is not None else "--"
        self.query_one("#stats", Label).update(
            f"{format_size(progress.bytes_done)} / {format_size(progress.bytes_total)}"
            f"   file {progress.files_done}/{progress.files_total}   {speed}   ETA {eta}"
        )

    def _result_for(self, button_id: str) -> None:
        return None

    def _activate(self, button_id: str) -> None:
        # Cancel signals the token but doesn't dismiss — see class docstring.
        self._cancel_token.cancel()
