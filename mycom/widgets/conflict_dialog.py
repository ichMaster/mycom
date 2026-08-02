"""Six-choice conflict resolution dialog (F0.10) and its ConflictPolicy adapter.

Raised by the fileops engine when a copy/move/rename target already exists.
Directory-over-directory merges and file/directory type mismatches are
handled by the engine itself (mycom.fileops.engine) before a conflict ever
reaches this dialog — it only ever resolves file-vs-file (or symlink)
collisions.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Input

from mycom.fileops.plan import PlanEntry
from mycom.fileops.policy import ConflictAnswer, ConflictChoice
from mycom.utils.fs import format_date, format_size
from mycom.widgets.dialog import DialogButton, DialogKit


class ConflictDialog(DialogKit[tuple[ConflictChoice, Path | None]]):
    """Shown for one file-vs-file conflict: both files' size/mtime, the newer
    one flagged, and six choices. `Rename` doesn't dismiss immediately — it
    swaps in an Input pre-filled with the conflicting name, with its own
    OK/Cancel pair, then dismisses with `(RENAME, new_path)`.
    """

    DEFAULT_CSS = (
        DialogKit.DEFAULT_CSS
        + """
    ConflictDialog .dialog-buttons Button {
        margin: 0 1;
        min-width: 0;
    }
    ConflictDialog #rename-input {
        display: none;
        margin: 1 0;
    }
    ConflictDialog #rename-row {
        width: 1fr;
        height: auto;
        align: center middle;
        display: none;
    }
    """
    )

    def __init__(
        self,
        *,
        dest_dir: Path,
        name: str,
        new_size: int,
        new_mtime: float,
        existing_size: int,
        existing_mtime: float,
        **kwargs,
    ) -> None:
        new_is_newer = new_mtime > existing_mtime
        new_mark = "> " if new_is_newer else "  "
        existing_mark = "> " if not new_is_newer else "  "
        message = (
            f'"{name}" already exists.\n\n'
            f"{new_mark}new:      {format_size(new_size)}   {format_date(new_mtime)}\n"
            f"{existing_mark}existing: {format_size(existing_size)}   {format_date(existing_mtime)}"
        )
        super().__init__(
            title="File exists",
            message=message,
            buttons=(
                DialogButton("Overwrite", "overwrite", hotkey="o", default=True, variant="primary"),
                DialogButton("Skip", "skip", hotkey="s"),
                DialogButton("Rename", "rename", hotkey="r"),
                DialogButton("Overwrite All", "overwrite_all", hotkey="w"),
                DialogButton("Skip All", "skip_all", hotkey="k"),
                DialogButton("Cancel", "cancel", hotkey="c"),
            ),
            cancel_result=(ConflictChoice.CANCEL, None),
            **kwargs,
        )
        self._dest_dir = dest_dir
        self._name = name
        self._renaming = False
        self._main_buttons = self._buttons
        self._rename_buttons = (
            DialogButton("OK", "rename_ok", default=True, variant="primary"),
            DialogButton("Cancel", "rename_cancel"),
        )

    def compose_body(self) -> ComposeResult:
        yield Input(value=self._name, id="rename-input")
        with Horizontal(id="rename-row"):
            yield Button("[underline]O[/underline]K", id="rename_ok", variant="primary")
            yield Button("[underline]C[/underline]ancel", id="rename_cancel")

    def on_mount(self) -> None:
        # The (CSS-hidden) rename Input still sits earlier in the DOM than
        # the button row, and Textual's initial auto-focus doesn't skip it
        # just because it's display:none — focus the default button explicitly.
        default_button = next((b for b in self._buttons if b.default), None) or (
            self._buttons[-1] if self._buttons else None
        )
        if default_button is not None:
            self.query_one(f"#{default_button.id}", Button).focus()

    def _result_for(self, button_id: str) -> tuple[ConflictChoice, Path | None]:
        mapping = {
            "overwrite": ConflictChoice.OVERWRITE,
            "skip": ConflictChoice.SKIP,
            "overwrite_all": ConflictChoice.OVERWRITE_ALL,
            "skip_all": ConflictChoice.SKIP_ALL,
            "cancel": ConflictChoice.CANCEL,
        }
        return mapping[button_id], None

    def _activate(self, button_id: str) -> None:
        if button_id == "rename":
            self._enter_rename_mode()
            return
        if button_id == "rename_ok":
            new_name = self.query_one("#rename-input", Input).value
            self.dismiss((ConflictChoice.RENAME, self._dest_dir / new_name))
            return
        if button_id == "rename_cancel":
            self._exit_rename_mode()
            return
        super()._activate(button_id)

    def _enter_rename_mode(self) -> None:
        self._renaming = True
        self._buttons = self._rename_buttons
        self.query_one(".dialog-buttons", Horizontal).display = False
        self.query_one("#rename-input", Input).display = True
        self.query_one("#rename-row", Horizontal).display = True
        self.query_one("#rename-input", Input).focus()

    def _exit_rename_mode(self) -> None:
        self._renaming = False
        self._buttons = self._main_buttons
        self.query_one("#rename-input", Input).display = False
        self.query_one("#rename-row", Horizontal).display = False
        self.query_one(".dialog-buttons", Horizontal).display = True

    def _on_escape(self) -> None:
        # Esc during rename backs out to the six-choice view instead of
        # dismissing the whole dialog (DialogKit's default) — see
        # DialogKit._on_escape for why this must be a plain method override,
        # not a second on_key.
        if self._renaming:
            self._exit_rename_mode()
        else:
            super()._on_escape()


class ConflictDialogPolicy:
    """`ConflictPolicy` adapter: shows `ConflictDialog` on the app's UI thread
    and blocks the calling worker thread for the answer.

    "All" persistence lives in `mycom.fileops.engine._resolve_conflict` (one
    `execute_plan` call remembers OVERWRITE_ALL/SKIP_ALL and stops asking) —
    this adapter is a stateless one-question-at-a-time translator, so a fresh
    instance per operation naturally can't leak an "All" answer into a later,
    separate operation.
    """

    def __init__(self, app: App, dest_dir: Path) -> None:
        self._app = app
        self._dest_dir = dest_dir

    def __call__(self, entry: PlanEntry, dst_stat: os.stat_result) -> ConflictAnswer:
        return self._app.call_from_thread(self._ask, entry, dst_stat)

    async def _ask(self, entry: PlanEntry, dst_stat: os.stat_result) -> ConflictAnswer:
        src_stat = entry.src.stat()
        dialog = ConflictDialog(
            dest_dir=self._dest_dir,
            name=entry.dst.name,
            new_size=src_stat.st_size,
            new_mtime=src_stat.st_mtime,
            existing_size=dst_stat.st_size,
            existing_mtime=dst_stat.st_mtime,
        )
        # push_screen_wait() requires an active Textual *worker* context, which
        # this coroutine doesn't have (it's scheduled by call_from_thread from
        # a plain background thread, not App.run_worker) — push_screen() plus
        # a manually-resolved future gives the same "wait for the dismiss
        # value" behavior without that requirement.
        future: asyncio.Future[ConflictAnswer] = asyncio.get_running_loop().create_future()

        def on_dismiss(result: ConflictAnswer) -> None:
            if not future.done():
                future.set_result(result)

        self._app.push_screen(dialog, callback=on_dismiss)
        return await future
