"""Pilot-driven integration tests for MC-032: command-line widget + cd interception."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_typing_a_letter_routes_to_command_line_not_the_panel(tmp_path):
    (tmp_path / "alpha.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()

        await pilot.press("l")
        await pilot.pause()
        await pilot.press("s")
        await pilot.pause()

        assert app._command_line.input.value == "ls"
        assert app._command_line.input.has_focus


@pytest.mark.asyncio
async def test_navigation_keys_still_reach_the_panel_while_typing_elsewhere(tmp_path):
    child = tmp_path / "child"
    child.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        app.active_panel.file_list.select_by_name("child")
        await pilot.pause()

        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.current_path == child
        assert app._command_line.input.value == ""  # never touched


@pytest.mark.asyncio
async def test_cd_absolute_path_navigates_active_panel(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()

        for ch in f"cd {dest}":
            await pilot.press("space" if ch == " " else ch)
        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.current_path == dest
        assert app._command_line.input.value == ""


@pytest.mark.asyncio
async def test_cd_relative_path_resolves_against_active_panel_not_process_cwd(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()

        for ch in "cd sub":
            await pilot.press("space" if ch == " " else ch)
        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.current_path == sub


@pytest.mark.asyncio
async def test_cd_nonexistent_reports_error_and_stays_in_place(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()

        for ch in "cd nonexistent":
            await pilot.press("space" if ch == " " else ch)
        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.current_path == tmp_path
        assert len(app.screen_stack) == 2  # the error dialog navigate_to shows
        await pilot.press("enter")  # dismiss it


@pytest.mark.asyncio
async def test_escape_clears_command_line_and_returns_focus_to_panel(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()

        await pilot.press("l")
        await pilot.pause()
        assert app._command_line.input.value == "l"

        await pilot.press("escape")
        await pilot.pause()

        assert app._command_line.input.value == ""
        assert app.active_panel.file_list.has_focus


@pytest.mark.asyncio
async def test_prompt_shows_active_panel_directory_and_follows_switches(tmp_path):
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        # Real interaction (typed `cd`), not a direct panel.navigate_to()
        # bypass — cd-sync is wired at MyComApp's navigation call sites, not
        # inside FileBrowserPanel itself; a full audit of every call site
        # (so *any* navigation, however triggered, stays in sync) is
        # MC-035's job.
        app.active_panel.file_list.focus()
        await pilot.pause()
        for ch in f"cd {left_dir}":
            await pilot.press("space" if ch == " " else ch)
        await pilot.press("enter")
        await pilot.pause()

        assert str(left_dir) in app._command_line._prompt_text()

        await pilot.press("tab")
        await pilot.pause()
        app.active_panel.file_list.focus()
        for ch in f"cd {right_dir}":
            await pilot.press("space" if ch == " " else ch)
        await pilot.press("enter")
        await pilot.pause()

        assert str(right_dir) in app._command_line._prompt_text()

        await pilot.press("tab")
        await pilot.pause()

        assert str(left_dir) in app._command_line._prompt_text()


@pytest.mark.asyncio
async def test_bound_keymap_key_does_not_also_leak_into_command_line(tmp_path):
    """A key that already has a real keymap action (e.g. `+` for select-by-
    mask) must not ALSO get typed into the command line — both reach
    App.on_key (it bubbles regardless of the binding), so on_key must only
    treat a key as "route to command line" when no action claims it."""
    (tmp_path / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.focus()
        await pilot.pause()

        await pilot.press("plus")
        await pilot.pause()

        assert len(app.screen_stack) == 2  # the mask-select InputDialog opened
        assert app._command_line.input.value == ""  # not also typed here
