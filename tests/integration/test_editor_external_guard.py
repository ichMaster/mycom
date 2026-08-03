"""Pilot-driven integration tests for MC-040: external-change guard,
$EDITOR escape hatch, and key-bar context isolation.

`self.suspend` and `subprocess.run` are both monkeypatched to fakes, same
discipline as MC-034's command-execution tests: Textual's headless test
driver can't actually suspend, and a real interactive $EDITOR has no place
in CI.
"""

from __future__ import annotations

import contextlib
import os

import pytest

import mycom.app as app_module
from mycom.app import MyComApp
from mycom.config import AppConfig, EditorConfig
from mycom.widgets.dialog import ConfirmDialog
from mycom.widgets.status_bar import StatusBar


async def _open_editor(pilot, app, tmp_path, content: bytes, name: str = "f.txt"):
    p = tmp_path / name
    p.write_bytes(content)
    app.active_panel.navigate_to(tmp_path)
    await pilot.pause()
    app.active_panel.file_list.select_by_name(name)
    await pilot.pause()
    await pilot.press("f4")
    await pilot.pause()
    return p


@pytest.mark.asyncio
async def test_saving_over_externally_modified_file_warns_first(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        p = await _open_editor(pilot, app, tmp_path, b"one\n")
        screen = app.screen
        await pilot.press("x")
        await pilot.pause()

        # Simulate an external edit, forcing a distinct mtime so this isn't
        # flaky under fast filesystems with coarse timestamp resolution.
        p.write_bytes(b"externally changed\n")
        target_mtime = screen._mtime_at_open + 5
        os.utime(p, (target_mtime, target_mtime))

        await pilot.press("f2")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmDialog)


@pytest.mark.asyncio
async def test_declining_external_change_warning_preserves_disk_and_buffer(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        p = await _open_editor(pilot, app, tmp_path, b"one\n")
        screen = app.screen
        await pilot.press("x")
        await pilot.pause()

        p.write_bytes(b"externally changed\n")
        target_mtime = screen._mtime_at_open + 5
        os.utime(p, (target_mtime, target_mtime))

        await pilot.press("f2")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmDialog)

        await pilot.press("n")  # No — decline the overwrite
        await pilot.pause()

        assert app.screen is screen
        assert p.read_bytes() == b"externally changed\n"  # disk: untouched
        assert screen._text_area.text == "xone\n"  # buffer: untouched
        assert screen.modified is True


@pytest.mark.asyncio
async def test_accepting_external_change_warning_overwrites(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        p = await _open_editor(pilot, app, tmp_path, b"one\n")
        screen = app.screen
        await pilot.press("x")
        await pilot.pause()

        p.write_bytes(b"externally changed\n")
        target_mtime = screen._mtime_at_open + 5
        os.utime(p, (target_mtime, target_mtime))

        await pilot.press("f2")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmDialog)

        await pilot.press("y")  # Yes — overwrite anyway
        await pilot.pause()

        assert app.screen is screen
        assert p.read_bytes() == b"xone\n"
        assert screen.modified is False


@pytest.mark.asyncio
async def test_saving_unchanged_file_does_not_warn(tmp_path):
    """No external modification happened — F2 must save straight through,
    no ConfirmDialog in the way."""
    app = MyComApp()
    async with app.run_test() as pilot:
        p = await _open_editor(pilot, app, tmp_path, b"one\n")
        screen = app.screen
        await pilot.press("x")
        await pilot.pause()

        await pilot.press("f2")
        await pilot.pause()

        assert app.screen is screen
        assert p.read_bytes() == b"xone\n"


@pytest.mark.asyncio
async def test_alt_f4_suspends_runs_editor_and_refreshes_panel(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)
    monkeypatch.setenv("EDITOR", "my-editor")

    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()

        await pilot.press("alt+f4")
        await pilot.pause()

        assert len(app.screen_stack) == 1  # no EditorScreen was ever pushed
    assert calls == [["my-editor", str(p)]]


@pytest.mark.asyncio
async def test_alt_f4_splits_multi_word_editor_command(tmp_path, monkeypatch):
    """Code review #1: $EDITOR conventionally carries flags (EDITOR=
    "code --wait", "vim -O", ...) — the whole string must not be treated as
    a single binary name."""
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    calls = []
    monkeypatch.setattr(app_module.subprocess, "run", lambda argv, **kw: calls.append(argv))
    monkeypatch.setenv("EDITOR", "my-editor --flag")

    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()

        await pilot.press("alt+f4")
        await pilot.pause()

    assert calls == [["my-editor", "--flag", str(p)]]


@pytest.mark.asyncio
async def test_alt_f4_falls_back_to_vi_when_editor_is_unset_or_blank(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    calls = []
    monkeypatch.setattr(app_module.subprocess, "run", lambda argv, **kw: calls.append(argv))
    monkeypatch.setenv("EDITOR", "   ")  # blank, not just unset

    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()

        await pilot.press("alt+f4")
        await pilot.pause()

    assert calls == [["vi", str(p)]]


@pytest.mark.asyncio
async def test_alt_f4_suspend_not_supported_shows_clean_error(tmp_path):
    """No monkeypatch of `suspend` at all — exercises the real headless
    driver, which can't suspend, proving Alt+F4 degrades gracefully instead
    of crashing (same discipline as MC-034's command-execution guard)."""
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()

        await pilot.press("alt+f4")
        await pilot.pause()
        assert len(app.screen_stack) == 2  # the ErrorDialog


@pytest.mark.asyncio
async def test_editor_external_default_config_makes_f4_launch_external_editor(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    calls = []
    monkeypatch.setattr(app_module.subprocess, "run", lambda argv, **kw: calls.append(argv))
    monkeypatch.setenv("EDITOR", "my-editor")

    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")

    app = MyComApp()
    app._config = AppConfig(editor=EditorConfig(external_default=True))
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()

        await pilot.press("f4")
        await pilot.pause()

        assert len(app.screen_stack) == 1  # no EditorScreen was ever pushed
    assert calls == [["my-editor", str(p)]]


@pytest.mark.asyncio
async def test_key_bar_shows_viewer_context_while_viewer_open(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()
        await pilot.press("f3")
        await pilot.pause()

        sb = app.screen.query_one(StatusBar)
        assert sb.scope == "viewer"
        slots = {s[0]: s[1] for s in sb._slots()}
        assert slots[2] == "viewer_wrap"
        assert slots[3] == "viewer_close"
        assert "copy" not in slots.values()


@pytest.mark.asyncio
async def test_key_bar_shows_editor_context_while_editor_open(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()
        await pilot.press("f4")
        await pilot.pause()

        sb = app.screen.query_one(StatusBar)
        assert sb.scope == "editor"
        slots = {s[0]: s[1] for s in sb._slots()}
        assert slots[2] == "editor_save"
        assert slots[10] == "editor_close"
        assert "copy" not in slots.values()


@pytest.mark.asyncio
async def test_key_bar_returns_to_panel_context_after_closing_editor(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("f.txt")
        await pilot.pause()
        await pilot.press("f4")
        await pilot.pause()
        await pilot.press("f10")
        await pilot.pause()

        assert len(app.screen_stack) == 1
        sb = app.screen.query_one(StatusBar)
        assert sb.scope == "panel"
