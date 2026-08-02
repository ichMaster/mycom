"""Pilot-driven integration tests for MC-013: sort keys and sort direction glyph."""

from __future__ import annotations

import time

import pytest

from mycom.app import MyComApp


def _make_fixture(tmp_path):
    (tmp_path / "b.txt").write_text("bb")
    time.sleep(0.01)
    (tmp_path / "a.py").write_text("a")
    time.sleep(0.01)
    (tmp_path / "z.log").write_text("zzz")
    (tmp_path / "café.md").touch()  # unicode name
    (tmp_path / "subdir").mkdir()


@pytest.mark.asyncio
async def test_ctrl_f3_sorts_by_name(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        # Switch away from the "name" default first so Ctrl+F3 selects a new
        # field (ascending) rather than toggling the direction of the default.
        await pilot.press("ctrl+f6")
        await pilot.press("ctrl+f3")
        await pilot.pause()
        assert app.active_panel.sort_field == "name"
        assert app.active_panel.sort_ascending is True


@pytest.mark.asyncio
async def test_ctrl_f4_sorts_by_extension(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+f4")
        await pilot.pause()
        assert app.active_panel.sort_field == "extension"


@pytest.mark.asyncio
async def test_ctrl_f5_sorts_by_mtime(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+f5")
        await pilot.pause()
        assert app.active_panel.sort_field == "date"


@pytest.mark.asyncio
async def test_ctrl_f6_sorts_by_size(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+f6")
        await pilot.pause()
        assert app.active_panel.sort_field == "size"


@pytest.mark.asyncio
async def test_same_key_twice_toggles_direction(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+f6")
        await pilot.pause()
        assert app.active_panel.sort_ascending is True

        await pilot.press("ctrl+f6")
        await pilot.pause()
        assert app.active_panel.sort_field == "size"
        assert app.active_panel.sort_ascending is False


@pytest.mark.asyncio
async def test_dirs_stay_first_after_sort(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+f6")
        await pilot.pause()
        await pilot.press("ctrl+f6")  # descending
        await pilot.pause()

        table = app.active_panel.file_list
        rows = list(table.rows)
        # First data row (after "..") should be the directory.
        assert str(rows[1].value) == "subdir"


@pytest.mark.asyncio
async def test_sort_glyph_shown_on_active_column_header(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+f6")  # size, ascending
        await pilot.pause()

        size_col = app.active_panel.file_list.ordered_columns[2]
        assert "▲" in str(size_col.label)

        await pilot.press("ctrl+f6")  # size, descending
        await pilot.pause()
        size_col = app.active_panel.file_list.ordered_columns[2]
        assert "▼" in str(size_col.label)


@pytest.mark.asyncio
async def test_no_glyph_in_brief_mode(tmp_path):
    _make_fixture(tmp_path)
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+1")  # Brief
        await pilot.pause()
        await pilot.press("ctrl+f3")
        await pilot.pause()

        for column in app.active_panel.file_list.ordered_columns:
            assert "▲" not in str(column.label) and "▼" not in str(column.label)
