"""TextArea-based editor screen (F0.13) — F4."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, TextArea

from mycom.editor.detect import EolStyle, apply_eol
from mycom.keymap import Keymap
from mycom.widgets.dialog import ErrorDialog, InputDialog, SaveDiscardCancelDialog
from mycom.widgets.status_bar import StatusBar

_EOL_LABELS = {
    EolStyle.LF: "LF",
    EolStyle.CRLF: "CRLF",
    EolStyle.MIXED_LF_DOMINANT: "LF*",
    EolStyle.MIXED_CRLF_DOMINANT: "CRLF*",
}


class EditorScreen(Screen[None]):
    """`F4`: a `TextArea`-based editor. The contract is *trust*: EOL and
    trailing-newline preserved byte-for-byte on save, a modified-guard
    (Save/Discard/Cancel) before ever closing a dirty buffer. Undo/redo is
    `TextArea`'s own built-in stack (`Ctrl+Z`/`Ctrl+Y`) — nothing extra to
    wire. Binary/oversize detection and the external-change guard live in
    the caller (`MyComApp`) and in MC-040 respectively; this screen assumes
    it was only ever constructed with text `read_text` already accepted.
    """

    DEFAULT_CSS = """
    EditorScreen {
        background: $panel-bg;
    }
    EditorScreen > #editor-info {
        dock: top;
        height: 1;
        background: $pathbar-active-bg;
        color: $pathbar-active-fg;
        padding: 0 1;
    }
    EditorScreen > TextArea {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(
        self,
        path: Path,
        keymap: Keymap,
        text: str,
        eol: EolStyle,
        trailing_newline: bool,
    ) -> None:
        super().__init__()
        self._path = path
        self._keymap = keymap
        self._eol = eol
        self._trailing_newline = trailing_newline
        self._saved_text = text
        # tab_behavior="focus" (the TextArea default) is required for F2/
        # Shift+F2/F10/Esc to bubble up to this screen's on_key at all — the
        # "indent" variant's own _on_key special-cases Escape to move focus
        # instead of letting it bubble.
        self._text_area = TextArea(text, tab_behavior="focus")
        self._info = Static(id="editor-info")

    def compose(self) -> ComposeResult:
        yield self._info
        yield self._text_area
        yield StatusBar(keymap=self._keymap, scope="editor")

    def on_mount(self) -> None:
        self._text_area.focus()
        self._update_info()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self._update_info()

    @property
    def modified(self) -> bool:
        return self._text_area.text != self._saved_text

    @property
    def path(self) -> Path:
        return self._path

    def _update_info(self) -> None:
        row, col = self._text_area.cursor_location
        marker = "*" if self.modified else ""
        eol_label = _EOL_LABELS[self._eol]
        self._info.update(f"{self._path.name}{marker}  {row + 1}:{col + 1}  {eol_label}")

    def on_key(self, event) -> None:
        actions = self._keymap.actions_for_key(event.key, context="editor")
        if not actions:
            return
        event.stop()
        event.prevent_default()
        {
            "editor_save": self.save,
            "editor_save_as": self.save_as,
            "editor_close": self.request_close,
        }[actions[0]]()

    def _serialize(self) -> str:
        text = self._text_area.text
        if self._trailing_newline and not text.endswith("\n"):
            text += "\n"
        elif not self._trailing_newline and text.endswith("\n"):
            text = text[:-1]
        return apply_eol(text, self._eol)

    def _write(self, path: Path) -> bool:
        try:
            path.write_text(self._serialize(), encoding="utf-8")
        except OSError as exc:
            self.app.push_screen(ErrorDialog(f"Cannot save: {exc}"))
            return False
        self._saved_text = self._text_area.text
        self._update_info()
        return True

    def save(self) -> None:
        self._write(self._path)

    def save_as(self) -> None:
        def on_dismiss(new_path_text: str | None) -> None:
            if not new_path_text:
                return
            new_path = Path(new_path_text)
            if self._write(new_path):
                self._path = new_path
                self._update_info()

        self.app.push_screen(
            InputDialog("Save as:", default=str(self._path)),
            callback=on_dismiss,
        )

    def request_close(self) -> None:
        if not self.modified:
            self.dismiss(None)
            return

        def on_choice(choice: str) -> None:
            if choice == "save":
                if self._write(self._path):
                    self.dismiss(None)
                # A failed write already showed an error — stay open so
                # nothing typed is lost.
            elif choice == "discard":
                self.dismiss(None)
            # "cancel" (or Esc): stay in the editor, buffer untouched.

        self.app.push_screen(
            SaveDiscardCancelDialog(f'Save changes to "{self._path.name}"?'),
            callback=on_choice,
        )
