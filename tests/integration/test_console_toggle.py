"""Pilot-driven integration tests for MC-035: Ctrl+O toggle + cd-sync polish."""

from __future__ import annotations

import contextlib

import pytest

import mycom.app as app_module
from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_ctrl_o_with_no_output_yet_shows_placeholder(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        await pilot.press("ctrl+o")
        await pilot.pause()

        assert len(app.screen_stack) == 2
        text = str(app.screen.query_one("Static").render())
        assert "No output yet" in text

        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_ctrl_o_recalls_last_command_output(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())

    def fake_run_in_pty(command, cwd, on_data):
        on_data(b"line one\nline two\n")
        return 0

    monkeypatch.setattr(app_module, "run_in_pty", fake_run_in_pty)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()
        for ch in "mycommand":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("enter")  # dismiss "Press any key"
        await pilot.pause()

        await pilot.press("ctrl+o")
        await pilot.pause()

        assert len(app.screen_stack) == 2
        text = str(app.screen.query_one("Static").render())
        assert "line one" in text
        assert "line two" in text

        await pilot.press("escape")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_ctrl_o_does_not_rerun_anything(tmp_path, monkeypatch):
    monkeypatch.setattr(MyComApp, "suspend", lambda self: contextlib.nullcontext())
    call_count = 0

    def fake_run_in_pty(command, cwd, on_data):
        nonlocal call_count
        call_count += 1
        on_data(b"output\n")
        return 0

    monkeypatch.setattr(app_module, "run_in_pty", fake_run_in_pty)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()
        for ch in "once":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert call_count == 1

        await pilot.press("ctrl+o")
        await pilot.pause()
        await pilot.press("ctrl+o")
        await pilot.pause()

        assert call_count == 1  # recall never re-executes


@pytest.mark.asyncio
async def test_prompt_stays_in_sync_across_full_navigation_audit(tmp_path):
    """Every navigation call site wired for cd-sync in one pass: Enter-into,
    Backspace-up, Tab-switch, Ctrl+U-swap."""
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    nested = left_dir / "nested"
    nested.mkdir(parents=True)
    right_dir.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app._left_panel.navigate_to(left_dir)
        app._right_panel.navigate_to(right_dir)
        await pilot.pause()
        app.active_panel.file_list.focus()

        # Enter-into
        app.active_panel.file_list.select_by_name("nested")
        await pilot.press("enter")
        await pilot.pause()
        assert str(nested) in app._command_line._prompt_text()

        # Backspace-up
        await pilot.press("backspace")
        await pilot.pause()
        assert str(left_dir) in app._command_line._prompt_text()

        # Tab-switch
        await pilot.press("tab")
        await pilot.pause()
        assert str(right_dir) in app._command_line._prompt_text()

        # Ctrl+U swap
        await pilot.press("ctrl+u")
        await pilot.pause()
        assert str(left_dir) in app._command_line._prompt_text()
