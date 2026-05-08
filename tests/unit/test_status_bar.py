"""Tests for StatusBar widget."""

import pytest
from textual.app import App, ComposeResult

from mycom.widgets.status_bar import HINT_ITEMS, StatusBar


class StatusBarApp(App):
    def compose(self) -> ComposeResult:
        yield StatusBar()


@pytest.mark.asyncio
async def test_status_bar_renders():
    async with StatusBarApp().run_test() as pilot:
        sb = pilot.app.query_one(StatusBar)
        assert sb is not None


@pytest.mark.asyncio
async def test_status_bar_has_default_hints():
    sb = StatusBar()
    assert sb.hints == list(HINT_ITEMS)
    assert len(sb.hints) == 8


@pytest.mark.asyncio
async def test_status_bar_custom_hints():
    custom = [("f1", "About"), ("f10", "Exit")]
    sb = StatusBar(hints=custom)
    assert sb.hints == custom
