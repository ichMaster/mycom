"""Pilot-driven integration tests for MC-031: Rename (Shift+F6)."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from tests.integration.test_copy_keys import _wait_until


@pytest.mark.asyncio
async def test_shift_f6_prefills_with_stem_selected(tmp_path):
    (tmp_path / "report.txt").write_bytes(b"data")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("report.txt")
        await pilot.pause()

        await pilot.press("shift+f6")
        await pilot.pause()

        assert len(app.screen_stack) == 2
        input_widget = app.screen.query_one("#input")
        assert input_widget.value == "report.txt"
        assert input_widget.selected_text == "report"


@pytest.mark.asyncio
async def test_shift_f6_renames_in_place_and_cursor_follows(tmp_path):
    (tmp_path / "report.txt").write_bytes(b"data")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("report.txt")
        await pilot.pause()

        await pilot.press("shift+f6")
        await pilot.pause()
        await pilot.press("x")  # overwrites the pre-selected stem -> "x.txt"
        await pilot.press("enter")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert not (tmp_path / "report.txt").exists()
    assert (tmp_path / "x.txt").read_bytes() == b"data"
    assert app.active_panel.file_list.selected_name == "x.txt"


@pytest.mark.asyncio
async def test_shift_f6_works_on_directories(tmp_path):
    (tmp_path / "olddir").mkdir()
    (tmp_path / "olddir" / "inside.txt").write_bytes(b"data")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("olddir")
        await pilot.pause()

        await pilot.press("shift+f6")
        await pilot.pause()
        app.screen.query_one("#input").value = "newdir"
        await pilot.press("enter")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert not (tmp_path / "olddir").exists()
    assert (tmp_path / "newdir" / "inside.txt").read_bytes() == b"data"


@pytest.mark.asyncio
async def test_shift_f6_same_name_is_noop(tmp_path):
    (tmp_path / "report.txt").write_bytes(b"data")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("report.txt")
        await pilot.pause()

        await pilot.press("shift+f6")
        await pilot.pause()
        await pilot.press("enter")  # unchanged default value
        await pilot.pause()

        assert len(app.screen_stack) == 1
        assert (tmp_path / "report.txt").read_bytes() == b"data"


@pytest.mark.asyncio
async def test_shift_f6_conflict_routes_through_conflict_dialog_not_exception(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"a-content")
    (tmp_path / "b.txt").write_bytes(b"b-content")

    app = MyComApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("shift+f6")
        await pilot.pause()
        app.screen.query_one("#input").value = "b.txt"
        await pilot.press("enter")
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 2)
        assert app.screen_stack[-1].__class__.__name__ == "ConflictDialog"
        await pilot.click("#overwrite")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert not (tmp_path / "a.txt").exists()
    assert (tmp_path / "b.txt").read_bytes() == b"a-content"


@pytest.mark.asyncio
async def test_shift_f6_dotdot_is_noop(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await pilot.press("shift+f6")
        await pilot.pause()
        assert len(app.screen_stack) == 1
