"""Pilot-driven integration tests for MC-022: Ctrl+H global hidden-files toggle."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_ctrl_h_shows_and_hides_dotfiles_in_both_panels(tmp_path):
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    (left_dir / ".hidden").touch()
    (left_dir / "visible.txt").touch()
    (right_dir / ".hidden").touch()
    (right_dir / "visible.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(left_dir)
        app.inactive_panel.navigate_to(right_dir)
        await pilot.pause()

        left_names_before = {e.name for e in app._left_panel._entries}
        right_names_before = {e.name for e in app._right_panel._entries}
        assert ".hidden" not in left_names_before
        assert ".hidden" not in right_names_before

        await pilot.press("ctrl+h")
        await pilot.pause()

        left_names_after = {e.name for e in app._left_panel._entries}
        right_names_after = {e.name for e in app._right_panel._entries}
        assert ".hidden" in left_names_after
        assert ".hidden" in right_names_after

        await pilot.press("ctrl+h")
        await pilot.pause()
        assert ".hidden" not in {e.name for e in app._left_panel._entries}
        assert ".hidden" not in {e.name for e in app._right_panel._entries}


@pytest.mark.asyncio
async def test_cursor_preserved_when_file_stays_visible(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("b.txt")
        await pilot.pause()

        await pilot.press("ctrl+h")
        await pilot.pause()

        assert app.active_panel.file_list.selected_name == "b.txt"


@pytest.mark.asyncio
async def test_cursor_falls_back_when_cursor_file_becomes_hidden(tmp_path):
    (tmp_path / ".hidden").touch()
    (tmp_path / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+h")  # show hidden files, in sync with app._show_hidden
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name(".hidden")
        await pilot.pause()
        assert app.active_panel.file_list.selected_name == ".hidden"

        await pilot.press("ctrl+h")  # hides ".hidden" — cursor can't stay on it
        await pilot.pause()

        assert app.active_panel.file_list.selected_name != ".hidden"
        assert app.active_panel.file_list.selected_name is not None


@pytest.mark.asyncio
async def test_toggle_is_a_noop_when_value_unchanged(tmp_path):
    """set_show_hidden(same value) must not clear an in-progress selection
    via a spurious refresh (it's a no-op, not a refresh-with-same-value)."""
    (tmp_path / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        app.active_panel.toggle_selection_at_cursor()
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}

        app.active_panel.set_show_hidden(app.active_panel._show_hidden)  # same value
        assert app.active_panel.selected_names == {"a.txt"}
