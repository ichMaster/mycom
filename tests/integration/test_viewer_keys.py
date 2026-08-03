"""Pilot-driven integration tests for MC-037: Viewer screen (F3)."""

from __future__ import annotations

import time

import pytest

from mycom.app import MyComApp
from mycom.editor.screen import EditorScreen
from mycom.viewer.screen import ViewerScreen


async def _open_viewer(pilot, app, tmp_path, content: bytes, name: str = "f.txt") -> None:
    p = tmp_path / name
    p.write_bytes(content)
    app.active_panel.navigate_to(tmp_path)
    await pilot.pause()
    app.active_panel.file_list.select_by_name(name)
    await pilot.pause()
    await pilot.press("f3")
    await pilot.pause()


@pytest.mark.asyncio
async def test_f3_opens_viewer_with_file_content(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, b"one\ntwo\nthree\n")
        assert len(app.screen_stack) == 2
        screen = app.screen
        assert isinstance(screen, ViewerScreen)
        assert "one" in screen._body.content.plain
        assert "two" in screen._body.content.plain


@pytest.mark.asyncio
async def test_f3_on_directory_does_not_open_viewer(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("sub")
        await pilot.pause()
        await pilot.press("f3")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("close_key", ["f3", "f10", "escape"])
async def test_viewer_closes_via_each_close_key(tmp_path, close_key):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, b"content\n")
        assert len(app.screen_stack) == 2
        await pilot.press(close_key)
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_f6_hands_off_to_editor_at_the_same_file(tmp_path):
    """F6 closes the viewer and opens the same file in the editor, at the
    top of the file (F0.12's own acceptance box — not the viewer's scroll
    position), landed by MC-039."""
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, b"content\n")
        assert len(app.screen_stack) == 2
        await pilot.press("f6")
        await pilot.pause()
        assert len(app.screen_stack) == 2
        assert isinstance(app.screen, EditorScreen)
        assert app.screen.path == tmp_path / "f.txt"


@pytest.mark.asyncio
async def test_line_down_and_up_navigate_by_one_line(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, b"aaa\nbbb\nccc\n")
        screen = app.screen
        assert screen.top_offset == 0
        await pilot.press("down")
        await pilot.pause()
        assert screen.top_offset == 4  # start of "bbb"
        await pilot.press("up")
        await pilot.pause()
        assert screen.top_offset == 0


@pytest.mark.asyncio
async def test_page_down_then_page_up_returns_to_start(tmp_path):
    content = "".join(f"line{i}\n" for i in range(500)).encode()
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, content, name="big.txt")
        screen = app.screen
        await pilot.press("pagedown")
        await pilot.pause()
        assert screen.top_offset > 0
        await pilot.press("pageup")
        await pilot.pause()
        assert screen.top_offset == 0


@pytest.mark.asyncio
async def test_home_and_end_jump_to_file_boundaries(tmp_path):
    content = "".join(f"line{i}\n" for i in range(500)).encode()
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, content, name="big.txt")
        screen = app.screen
        await pilot.press("end")
        await pilot.pause()
        assert screen.top_offset > 0
        await pilot.press("home")
        await pilot.pause()
        assert screen.top_offset == 0


@pytest.mark.asyncio
async def test_wrap_toggle_preserves_top_offset(tmp_path):
    content = "".join(f"line{i}\n" for i in range(500)).encode()
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, content, name="big.txt")
        screen = app.screen
        await pilot.press("pagedown")
        await pilot.pause()
        offset_before = screen.top_offset
        assert offset_before > 0

        await pilot.press("f2")
        await pilot.pause()
        assert screen._wrap is True
        assert screen.top_offset == offset_before

        await pilot.press("f2")
        await pilot.pause()
        assert screen._wrap is False
        assert screen.top_offset == offset_before


@pytest.mark.asyncio
async def test_externally_modified_file_does_not_crash_viewer(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_viewer(pilot, app, tmp_path, b"one\ntwo\nthree\n")
        screen = app.screen
        # Modify the file on disk while the viewer holds it open — the mmap
        # window may go stale, but the viewer must keep working, not crash.
        (tmp_path / "f.txt").write_bytes(b"one\ntwo\nthree\nfour\nfive\n")
        await pilot.press("down")
        await pilot.pause()
        assert len(app.screen_stack) == 2
        assert screen.top_offset >= 0


@pytest.mark.asyncio
async def test_large_file_opens_and_reaches_eof_quickly_through_real_screen(tmp_path):
    """Re-exercises MC-036's own bounded-time guarantee through the real
    Pilot-driven screen, not a fresh timing bound at the UI layer."""
    p = tmp_path / "big.log"
    block = "".join(f"line {i:08d}\n" for i in range(2000)).encode()
    with open(p, "wb") as f:
        written = 0
        target = 200 * 1024 * 1024
        while written < target:
            f.write(block)
            written += len(block)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("big.log")
        await pilot.pause()

        start_open = time.monotonic()
        await pilot.press("f3")
        await pilot.pause()
        elapsed_open = time.monotonic() - start_open
        assert len(app.screen_stack) == 2

        start_end = time.monotonic()
        await pilot.press("end")
        await pilot.pause()
        elapsed_end = time.monotonic() - start_end

    assert elapsed_open < 1.0
    assert elapsed_end < 1.0
