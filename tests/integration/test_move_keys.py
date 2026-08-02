"""Pilot-driven integration tests for MC-028: Move (F6)."""

from __future__ import annotations

import asyncio
import time

import pytest

from mycom.app import MyComApp
from tests.integration.test_copy_keys import _wait_until


@pytest.mark.asyncio
async def test_f6_same_filesystem_move_is_instant_no_progress_dialog(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"hello world")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("enter")  # confirm the pre-filled target (dst_dir)
        await pilot.pause()

        # No progress dialog for a same-filesystem move — should already be
        # back to just the default screen.
        assert len(app.screen_stack) == 1

    assert (dst_dir / "a.txt").read_bytes() == b"hello world"
    assert not (src_dir / "a.txt").exists()  # moved, not copied


@pytest.mark.asyncio
async def test_f6_deselects_and_refreshes_both_panels(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"a")
    (src_dir / "b.txt").write_bytes(b"b")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.selected_names == frozenset()
        assert {e.name for e in app.active_panel._entries} == set()
        assert {e.name for e in app.inactive_panel._entries} == {"a.txt", "b.txt"}


@pytest.mark.asyncio
async def test_f6_refuses_move_into_own_subdirectory(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "nested").mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        app.inactive_panel.navigate_to(src_dir / "nested")
        await pilot.pause()
        app.active_panel.file_list.select_by_name("src")
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert len(app.screen_stack) == 2  # the ErrorDialog, no I/O started
        assert src_dir.exists()
        assert not (src_dir / "nested" / "src").exists()


@pytest.mark.asyncio
async def test_f6_conflict_uses_the_same_conflict_dialog_as_copy(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"new-content")
    (dst_dir / "a.txt").write_bytes(b"old-content")

    app = MyComApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 2)  # ConflictDialog only
        assert app.screen_stack[-1].__class__.__name__ == "ConflictDialog"
        await pilot.click("#overwrite")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert (dst_dir / "a.txt").read_bytes() == b"new-content"
    assert not (src_dir / "a.txt").exists()


@pytest.mark.asyncio
async def test_f6_cross_device_move_shows_progress_and_verifies_before_delete(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("mycom.app.same_filesystem", lambda a, b: False)

    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"cross device content")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("enter")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1, timeout=10.0)

    assert (dst_dir / "a.txt").read_bytes() == b"cross device content"
    assert not (src_dir / "a.txt").exists()


@pytest.mark.asyncio
async def test_f6_cross_device_move_cancellation_leaves_source_intact(tmp_path, monkeypatch):
    """Cross-device move is copy + verified delete — cancelling mid-copy
    must never delete the (not-yet-fully-copied) source."""
    monkeypatch.setattr("mycom.app.same_filesystem", lambda a, b: False)

    import mycom.app as app_module

    real_execute_move_plan = app_module.execute_move_plan

    def delayed_execute_move_plan(plan, cancel, conflict_policy, on_progress, **kwargs):
        def slow_on_progress(progress):
            time.sleep(0.03)
            on_progress(progress)

        return real_execute_move_plan(plan, cancel, conflict_policy, slow_on_progress, **kwargs)

    monkeypatch.setattr(app_module, "execute_move_plan", delayed_execute_move_plan)

    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    originals = {}
    for i in range(20):
        name = f"f{i:02d}.bin"
        data = bytes([i]) * 1000
        (src_dir / name).write_bytes(data)
        originals[name] = data

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 2)
        await asyncio.sleep(0.1)
        await pilot.click("#cancel")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1, timeout=10.0)

    # A cancelled cross-device move legitimately deletes source files it has
    # already verified-copied — the real safety invariant is "never lost":
    # each file ends up exactly once, either still in source or fully moved.
    for name, data in originals.items():
        src_file, dst_file = src_dir / name, dst_dir / name
        if src_file.exists():
            assert src_file.read_bytes() == data
            assert not dst_file.exists()
        else:
            assert dst_file.read_bytes() == data
    assert len(list(dst_dir.iterdir())) < 20  # cancelled before finishing all of them


@pytest.mark.asyncio
async def test_f6_unexpected_os_error_shows_error_dialog_not_a_crash(tmp_path, monkeypatch):
    """See test_copy_keys.py's equivalent — code review v0.4 #1."""
    import mycom.app as app_module

    def raising_execute_move_plan(plan, cancel, conflict_policy, on_progress, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(app_module, "execute_move_plan", raising_execute_move_plan)
    monkeypatch.setattr("mycom.app.same_filesystem", lambda a, b: False)  # force a progress dialog

    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"x")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("enter")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 2)

        assert app.screen_stack[-1].__class__.__name__ == "ErrorDialog"
        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1  # app is still alive and responsive
