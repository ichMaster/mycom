"""Regression tests for code review #1 (v0.6): the viewer and editor
screens must own every key while active — a key neither recognizes must
never bubble past them into a panel-level action underneath. Reproduced
empirically before the fix: pressing "+" while the viewer was open pushed
the panel's mask-select InputDialog on top of it; Ctrl+O while the editor
was open pushed the console-output screen on top of it.
"""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from mycom.editor.screen import EditorScreen
from mycom.viewer.screen import ViewerScreen


async def _open_viewer(pilot, app, tmp_path, name: str = "f.txt") -> None:
    p = tmp_path / name
    p.write_bytes(b"one\ntwo\n")
    app.active_panel.navigate_to(tmp_path)
    await pilot.pause()
    app.active_panel.file_list.select_by_name(name)
    await pilot.pause()
    await pilot.press("f3")
    await pilot.pause()


async def _open_editor(pilot, app, tmp_path, name: str = "f.txt") -> None:
    p = tmp_path / name
    p.write_bytes(b"one\ntwo\n")
    app.active_panel.navigate_to(tmp_path)
    await pilot.pause()
    app.active_panel.file_list.select_by_name(name)
    await pilot.pause()
    await pilot.press("f4")
    await pilot.pause()


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["plus", "ctrl+o", "ctrl+u", "ctrl+h", "tab"])
async def test_unrecognized_key_does_not_leak_past_viewer_to_panel_action(tmp_path, key):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path)
        left_path_before = app._left_panel.current_path
        right_path_before = app._right_panel.current_path

        await pilot.press(key)
        await pilot.pause()

        assert len(app.screen_stack) == 2
        assert isinstance(app.screen, ViewerScreen)
        # Ctrl+U (panel_swap) is the one leakable action with no visible
        # dialog — assert the silent state mutation didn't happen either.
        assert app._left_panel.current_path == left_path_before
        assert app._right_panel.current_path == right_path_before


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["ctrl+o", "ctrl+u", "ctrl+h"])
async def test_unrecognized_key_does_not_leak_past_editor_to_panel_action(tmp_path, key):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path)
        left_path_before = app._left_panel.current_path
        right_path_before = app._right_panel.current_path

        await pilot.press(key)
        await pilot.pause()

        assert len(app.screen_stack) == 2
        assert isinstance(app.screen, EditorScreen)
        assert app._left_panel.current_path == left_path_before
        assert app._right_panel.current_path == right_path_before


@pytest.mark.asyncio
async def test_viewer_recognized_keys_still_work_after_the_isolation_fix(tmp_path):
    """Guards against an over-broad fix that swallows the keys the viewer
    is actually supposed to handle."""
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path)
        await pilot.press("down")
        await pilot.pause()
        assert app.screen.top_offset == 4
        await pilot.press("escape")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_editor_typing_still_works_after_the_isolation_fix(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path)
        await pilot.press("x")
        await pilot.pause()
        assert app.screen._text_area.text == "xone\ntwo\n"
