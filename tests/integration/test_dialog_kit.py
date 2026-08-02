"""Pilot-driven integration tests for MC-015: the DialogKit engine."""

from __future__ import annotations

import pytest
from textual.app import ComposeResult
from textual.widgets import Input, Static

from mycom.widgets.dialog import DialogButton, DialogKit
from tests.support import ThemedApp


class _TwoButtonDialog(DialogKit[str]):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            title="Pick one",
            message="Choose Yes or No",
            buttons=(
                DialogButton("Yes", "yes", hotkey="y", default=True, variant="primary"),
                DialogButton("No", "no", hotkey="n"),
            ),
            cancel_result="cancelled",
            **kwargs,
        )

    def _result_for(self, button_id: str) -> str:
        return button_id


class _InputDialogHarness(DialogKit[str | None]):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            title="Name",
            buttons=(DialogButton("OK", "ok", hotkey="o", default=True),),
            cancel_result=None,
            **kwargs,
        )

    def compose_body(self) -> ComposeResult:
        yield Input(id="input")

    def _result_for(self, button_id: str) -> str | None:
        if button_id == "ok":
            return self.query_one("#input", Input).value
        return None


class DialogHostApp(ThemedApp):
    def compose(self) -> ComposeResult:
        yield Static("host")


@pytest.mark.asyncio
async def test_tab_and_arrows_cycle_focus_between_buttons():
    app = DialogHostApp()
    async with app.run_test() as pilot:
        app.push_screen(_TwoButtonDialog())
        await pilot.pause()

        first = app.screen.focused
        await pilot.press("tab")
        await pilot.pause()
        assert app.screen.focused is not first

        await pilot.press("left")
        await pilot.pause()
        assert app.screen.focused is first


@pytest.mark.asyncio
async def test_bare_hotkey_activates_button_when_no_input_focused():
    app = DialogHostApp()
    result = "not_set"

    def on_dismiss(value: str) -> None:
        nonlocal result
        result = value

    async with app.run_test() as pilot:
        app.push_screen(_TwoButtonDialog(), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

    assert result == "no"


@pytest.mark.asyncio
async def test_alt_hotkey_activates_button_even_with_input_focused():
    app = DialogHostApp()
    result = "not_set"

    def on_dismiss(value: str | None) -> None:
        nonlocal result
        result = value

    async with app.run_test() as pilot:
        app.push_screen(_InputDialogHarness(), callback=on_dismiss)
        await pilot.pause()
        app.screen.query_one("#input", Input).focus()
        await pilot.pause()
        await pilot.press("alt+o")
        await pilot.pause()

    assert result == ""


@pytest.mark.asyncio
async def test_enter_activates_default_button():
    app = DialogHostApp()
    result = "not_set"

    def on_dismiss(value: str) -> None:
        nonlocal result
        result = value

    async with app.run_test() as pilot:
        app.push_screen(_TwoButtonDialog(), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

    assert result == "yes"


@pytest.mark.asyncio
async def test_escape_dismisses_with_cancel_result():
    app = DialogHostApp()
    result = "not_set"

    def on_dismiss(value: str) -> None:
        nonlocal result
        result = value

    async with app.run_test() as pilot:
        app.push_screen(_TwoButtonDialog(), callback=on_dismiss)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

    assert result == "cancelled"


@pytest.mark.asyncio
async def test_input_submits_value_via_enter():
    app = DialogHostApp()
    result = "not_set"

    def on_dismiss(value: str | None) -> None:
        nonlocal result
        result = value

    async with app.run_test() as pilot:
        app.push_screen(_InputDialogHarness(), callback=on_dismiss)
        await pilot.pause()
        app.screen.query_one("#input", Input).focus()
        await pilot.pause()
        await pilot.press("h", "i")
        await pilot.press("enter")
        await pilot.pause()

    assert result == "hi"


@pytest.mark.asyncio
async def test_stacked_dialogs_dismiss_independently():
    app = DialogHostApp()
    async with app.run_test() as pilot:
        app.push_screen(_TwoButtonDialog())
        await pilot.pause()
        first_screen = app.screen

        app.push_screen(_TwoButtonDialog())
        await pilot.pause()
        assert app.screen is not first_screen

        await pilot.press("n")
        await pilot.pause()
        assert app.screen is first_screen
