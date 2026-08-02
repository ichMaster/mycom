"""Tests for MC-018: panel footer (item count, selection placeholder, free-space placeholder)."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_active_panel_footer_shows_count_and_selection_placeholder(tmp_path):
    # A subdirectory, not tmp_path itself — conftest's autouse fixture points
    # MYCOM_LOG_FILE at tmp_path/mycom.log, which would otherwise inflate
    # the listing by one entry.
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.txt").touch()
    (content_dir / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()

        text = str(app.active_panel._footer.content)
        assert text.startswith("2 items  0 selected")


@pytest.mark.asyncio
async def test_active_panel_footer_includes_cursor_name(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "only.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("only.txt")
        await pilot.pause()

        text = str(app.active_panel._footer.content)
        assert "only.txt" in text


@pytest.mark.asyncio
async def test_passive_panel_footer_shows_free_space_placeholder():
    app = MyComApp()
    async with app.run_test():
        active_text = str(app.active_panel._footer.content)
        passive_text = str(app.inactive_panel._footer.content)
        assert "free" not in active_text
        assert "free" in passive_text


@pytest.mark.asyncio
async def test_footer_updates_when_panel_activation_changes(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        was_active_footer = str(app.active_panel._footer.content)
        assert "free" not in was_active_footer

        await pilot.press("tab")
        await pilot.pause()

        # The panel that was active is now passive and must show the placeholder.
        now_passive = app.inactive_panel
        assert "free" in str(now_passive._footer.content)
        assert "free" not in str(app.active_panel._footer.content)


@pytest.mark.asyncio
async def test_singular_item_count(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "one.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        text = str(app.active_panel._footer.content)
        assert text.startswith("1 item  0 selected")
