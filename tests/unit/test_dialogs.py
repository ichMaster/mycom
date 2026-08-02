"""Tests for dialog widgets."""

import pytest
from textual.app import ComposeResult
from textual.widgets import Static

from mycom.widgets.dialog import ConfirmDialog, DialogKit, ErrorDialog, InputDialog, ProgressDialog
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


def test_all_four_dialogs_are_dialog_kit_subclasses():
    assert issubclass(ConfirmDialog, DialogKit)
    assert issubclass(InputDialog, DialogKit)
    assert issubclass(ErrorDialog, DialogKit)
    assert issubclass(ProgressDialog, DialogKit)


def test_no_dialog_defines_its_own_default_css():
    """Audit: zero ad-hoc modal code remains outside DialogKit itself."""
    for cls in (ConfirmDialog, InputDialog, ErrorDialog, ProgressDialog):
        assert "DEFAULT_CSS" not in cls.__dict__


@pytest.mark.asyncio
async def test_confirm_dialog_bare_hotkeys():
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = None

        def on_dismiss(value: bool) -> None:
            nonlocal result
            result = value

        app.push_screen(ConfirmDialog("Delete file?"), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        assert result is False


@pytest.mark.asyncio
async def test_confirm_dialog_alt_hotkey():
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = None

        def on_dismiss(value: bool) -> None:
            nonlocal result
            result = value

        app.push_screen(ConfirmDialog("Delete file?"), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("alt+y")
        await pilot.pause()
        assert result is True


@pytest.mark.asyncio
async def test_progress_dialog_escape_does_not_dismiss():
    """Textual dispatches on_key to every MRO class that defines it, so the
    v0.2 `key_escape` no-op didn't actually suppress DialogKit's own escape
    handling — Esc silently dismissed the dialog anyway (code review v0.4).
    The fix routes through the `_on_escape` hook instead."""
    app = DialogTestApp()
    async with app.run_test() as pilot:
        dismissed = False

        def on_dismiss(_value: None) -> None:
            nonlocal dismissed
            dismissed = True

        app.push_screen(ProgressDialog("Working..."), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert dismissed is False
        assert len(app.screen_stack) == 2


@pytest.mark.asyncio
async def test_input_dialog_enter_submits_value():
    """The v0.1 ad-hoc InputDialog had no Enter handler at all — Enter while
    typing did nothing. Building on DialogKit closes that gap."""
    app = DialogTestApp()
    async with app.run_test() as pilot:
        result = "not_set"

        def on_dismiss(value: str | None) -> None:
            nonlocal result
            result = value

        app.push_screen(InputDialog("Enter name:"), callback=on_dismiss)
        await pilot.pause()
        app.screen.query_one("#input").focus()
        await pilot.pause()
        await pilot.press("f", "o", "o")
        await pilot.press("enter")
        await pilot.pause()
        assert result == "foo"

