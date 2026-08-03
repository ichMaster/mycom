"""TextArea-based editor screen (F0.13) — F4."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, TextArea

from mycom.editor.detect import EolStyle, apply_eol
from mycom.keymap import Keymap
from mycom.widgets.dialog import ConfirmDialog, ErrorDialog, InputDialog, SaveDiscardCancelDialog
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
    (Save/Discard/Cancel) before ever closing a dirty buffer, and an
    external-change guard before ever overwriting a file that was touched on
    disk since it was opened. Undo/redo is `TextArea`'s own built-in stack
    (`Ctrl+Z`/`Ctrl+Y`) — nothing extra to wire. Binary/oversize detection
    lives in the caller (`MyComApp`); this screen assumes it was only ever
    constructed with text `read_text` already accepted.
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
        self._mtime_at_open = self._safe_mtime(path)
        # tab_behavior="focus" (the TextArea default) is required for F2/
        # Shift+F2/F10/Esc to bubble up to this screen's on_key at all — the
        # "indent" variant's own _on_key special-cases Escape to move focus
        # instead of letting it bubble.
        self._text_area = TextArea(text, tab_behavior="focus")
        self._info = Static(id="editor-info")

    @staticmethod
    def _safe_mtime(path: Path) -> float | None:
        try:
            return path.stat().st_mtime
        except OSError:
            return None

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
        self._mtime_at_open = self._safe_mtime(path)
        self._update_info()
        return True

    def _external_change_detected(self) -> bool:
        current = self._safe_mtime(self._path)
        return (
            self._mtime_at_open is not None
            and current is not None
            and current != self._mtime_at_open
        )

    def _save_with_guard(self, on_done: Callable[[bool], None]) -> None:
        """Writes to `self._path`, warning first if the file was touched on
        disk since it was opened — never a silent last-writer-wins. `on_done`
        is called with whether the write actually happened (declining the
        warning, or a write failure, both leave the in-memory buffer
        untouched — nothing is ever lost either way)."""
        if self._external_change_detected():

            def on_confirm(confirmed: bool) -> None:
                on_done(self._write(self._path) if confirmed else False)

            self.app.push_screen(
                ConfirmDialog(
                    f'"{self._path.name}" changed on disk since you opened it. '
                    "Overwrite anyway?"
                ),
                callback=on_confirm,
            )
            return
        on_done(self._write(self._path))

    def save(self) -> None:
        self._save_with_guard(lambda _success: None)

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
                # A failed write (or a declined external-change warning)
                # already showed the reason — stay open so nothing typed is
                # lost.
                self._save_with_guard(lambda success: self.dismiss(None) if success else None)
            elif choice == "discard":
                self.dismiss(None)
            # "cancel" (or Esc): stay in the editor, buffer untouched.

        self.app.push_screen(
            SaveDiscardCancelDialog(f'Save changes to "{self._path.name}"?'),
            callback=on_choice,
        )
