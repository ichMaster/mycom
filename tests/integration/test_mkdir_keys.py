"""Pilot-driven integration tests for MC-029: Mkdir (F7)."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_f7_creates_directory_and_cursor_lands_on_it(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        await pilot.press("f7")
        await pilot.pause()
        for ch in "newdir":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        assert (tmp_path / "newdir").is_dir()
        assert app.active_panel.file_list.selected_name == "newdir"


@pytest.mark.asyncio
async def test_f7_creates_nested_chain_in_one_step(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        await pilot.press("f7")
        await pilot.pause()
        for ch in "a/b/c":
            await pilot.press("slash" if ch == "/" else ch)
        await pilot.press("enter")
        await pilot.pause()

        assert (tmp_path / "a" / "b" / "c").is_dir()
        assert app.active_panel.file_list.selected_name == "a"


@pytest.mark.asyncio
async def test_f7_existing_name_shows_error_and_reopens_prefilled(tmp_path):
    (tmp_path / "existing").mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        await pilot.press("f7")
        await pilot.pause()
        for ch in "existing":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        # ErrorDialog on top
        assert len(app.screen_stack) == 2
        await pilot.press("enter")  # dismiss the error (OK is default)
        await pilot.pause()

        # InputDialog reopened, pre-filled with the attempted name
        assert len(app.screen_stack) == 2
        input_widget = app.screen.query_one("#input")
        assert input_widget.value == "existing"

        # correct it and retry
        await pilot.press("end")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        assert (tmp_path / "existing2").is_dir()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_f7_empty_name_is_noop(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()

        await pilot.press("f7")
        await pilot.pause()
        await pilot.press("enter")  # confirm with the empty default
        await pilot.pause()

        assert len(app.screen_stack) == 1
        assert list(content_dir.iterdir()) == []
