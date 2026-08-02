"""Pilot tests for ConflictDialog (F0.10): the six choices, driven via keyboard."""

from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import ComposeResult
from textual.widgets import Static

from mycom.fileops.policy import ConflictChoice
from mycom.widgets.conflict_dialog import ConflictDialog
from tests.support import ThemedApp


class ConflictDialogTestApp(ThemedApp):
    def compose(self) -> ComposeResult:
        yield Static("Conflict dialog test host")


def _dialog(dest_dir: Path = Path("/tmp/dest")) -> ConflictDialog:
    return ConflictDialog(
        dest_dir=dest_dir,
        name="a.txt",
        new_size=100,
        new_mtime=2000.0,
        existing_size=50,
        existing_mtime=1000.0,
    )


async def _open(pilot, app, dialog=None):
    dialog = dialog or _dialog()
    result = {}

    def on_dismiss(value):
        result["value"] = value

    app.push_screen(dialog, callback=on_dismiss)
    await pilot.pause()
    return result


@pytest.mark.asyncio
async def test_overwrite_choice():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app)
        await pilot.click("#overwrite")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.OVERWRITE, None)


@pytest.mark.asyncio
async def test_skip_choice():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app)
        await pilot.click("#skip")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.SKIP, None)


@pytest.mark.asyncio
async def test_overwrite_all_choice():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app)
        await pilot.click("#overwrite_all")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.OVERWRITE_ALL, None)


@pytest.mark.asyncio
async def test_skip_all_choice():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app)
        await pilot.click("#skip_all")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.SKIP_ALL, None)


@pytest.mark.asyncio
async def test_cancel_choice():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app)
        await pilot.click("#cancel")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.CANCEL, None)


@pytest.mark.asyncio
async def test_escape_cancels():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app)
        await pilot.press("escape")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.CANCEL, None)


@pytest.mark.asyncio
async def test_rename_choice_prefills_and_dismisses_with_new_path():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app, _dialog(Path("/tmp/dest")))
        await pilot.click("#rename")
        await pilot.pause()

        input_widget = app.screen.query_one("#rename-input")
        assert input_widget.value == "a.txt"
        assert input_widget.display is True

        input_widget.value = "a(2).txt"
        await pilot.click("#rename_ok")
        await pilot.pause()

        assert result["value"] == (ConflictChoice.RENAME, Path("/tmp/dest/a(2).txt"))


@pytest.mark.asyncio
async def test_rename_cancel_returns_to_six_choices():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app)
        await pilot.click("#rename")
        await pilot.pause()
        await pilot.click("#rename_cancel")
        await pilot.pause()

        assert app.screen.query_one("#rename-input").display is False
        await pilot.click("#overwrite")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.OVERWRITE, None)


@pytest.mark.asyncio
async def test_rename_enter_submits():
    app = ConflictDialogTestApp()
    async with app.run_test(size=(120, 40)) as pilot:
        result = await _open(pilot, app, _dialog(Path("/tmp/dest")))
        await pilot.click("#rename")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert result["value"] == (ConflictChoice.RENAME, Path("/tmp/dest/a.txt"))


def test_duplicate_hotkeys_rejected():
    """Six distinct hotkeys — DialogKit's guard (v0.2) would raise on a collision."""
    _dialog()  # construction alone exercises the guard; no exception means all distinct
