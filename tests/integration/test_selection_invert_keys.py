"""Pilot-driven integration tests for MC-021: invert key + select-all via mask."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_asterisk_key_inverts_selection(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.txt").touch()
    (content_dir / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("a.txt", True)
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}

        await pilot.press("asterisk")
        await pilot.pause()
        assert app.active_panel.selected_names == {"b.txt"}


@pytest.mark.asyncio
async def test_alt_8_also_inverts(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()

        await pilot.press("alt+8")
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}


@pytest.mark.asyncio
async def test_plus_enter_default_pattern_selects_all(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.txt").touch()
    (content_dir / "b.py").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()

        await pilot.press("plus")
        await pilot.pause()
        await pilot.press("enter")  # default pattern "*", no typing
        await pilot.pause()

        assert app.active_panel.selected_names == {"a.txt", "b.py"}
