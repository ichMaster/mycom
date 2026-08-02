"""Pilot-driven integration tests for MC-011: swap, cursor-restore, EACCES, resize."""

from __future__ import annotations

import os

import pytest
from textual.css.scalar import Unit

from mycom.app import MyComApp
from mycom.widgets.dialog import ErrorDialog


@pytest.mark.asyncio
async def test_ctrl_u_swaps_paths_and_cursor(tmp_path):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "in_a.txt").touch()
    (dir_b / "in_b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(dir_a)
        app.inactive_panel.navigate_to(dir_b)
        app.active_panel.file_list.select_by_name("in_a.txt")
        app.inactive_panel.file_list.select_by_name("in_b.txt")
        await pilot.pause()

        await pilot.press("ctrl+u")
        await pilot.pause()

        assert app.active_panel.current_path == dir_b
        assert app.inactive_panel.current_path == dir_a
        assert app.active_panel.file_list.selected_name == "in_b.txt"
        assert app.inactive_panel.file_list.selected_name == "in_a.txt"


@pytest.mark.asyncio
async def test_cursor_restores_on_go_up_via_backspace(tmp_path):
    child = tmp_path / "child"
    child.mkdir()
    (child / "inside.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(child)
        await pilot.pause()

        await pilot.press("backspace")
        await pilot.pause()

        assert app.active_panel.current_path == tmp_path
        assert app.active_panel.file_list.selected_name == "child"


@pytest.mark.asyncio
async def test_ctrl_pageup_is_go_up_alias(tmp_path):
    child = tmp_path / "child"
    child.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(child)
        await pilot.pause()

        await pilot.press("ctrl+pageup")
        await pilot.pause()

        assert app.active_panel.current_path == tmp_path
        assert app.active_panel.file_list.selected_name == "child"


@pytest.mark.asyncio
async def test_resize_keys_cycle_active_panel_width():
    app = MyComApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+right")
        await pilot.pause()
        assert app.active_panel.styles.width.value == 70

        await pilot.press("ctrl+left")
        await pilot.press("ctrl+left")
        await pilot.pause()
        assert app.active_panel.styles.width.value == 30
        assert app.inactive_panel.styles.width.unit == Unit.FRACTION

        # Clamped at the bottom, not wrapping.
        await pilot.press("ctrl+left")
        await pilot.pause()
        assert app.active_panel.styles.width.value == 30


@pytest.mark.skipif(os.getuid() == 0, reason="permission bits are bypassed when running as root")
@pytest.mark.asyncio
async def test_eacces_shows_error_dialog_and_stays_in_place(tmp_path):
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    try:
        app = MyComApp()
        async with app.run_test() as pilot:
            app.active_panel.navigate_to(tmp_path)
            await pilot.pause()
            before = app.active_panel.current_path

            app.active_panel.navigate_to(locked)
            await pilot.pause()

            assert isinstance(app.screen, ErrorDialog)
            assert app.active_panel.current_path == before

            await pilot.press("enter")
            await pilot.pause()
            assert not isinstance(app.screen, ErrorDialog)
    finally:
        locked.chmod(0o755)
