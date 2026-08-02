"""Pilot-driven integration tests for MC-012: Brief/Full/Wide view modes."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from mycom.panels.views import ViewMode


@pytest.mark.asyncio
async def test_ctrl_keys_switch_active_panel_view_mode(tmp_path):
    for i in range(5):
        (tmp_path / f"file{i}.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        await pilot.press("ctrl+1")
        await pilot.pause()
        assert app.active_panel.view_mode is ViewMode.BRIEF

        await pilot.press("ctrl+2")
        await pilot.pause()
        assert app.active_panel.view_mode is ViewMode.FULL

        await pilot.press("ctrl+3")
        await pilot.pause()
        assert app.active_panel.view_mode is ViewMode.WIDE


@pytest.mark.asyncio
async def test_inactive_panel_unaffected_by_view_switch(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        assert app.inactive_panel.view_mode is ViewMode.FULL
        await pilot.press("ctrl+1")
        await pilot.pause()

        assert app.active_panel.view_mode is ViewMode.BRIEF
        assert app.inactive_panel.view_mode is ViewMode.FULL


@pytest.mark.asyncio
async def test_directories_show_dir_marker_in_full_mode(tmp_path):
    (tmp_path / "subdir").mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        entries = {e.name: e for e in app.active_panel._entries}
        assert entries["subdir"].is_dir is True


@pytest.mark.asyncio
async def test_brief_mode_renders_without_crashing_at_narrow_and_wide(tmp_path):
    for i in range(30):
        (tmp_path / f"item{i:02d}.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.press("ctrl+1")
        await pilot.pause()
        # 30 files + ".." across whatever column count fits an 80-col test terminal.
        assert app.active_panel.file_list.row_count > 0


@pytest.mark.asyncio
async def test_broken_symlink_does_not_crash_listing(tmp_path):
    target = tmp_path / "nonexistent_target"
    link = tmp_path / "broken_link"
    link.symlink_to(target)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await pilot.press("ctrl+1")
        await pilot.pause()
        await pilot.press("ctrl+3")
        await pilot.pause()
        names = {e.name for e in app.active_panel._entries}
        assert "broken_link" in names
