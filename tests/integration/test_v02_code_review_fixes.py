"""Regression tests for spec/roadmap/implementation/v0.2-code-review.md findings 1-2."""

from __future__ import annotations

import pytest
from textual.app import ComposeResult
from textual.widgets import Input, Static

from mycom.widgets.dialog import DialogButton, DialogKit
from tests.support import ThemedApp


class _InputAndButtonsDialog(DialogKit[str | None]):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            title="Name",
            buttons=(
                DialogButton("OK", "ok", hotkey="o", default=True),
                DialogButton("Cancel", "cancel", hotkey="c"),
            ),
            cancel_result=None,
            **kwargs,
        )

    def compose_body(self) -> ComposeResult:
        yield Input(id="input")

    def _result_for(self, button_id: str) -> str | None:
        return button_id


class DialogHostApp(ThemedApp):
    def compose(self) -> ComposeResult:
        yield Static("host")


@pytest.mark.asyncio
async def test_arrow_cycling_never_lands_on_input():
    """Finding 1: arrow-key focus cycling must stay among buttons — landing
    on the Input would strand keyboard-only arrow navigation there forever."""
    app = DialogHostApp()
    async with app.run_test() as pilot:
        app.push_screen(_InputAndButtonsDialog())
        await pilot.pause()

        # The Input auto-focuses first (it's first in compose order); Tab
        # away from it onto a button before exercising arrow-cycling, since
        # arrows intentionally edit text while the Input itself is focused.
        assert isinstance(app.screen.focused, Input)
        await pilot.press("tab")
        await pilot.pause()
        assert not isinstance(app.screen.focused, Input)

        # Cycle forward far more times than there are buttons; focus must
        # never once land back on the Input.
        for _ in range(10):
            await pilot.press("right")
            await pilot.pause()
            assert not isinstance(app.screen.focused, Input)


@pytest.mark.asyncio
async def test_arrow_cycling_wraps_between_both_buttons():
    app = DialogHostApp()
    async with app.run_test() as pilot:
        app.push_screen(_InputAndButtonsDialog())
        await pilot.pause()

        await pilot.press("tab")  # Input -> OK
        await pilot.pause()
        first = app.screen.focused
        assert not isinstance(first, Input)

        await pilot.press("right")
        await pilot.pause()
        second = app.screen.focused
        assert second is not first
        assert not isinstance(second, Input)

        await pilot.press("right")
        await pilot.pause()
        assert app.screen.focused is first
