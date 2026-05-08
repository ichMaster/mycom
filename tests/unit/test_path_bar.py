"""Tests for PathBar widget."""

import pytest
from pathlib import Path
from textual.app import App, ComposeResult

from mycom.widgets.path_bar import PathBar


class PathBarApp(App):
    def compose(self) -> ComposeResult:
        yield PathBar(path=Path("/home/user/documents"))


@pytest.mark.asyncio
async def test_path_bar_shows_path():
    async with PathBarApp().run_test() as pilot:
        pb = pilot.app.query_one(PathBar)
        assert pb.path == Path("/home/user/documents")


@pytest.mark.asyncio
async def test_path_bar_update_path():
    async with PathBarApp().run_test() as pilot:
        pb = pilot.app.query_one(PathBar)
        pb.path = Path("/tmp")
        assert pb.path == Path("/tmp")


def test_truncation_short_path():
    pb = PathBar.__new__(PathBar)
    result = pb._truncate("/home/user", max_width=60)
    assert result == "/home/user"


def test_truncation_long_path():
    pb = PathBar.__new__(PathBar)
    long_path = "/home/user/" + "a" * 100
    result = pb._truncate(long_path, max_width=60)
    assert result.startswith("...")
    assert len(result) == 60


@pytest.mark.asyncio
async def test_path_bar_active_inactive():
    async with PathBarApp().run_test() as pilot:
        pb = pilot.app.query_one(PathBar)
        pb.set_active(False)
        assert "inactive" in pb.classes
        pb.set_active(True)
        assert "inactive" not in pb.classes
