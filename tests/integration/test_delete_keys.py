"""Pilot-driven integration tests for MC-030: Delete (F8)."""

from __future__ import annotations

import stat

import pytest

from mycom.app import MyComApp
from tests.integration.test_copy_keys import _wait_until


@pytest.mark.asyncio
async def test_f8_single_file_confirm_deletes(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"x")
    (tmp_path / "b.txt").write_bytes(b"y")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        assert len(app.screen_stack) == 2
        await pilot.press("enter")  # Yes is default
        await pilot.pause()

        assert not (tmp_path / "a.txt").exists()
        assert (tmp_path / "b.txt").exists()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_f8_escape_cancels_and_deletes_nothing(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"x")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert (tmp_path / "a.txt").exists()
        assert app.active_panel.file_list.selected_name == "a.txt"  # cursor untouched


@pytest.mark.asyncio
async def test_f8_multi_selection_prompt_and_cursor_moves_to_survivor(tmp_path):
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_bytes(b"x")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.replace_selection({"a.txt", "b.txt"})
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        assert len(app.screen_stack) == 2
        await pilot.press("enter")
        await pilot.pause()

        assert not (tmp_path / "a.txt").exists()
        assert not (tmp_path / "b.txt").exists()
        assert (tmp_path / "c.txt").exists()
        assert app.active_panel.file_list.selected_name == "c.txt"


@pytest.mark.asyncio
async def test_f8_non_empty_directory_gets_second_stronger_confirmation(tmp_path):
    d = tmp_path / "full_dir"
    d.mkdir()
    (d / "inside.txt").write_bytes(b"data")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("full_dir")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        await pilot.press("enter")  # first confirm
        await pilot.pause()

        assert len(app.screen_stack) == 2  # the SECOND, stronger confirmation
        await pilot.press("enter")
        await pilot.pause()

        assert not d.exists()


@pytest.mark.asyncio
async def test_f8_declining_nonempty_dir_confirmation_aborts_entirely(tmp_path):
    d = tmp_path / "full_dir"
    d.mkdir()
    (d / "inside.txt").write_bytes(b"data")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("full_dir")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        await pilot.press("enter")  # first confirm
        await pilot.pause()
        await pilot.press("n")  # decline the non-empty-dir confirmation
        await pilot.pause()

        assert d.exists()
        assert (d / "inside.txt").exists()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_f8_readonly_file_prompts_individually_and_can_be_kept(tmp_path):
    ro = tmp_path / "readonly.txt"
    ro.write_bytes(b"protected")
    ro.chmod(stat.S_IREAD)
    other = tmp_path / "other.txt"
    other.write_bytes(b"delete me")

    app = MyComApp()
    try:
        async with app.run_test() as pilot:
            app.active_panel.navigate_to(tmp_path)
            await pilot.pause()
            app.active_panel.select_by_mask("*", True)
            await pilot.pause()

            await pilot.press("f8")
            await pilot.pause()
            await pilot.press("enter")  # initial multi-confirm
            await pilot.pause()

            assert len(app.screen_stack) == 2  # the read-only prompt
            await pilot.press("n")  # keep it
            await pilot.pause()

            await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

        assert ro.exists()
        assert ro.read_bytes() == b"protected"
        assert not other.exists()
    finally:
        ro.chmod(stat.S_IREAD | stat.S_IWRITE)  # tmp_path cleanup needs write perms


@pytest.mark.asyncio
async def test_f8_readonly_file_can_be_deleted_when_confirmed(tmp_path):
    ro = tmp_path / "readonly.txt"
    ro.write_bytes(b"protected")
    ro.chmod(stat.S_IREAD)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("readonly.txt")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        await pilot.press("enter")  # initial confirm
        await pilot.pause()
        assert len(app.screen_stack) == 2  # read-only prompt
        await pilot.press("enter")  # Yes is default -> delete it
        await pilot.pause()

        assert not ro.exists()


@pytest.mark.asyncio
async def test_f8_large_tree_shows_progress_dialog(tmp_path):
    d = tmp_path / "big"
    d.mkdir()
    for i in range(30):
        (d / f"f{i:02d}.txt").write_bytes(b"x")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("big")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        await pilot.press("enter")  # initial confirm
        await pilot.pause()
        await pilot.press("enter")  # non-empty-directory confirm
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 1, timeout=10.0)

    assert not d.exists()


@pytest.mark.asyncio
async def test_f8_nothing_selected_on_dotdot_is_noop(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        await pilot.press("f8")
        await pilot.pause()
        assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_f8_unexpected_os_error_shows_error_dialog_not_a_crash(tmp_path, monkeypatch):
    """See test_copy_keys.py's equivalent — code review v0.4 #1."""
    import mycom.app as app_module

    def raising_execute_delete_plan(plan, cancel, on_progress, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(app_module, "execute_delete_plan", raising_execute_delete_plan)

    (tmp_path / "a.txt").write_bytes(b"x")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f8")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert app.screen_stack[-1].__class__.__name__ == "ErrorDialog"
        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1  # app is still alive and responsive
