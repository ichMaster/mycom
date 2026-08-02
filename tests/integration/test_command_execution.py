"""Pilot-driven integration tests for MC-034: wire Enter-to-execute.

`self.suspend` and `run_in_pty` are both monkeypatched to fakes for the
happy-path tests — Textual's headless test driver can't actually suspend
(confirmed by reading textual/drivers/headless_driver.py directly: it
doesn't override Driver.can_suspend, which defaults to False), and real
`vim`/`htop` interactivity is an explicit manual matrix per roadmap §v0.5
Tests, not something this suite drives.
"""

from __future__ import annotations

import contextlib

import pytest

import mycom.app as app_module
from mycom.app import MyComApp


async def _submit_command(pilot, app, text: str) -> None:
    app.active_panel.file_list.focus()
    await pilot.pause()
    for ch in text:
        await pilot.press("space" if ch == " " else ch)
    await pilot.press("enter")
    await pilot.pause()


@pytest.mark.asyncio
async def test_command_reaches_run_in_pty_with_active_panel_cwd(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    calls = []

    def fake_run_in_pty(command, cwd, on_data):
        calls.append((command, cwd))
        return 0

    monkeypatch.setattr(app_module, "run_in_pty", fake_run_in_pty)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await _submit_command(pilot, app, "ls -la")

    assert calls == [("ls -la", tmp_path)]


@pytest.mark.asyncio
async def test_silent_zero_exit_skips_press_any_key(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    monkeypatch.setattr(app_module, "run_in_pty", lambda command, cwd, on_data: 0)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await _submit_command(pilot, app, "true")

        assert len(app.screen_stack) == 1
        assert app.active_panel.file_list.has_focus


@pytest.mark.asyncio
async def test_output_zero_exit_shows_press_any_key_without_exit_code(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())

    def fake_run_in_pty(command, cwd, on_data):
        on_data(b"hello\n")
        return 0

    monkeypatch.setattr(app_module, "run_in_pty", fake_run_in_pty)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await _submit_command(pilot, app, "echo hello")

        assert len(app.screen_stack) == 2
        text = app.screen.query_one("Static").render()
        assert "Press any key" in str(text)
        assert "Exit code" not in str(text)

        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_silent_nonzero_exit_shows_exit_code(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    monkeypatch.setattr(app_module, "run_in_pty", lambda command, cwd, on_data: 2)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await _submit_command(pilot, app, "false")

        assert len(app.screen_stack) == 2
        text = str(app.screen.query_one("Static").render())
        assert "Exit code: 2" in text
        assert "Press any key" in text

        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_output_and_nonzero_exit_shows_both(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())

    def fake_run_in_pty(command, cwd, on_data):
        on_data(b"partial output\n")
        return 5

    monkeypatch.setattr(app_module, "run_in_pty", fake_run_in_pty)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await _submit_command(pilot, app, "broken-thing")

        text = str(app.screen.query_one("Static").render())
        assert "Exit code: 5" in text
        assert "Press any key" in text

        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_both_panels_refresh_after_command(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())

    src = tmp_path / "src"
    src.mkdir()

    def fake_run_in_pty(command, cwd, on_data):
        (src / "new_file.txt").write_bytes(b"created externally")
        return 0

    monkeypatch.setattr(app_module, "run_in_pty", fake_run_in_pty)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src)
        app.inactive_panel.navigate_to(src)
        await pilot.pause()
        await _submit_command(pilot, app, "touch new_file.txt")

        assert "new_file.txt" in {e.name for e in app.active_panel._entries}
        assert "new_file.txt" in {e.name for e in app.inactive_panel._entries}


@pytest.mark.asyncio
async def test_suspend_not_supported_shows_clean_error_not_a_crash(tmp_path):
    """No monkeypatch of `suspend` at all — exercises the REAL headless
    driver, which can't suspend (SuspendNotSupported), proving the app
    survives instead of propagating the exception uncaught."""
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await _submit_command(pilot, app, "ls")

        assert len(app.screen_stack) == 2
        text = str(app.screen.query_one("Static").render())
        assert "Command failed" in text

        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1  # app is still alive and responsive


@pytest.mark.asyncio
async def test_unexpected_os_error_from_run_in_pty_shows_clean_error(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())

    def raising_run_in_pty(command, cwd, on_data):
        raise OSError("no such shell")

    monkeypatch.setattr(app_module, "run_in_pty", raising_run_in_pty)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await _submit_command(pilot, app, "ls")

        assert len(app.screen_stack) == 2
        text = str(app.screen.query_one("Static").render())
        assert "Command failed" in text

        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1
