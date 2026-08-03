"""Pilot-driven integration tests for MC-039: Editor screen (F4)."""

from __future__ import annotations

import string
from pathlib import Path

import pytest

from mycom.app import MyComApp
from mycom.editor.screen import EditorScreen
from mycom.viewer.screen import ViewerScreen
from mycom.widgets.dialog import SaveDiscardCancelDialog


async def _open_editor(pilot, app, tmp_path, content: bytes, name: str = "f.txt") -> None:
    p = tmp_path / name
    p.write_bytes(content)
    app.active_panel.navigate_to(tmp_path)
    await pilot.pause()
    app.active_panel.file_list.select_by_name(name)
    await pilot.pause()
    await pilot.press("f4")
    await pilot.pause()


@pytest.mark.asyncio
async def test_f4_opens_editor_with_file_content(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\ntwo\nthree\n")
        assert len(app.screen_stack) == 2
        screen = app.screen
        assert isinstance(screen, EditorScreen)
        assert screen._text_area.text == "one\ntwo\nthree\n"
        assert screen.modified is False


@pytest.mark.asyncio
async def test_f4_on_directory_does_not_open_editor(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("sub")
        await pilot.pause()
        await pilot.press("f4")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_f4_on_binary_file_redirects_to_viewer(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"\x00\x01\x02binary\x00data", name="f.bin")
        assert isinstance(app.screen, ViewerScreen)


@pytest.mark.asyncio
async def test_f4_on_oversized_file_redirects_to_viewer(tmp_path):
    from mycom.editor.detect import MAX_EDITABLE_SIZE

    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(
            pilot, app, tmp_path, b"x" * (MAX_EDITABLE_SIZE + 1), name="big.txt"
        )
        assert isinstance(app.screen, ViewerScreen)


@pytest.mark.asyncio
async def test_typing_marks_modified_and_save_writes_and_clears_it(tmp_path):
    p = tmp_path / "f.txt"
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\ntwo\n")
        screen = app.screen
        await pilot.press("x")
        await pilot.pause()
        assert screen.modified is True

        await pilot.press("f2")
        await pilot.pause()
        assert screen.modified is False
        assert p.read_bytes() == b"xone\ntwo\n"


@pytest.mark.asyncio
async def test_crlf_round_trip_with_no_edits_produces_byte_identical_save(tmp_path):
    p = tmp_path / "f.txt"
    original = b"one\r\ntwo\r\nthree\r\n"
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, original)
        await pilot.press("f2")
        await pilot.pause()
        assert p.read_bytes() == original


@pytest.mark.asyncio
async def test_save_writes_with_newline_empty_to_avoid_double_translation(tmp_path, monkeypatch):
    """Code review #3: without newline="", Python's universal-newline
    write-mode translation would replace every embedded "\\n" (including
    ones already inside a CRLF pair from apply_eol) with os.linesep on any
    platform where os.linesep != "\\n" — currently inert on POSIX (where
    os.linesep == "\\n" makes it a no-op) but not a portable guarantee.
    Asserts the call contract directly rather than only the POSIX-incidental
    output the CRLF round-trip test above already covers."""
    calls = []
    real_write_text = Path.write_text

    def spy_write_text(self, *args, **kwargs):
        calls.append(kwargs.get("newline"))
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", spy_write_text)

    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\r\ntwo\r\n")
        await pilot.press("f2")
        await pilot.pause()

    assert calls == [""]


@pytest.mark.asyncio
async def test_trailing_newline_absent_stays_absent_after_save(tmp_path):
    p = tmp_path / "f.txt"
    original = b"one\ntwo"
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, original)
        await pilot.press("f2")
        await pilot.pause()
        assert p.read_bytes() == original


@pytest.mark.asyncio
async def test_trailing_newline_present_stays_present_after_save(tmp_path):
    p = tmp_path / "f.txt"
    original = b"one\ntwo\n"
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, original)
        await pilot.press("f2")
        await pilot.pause()
        assert p.read_bytes() == original


@pytest.mark.asyncio
async def test_undo_redo_chain_replays_correctly(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"", name="f.txt")
        screen = app.screen

        chars = ((string.ascii_lowercase + string.digits) * 2)[:55]
        for ch in chars:
            await pilot.press(ch)
        await pilot.pause()
        final_text = screen._text_area.text
        assert final_text == chars

        for _ in range(len(chars) + 10):
            await pilot.press("ctrl+z")
        await pilot.pause()
        assert screen._text_area.text == ""

        for _ in range(len(chars) + 10):
            await pilot.press("ctrl+y")
        await pilot.pause()
        assert screen._text_area.text == final_text


@pytest.mark.asyncio
async def test_quit_without_modifications_closes_immediately(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\n")
        assert len(app.screen_stack) == 2
        await pilot.press("f10")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_dirty_close_guard_cancel_returns_to_editing_with_buffer_intact(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\n")
        screen = app.screen
        await pilot.press("x")
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()
        assert len(app.screen_stack) == 3
        assert isinstance(app.screen, SaveDiscardCancelDialog)

        await pilot.press("escape")  # Cancel: stay in the editor
        await pilot.pause()
        assert len(app.screen_stack) == 2
        assert app.screen is screen
        assert screen._text_area.text == "xone\n"
        assert screen.modified is True


@pytest.mark.asyncio
async def test_dirty_close_guard_discard_closes_without_writing(tmp_path):
    p = tmp_path / "f.txt"
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\n")
        await pilot.press("x")
        await pilot.pause()

        await pilot.press("f10")
        await pilot.pause()
        assert isinstance(app.screen, SaveDiscardCancelDialog)

        await pilot.press("d")  # Discard hotkey
        await pilot.pause()
        assert len(app.screen_stack) == 1
        assert p.read_bytes() == b"one\n"  # unchanged


@pytest.mark.asyncio
async def test_dirty_close_guard_save_writes_then_closes(tmp_path):
    p = tmp_path / "f.txt"
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\n")
        await pilot.press("x")
        await pilot.pause()

        await pilot.press("f10")
        await pilot.pause()
        assert isinstance(app.screen, SaveDiscardCancelDialog)

        await pilot.press("enter")  # Save is the default button
        await pilot.pause()
        assert len(app.screen_stack) == 1
        assert p.read_bytes() == b"xone\n"


@pytest.mark.asyncio
async def test_save_as_continues_editing_the_new_path(tmp_path):
    original = tmp_path / "f.txt"
    app = MyComApp()
    async with app.run_test() as pilot:
        await _open_editor(pilot, app, tmp_path, b"one\n")
        screen = app.screen

        await pilot.press("shift+f2")
        await pilot.pause()
        assert len(app.screen_stack) == 3  # the save-as InputDialog

        new_path = tmp_path / "g.txt"
        # Replace the pre-filled default path with the new one.
        dialog_input = app.screen.query_one("#input")
        dialog_input.value = str(new_path)
        await pilot.press("enter")
        await pilot.pause()

        assert len(app.screen_stack) == 2  # back to the editor, still open
        assert app.screen is screen
        assert screen.path == new_path
        assert new_path.read_bytes() == b"one\n"
        assert original.read_bytes() == b"one\n"  # save-as never touches the source
