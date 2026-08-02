"""Tests for dialog widgets."""

import pytest
from textual.app import ComposeResult
from textual.widgets import Static

from mycom.widgets.dialog import ConfirmDialog, InputDialog
from tests.support import ThemedApp


class DialogTestApp(ThemedApp):
    def compose(self) -> ComposeResult:
        yield Static("Dialog test host")


@pytest.mark.asyncio
async def test_confirm_dialog_yes():
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = None

        def on_dismiss(value: bool) -> None:
            nonlocal result
            result = value

        app.push_screen(ConfirmDialog("Delete file?"), callback=on_dismiss)
        await pilot.pause()
        await pilot.click("#yes")
        await pilot.pause()
        assert result is True


@pytest.mark.asyncio
async def test_confirm_dialog_no():
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = None

        def on_dismiss(value: bool) -> None:
            nonlocal result
            result = value

        app.push_screen(ConfirmDialog("Delete file?"), callback=on_dismiss)
        await pilot.pause()
        await pilot.click("#no")
        await pilot.pause()
        assert result is False


@pytest.mark.asyncio
async def test_confirm_dialog_escape():
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = None

        def on_dismiss(value: bool) -> None:
            nonlocal result
            result = value

        app.push_screen(ConfirmDialog("Delete file?"), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert result is False


@pytest.mark.asyncio
async def test_input_dialog_cancel():
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = "not_set"

        def on_dismiss(value: str | None) -> None:
            nonlocal result
            result = value

        app.push_screen(InputDialog("Enter name:"), callback=on_dismiss)
        await pilot.pause()
        await pilot.click("#cancel")
        await pilot.pause()
        assert result is None


@pytest.mark.asyncio
async def test_input_dialog_escape():
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = "not_set"

        def on_dismiss(value: str | None) -> None:
            nonlocal result
            result = value

        app.push_screen(InputDialog("Enter name:"), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert result is None
