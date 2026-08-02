"""Pilot-driven integration tests for MC-020: mask select/deselect dialogs."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from mycom.widgets.dialog import InputDialog


@pytest.mark.asyncio
async def test_plus_opens_dialog_and_selects_matching_files(tmp_path):
    (tmp_path / "a.py").touch()
    (tmp_path / "b.py").touch()
    (tmp_path / "c.md").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        await pilot.press("+")
        await pilot.pause()
        assert isinstance(app.screen, InputDialog)

        # Clear the pre-filled "*" and type "*.py".
        app.screen.query_one("#input").value = ""
        await pilot.press("*", ".", "p", "y")
        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.selected_names == {"a.py", "b.py"}


@pytest.mark.asyncio
async def test_minus_deselects_matching_files(tmp_path):
    # A subdirectory, not tmp_path itself — conftest's autouse fixture points
    # MYCOM_LOG_FILE at tmp_path/mycom.log, which "*" would also select.
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.py").touch()
    (content_dir / "b.py").touch()
    (content_dir / "c.md").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.py", "b.py", "c.md"}

        await pilot.press("-")
        await pilot.pause()
        app.screen.query_one("#input").value = ""
        await pilot.press("*", ".", "p", "y")
        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.selected_names == {"c.md"}


@pytest.mark.asyncio
async def test_escape_cancels_without_changing_selection(tmp_path):
    (tmp_path / "a.py").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        await pilot.press("+")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert app.active_panel.selected_names == frozenset()
