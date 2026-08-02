"""Pilot-driven integration tests for MC-019: Ins/Space toggle-and-advance, footer, rendering."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from mycom.theme import SELECTED_FG


@pytest.mark.asyncio
async def test_insert_toggles_and_advances(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("insert")
        await pilot.pause()

        assert app.active_panel.selected_names == {"a.txt"}
        # Cursor advanced off "a.txt".
        assert app.active_panel.file_list.selected_name != "a.txt"


@pytest.mark.asyncio
async def test_space_also_toggles(tmp_path):
    (tmp_path / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("space")
        await pilot.pause()

        assert app.active_panel.selected_names == {"a.txt"}


@pytest.mark.asyncio
async def test_insert_twice_toggles_off(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    (tmp_path / "c.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("insert")  # select a.txt, advance
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()
        await pilot.press("insert")  # deselect a.txt
        await pilot.pause()

        assert "a.txt" not in app.active_panel.selected_names


@pytest.mark.asyncio
async def test_footer_shows_selection_count_and_size(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"x" * 1024)
    (tmp_path / "b.txt").write_bytes(b"x" * 1024)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        for name in ("a.txt", "b.txt"):
            app.active_panel.file_list.select_by_name(name)
            app.active_panel.toggle_selection_at_cursor()
            await pilot.pause()

        text = str(app.active_panel._footer.content)
        assert "2 selected" in text
        assert "2.0 KB" in text


@pytest.mark.asyncio
async def test_selected_row_renders_with_selected_fg_markup(tmp_path):
    (tmp_path / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        app.active_panel.toggle_selection_at_cursor()
        await pilot.pause()

        cell = app.active_panel.file_list.get_cell("a.txt", "name")
        assert cell == f"[{SELECTED_FG}]a.txt[/{SELECTED_FG}]"
