"""Integration tests for MC-024: wiring mycom/state.py into the app lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from mycom.app import MyComApp, _resolve_startup_path


def test_resolve_startup_path_returns_existing_dir_unchanged(tmp_path):
    assert _resolve_startup_path(tmp_path) == tmp_path


def test_resolve_startup_path_walks_up_to_existing_ancestor(tmp_path):
    vanished = tmp_path / "gone" / "also_gone"
    assert _resolve_startup_path(vanished) == tmp_path


def test_resolve_startup_path_falls_back_to_home_when_nothing_exists():
    fully_vanished = Path("/this/does/not/exist/anywhere/at/all")
    assert _resolve_startup_path(fully_vanished) == Path.home()


@pytest.mark.asyncio
async def test_restart_restores_path_sort_view_hidden(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.txt").touch()
    (content_dir / ".hidden").touch()

    app1 = MyComApp()
    async with app1.run_test() as pilot:
        app1.active_panel.navigate_to(content_dir)
        await pilot.pause()
        await pilot.press("ctrl+f6")  # sort by size
        await pilot.press("ctrl+3")  # Wide view
        await pilot.press("ctrl+h")  # show hidden
        await pilot.pause()
        app1._flush_state()  # force a synchronous write instead of waiting on the debounce timer

    app2 = MyComApp()
    async with app2.run_test():
        assert app2.active_panel.current_path == content_dir
        assert app2.active_panel.sort_field == "size"
        assert app2.active_panel.view_mode.value == "wide"
        assert app2._show_hidden is True


@pytest.mark.asyncio
async def test_restart_restores_both_panels_independently(tmp_path):
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()

    app1 = MyComApp()
    async with app1.run_test() as pilot:
        app1.active_panel.navigate_to(left_dir)
        app1.inactive_panel.navigate_to(right_dir)
        await pilot.pause()
        app1._flush_state()

    app2 = MyComApp()
    async with app2.run_test():
        assert app2._left_panel.current_path == left_dir
        assert app2._right_panel.current_path == right_dir


@pytest.mark.asyncio
async def test_restart_restores_active_side_and_resize(tmp_path):
    app1 = MyComApp()
    async with app1.run_test() as pilot:
        await pilot.press("tab")  # switch active side to "right"
        await pilot.press("ctrl+right")  # grow (resize_index changes)
        await pilot.pause()
        assert app1._active_side == "right"
        app1._flush_state()

    app2 = MyComApp()
    async with app2.run_test():
        assert app2._active_side == "right"
        assert app2._resize_index == app1._resize_index


@pytest.mark.asyncio
async def test_vanished_saved_path_falls_back_to_ancestor(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    app1 = MyComApp()
    async with app1.run_test() as pilot:
        app1.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app1._flush_state()

    content_dir.rmdir()  # the saved path no longer exists

    app2 = MyComApp()
    async with app2.run_test():
        assert app2.active_panel.current_path == tmp_path


@pytest.mark.asyncio
async def test_deleting_state_db_yields_clean_defaults(tmp_path):
    from mycom.state import DEFAULT_DB_PATH

    app1 = MyComApp()
    async with app1.run_test() as pilot:
        app1.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app1._flush_state()

    DEFAULT_DB_PATH.unlink()

    app2 = MyComApp()
    async with app2.run_test():
        assert app2.active_panel.current_path == Path.cwd()  # clean config-driven default


@pytest.mark.asyncio
async def test_state_survives_without_a_clean_shutdown(tmp_path):
    """Simulates kill-9: no action_quit call, no final flush — only whatever
    debounced save already landed. The DB must still open cleanly next time."""
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    app1 = MyComApp()
    async with app1.run_test() as pilot:
        app1.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app1._flush_state()  # a save that DID land before the simulated crash
    # No action_quit() — simulates an unclean exit.

    app2 = MyComApp()
    async with app2.run_test():
        assert app2.active_panel.current_path == content_dir


@pytest.mark.asyncio
async def test_quit_does_not_crash_when_the_final_save_fails(tmp_path, monkeypatch):
    """Code review #3: a write failure in the final flush (locked DB, full
    disk, read-only FS, ...) must not crash action_quit — quitting must
    always succeed even if the last save doesn't."""
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()

        def boom(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(app._state_db, "save_panel_state", boom)

        await app.action_quit()  # must not raise
        assert app._exit
