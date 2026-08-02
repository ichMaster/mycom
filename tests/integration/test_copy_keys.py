"""Pilot-driven integration tests for MC-027: Copy (F5)."""

from __future__ import annotations

import asyncio
import os
import time

import pytest

from mycom.app import MyComApp


async def _wait_until(pilot, predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        await pilot.pause()
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition not met within timeout")


@pytest.mark.asyncio
async def test_f5_copies_single_selected_file_to_passive_panel_dir(tmp_path):
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

        await pilot.press("f5")
        await pilot.pause()
        assert len(app.screen_stack) == 2  # the target InputDialog

        await pilot.press("enter")  # confirm the pre-filled target (dst_dir)
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

        assert (dst_dir / "a.txt").read_bytes() == b"hello world"
        assert (src_dir / "a.txt").exists()  # copy, not move
        assert app.inactive_panel.current_path == dst_dir
        assert "a.txt" in {e.name for e in app.inactive_panel._entries}


@pytest.mark.asyncio
async def test_f5_copies_multi_selection(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"a")
    (src_dir / "b.txt").write_bytes(b"b")
    (src_dir / "c.txt").write_bytes(b"c")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

        assert {p.name for p in dst_dir.iterdir()} == {"a.txt", "b.txt", "c.txt"}
        # deselected on success (v0.3 deselect-on-success contract)
        assert app.active_panel.selected_names == frozenset()


@pytest.mark.asyncio
async def test_f5_nothing_selected_on_dotdot_is_noop(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        await pilot.pause()
        await pilot.press("f5")
        await pilot.pause()
        assert len(app.screen_stack) == 1  # no dialog opened


@pytest.mark.asyncio
async def test_f5_refuses_copy_into_own_subdirectory(tmp_path):
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

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")  # confirm target = src/nested (inside src itself)
        await pilot.pause()

        assert len(app.screen_stack) == 2  # the ErrorDialog, no I/O started
        assert not (src_dir / "nested" / "src").exists()


@pytest.mark.asyncio
async def test_f5_refuses_copy_onto_itself_same_directory(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"original")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(src_dir)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")  # target defaults to src_dir itself
        await pilot.pause()

        assert len(app.screen_stack) == 2  # ErrorDialog
        assert (src_dir / "a.txt").read_bytes() == b"original"


@pytest.mark.asyncio
async def test_f5_conflict_choices_overwrite_skip_rename_and_sticky_overwrite_all(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()

    (src_dir / "bulk1.txt").write_bytes(b"new-bulk1")
    (src_dir / "bulk2.txt").write_bytes(b"new-bulk2")
    (src_dir / "a_keep.txt").write_bytes(b"new-keep")
    (src_dir / "no_conflict.txt").write_bytes(b"new-renamed")
    (src_dir / "b_replace.txt").write_bytes(b"new-replace")

    (dst_dir / "bulk1.txt").write_bytes(b"old-bulk1")
    (dst_dir / "bulk2.txt").write_bytes(b"old-bulk2")
    (dst_dir / "a_keep.txt").write_bytes(b"old-keep")
    (dst_dir / "b_replace.txt").write_bytes(b"old-replace")

    app = MyComApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        # Plan order is alphabetical: a_keep, b_replace, bulk1, bulk2,
        # no_conflict (no dialog). "All" must come LAST — it consumes every
        # remaining conflict for the rest of the operation (by design), so
        # individually-answered conflicts have to precede it.
        await _wait_until(pilot, lambda: len(app.screen_stack) == 3)  # progress + conflict
        await pilot.click("#skip")  # a_keep.txt

        await _wait_until(pilot, lambda: len(app.screen_stack) == 3)
        await pilot.click("#overwrite")  # b_replace.txt

        await _wait_until(pilot, lambda: len(app.screen_stack) == 3)
        await pilot.click("#overwrite_all")  # bulk1 -> propagates to bulk2 too

        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert (dst_dir / "a_keep.txt").read_bytes() == b"old-keep"  # skipped
    assert (dst_dir / "b_replace.txt").read_bytes() == b"new-replace"  # overwritten
    assert (dst_dir / "bulk1.txt").read_bytes() == b"new-bulk1"
    assert (dst_dir / "bulk2.txt").read_bytes() == b"new-bulk2"  # sticky ALL, no 2nd dialog
    assert (dst_dir / "no_conflict.txt").read_bytes() == b"new-renamed"  # no conflict


@pytest.mark.asyncio
async def test_f5_conflict_rename_choice(tmp_path):
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

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 3)
        await pilot.click("#rename")
        await pilot.pause()
        input_widget = app.screen.query_one("#rename-input")
        input_widget.value = "a-renamed.txt"
        await pilot.click("#rename_ok")

        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert (dst_dir / "a.txt").read_bytes() == b"old-content"
    assert (dst_dir / "a-renamed.txt").read_bytes() == b"new-content"


@pytest.mark.asyncio
async def test_f5_conflict_sticky_skip_all(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "one.txt").write_bytes(b"new-one")
    (src_dir / "two.txt").write_bytes(b"new-two")
    (dst_dir / "one.txt").write_bytes(b"old-one")
    (dst_dir / "two.txt").write_bytes(b"old-two")

    app = MyComApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 3)
        await pilot.click("#skip_all")

        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert (dst_dir / "one.txt").read_bytes() == b"old-one"
    assert (dst_dir / "two.txt").read_bytes() == b"old-two"  # sticky, no 2nd dialog


@pytest.mark.asyncio
async def test_f5_conflict_cancel_stops_the_whole_operation(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    (src_dir / "one.txt").write_bytes(b"new-one")
    (src_dir / "two.txt").write_bytes(b"new-two")
    (dst_dir / "one.txt").write_bytes(b"old-one")

    app = MyComApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 3)
        await pilot.click("#cancel")

        await _wait_until(pilot, lambda: len(app.screen_stack) == 1)

    assert (dst_dir / "one.txt").read_bytes() == b"old-one"  # untouched
    assert not (dst_dir / "two.txt").exists()  # never reached


@pytest.mark.asyncio
async def test_f5_cancel_button_mid_copy_leaves_source_intact(tmp_path, monkeypatch):
    """Raw I/O on tmpfs is fast enough that a modest tree can finish before
    the test ever observes it "in progress" — racing real throughput would
    make this test flaky. Instead, wrap execute_plan with a small per-file
    delay (mycom.app calls it by module-global name each time, so patching
    mycom.app.execute_plan is a clean, reliable seam) to guarantee a stable
    window to click Cancel mid-operation, independent of hardware speed."""
    import mycom.app as app_module

    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    originals = {}
    for i in range(20):
        name = f"f{i:02d}.bin"
        data = os.urandom(1000)
        (src_dir / name).write_bytes(data)
        originals[name] = data

    real_execute_plan = app_module.execute_plan

    def delayed_execute_plan(plan, cancel, conflict_policy, on_progress, **kwargs):
        def slow_on_progress(progress):
            time.sleep(0.03)
            on_progress(progress)

        return real_execute_plan(plan, cancel, conflict_policy, slow_on_progress, **kwargs)

    monkeypatch.setattr(app_module, "execute_plan", delayed_execute_plan)

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(src_dir)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        await pilot.pause()

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        await _wait_until(pilot, lambda: len(app.screen_stack) == 2)
        await asyncio.sleep(0.1)  # let a few entries complete (30ms delay each)
        await pilot.click("#cancel")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1, timeout=10.0)

    for name, data in originals.items():
        assert (src_dir / name).read_bytes() == data
    copied = list(dst_dir.iterdir())
    assert len(copied) < 20  # cancelled before finishing


@pytest.mark.asyncio
async def test_f5_multi_file_copy_byte_identical_with_preserved_mtimes(tmp_path):
    """Stands in for the roadmap DoD's "1 GB tree" at a CI-practical scale —
    exercises the same chunked-copy/metadata-preservation code path as a
    literal 1 GB tree without the runtime/disk cost in automated tests."""
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()
    nested = src_dir / "nested"
    nested.mkdir()

    files = {}
    for i in range(5):
        name = f"big{i}.bin"
        data = os.urandom(2_000_000)
        path = src_dir / name
        path.write_bytes(data)
        os.utime(path, (1_700_000_000 + i, 1_700_000_000 + i))
        files[path] = data
    for i in range(3):
        name = f"nested{i}.bin"
        data = os.urandom(1_000_000)
        path = nested / name
        path.write_bytes(data)
        os.utime(path, (1_700_000_100 + i, 1_700_000_100 + i))
        files[path] = data

    total_bytes = sum(len(d) for d in files.values())

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        app.inactive_panel.navigate_to(dst_dir)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("src")
        await pilot.pause()

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 1, timeout=15.0)

    for src_path, data in files.items():
        rel = src_path.relative_to(tmp_path)
        dst_path = dst_dir / rel
        assert dst_path.read_bytes() == data
        assert dst_path.stat().st_mtime == pytest.approx(src_path.stat().st_mtime)
    copied_total = sum(p.stat().st_size for p in dst_dir.rglob("*") if p.is_file())
    assert copied_total == total_bytes


@pytest.mark.asyncio
async def test_f5_unexpected_os_error_shows_error_dialog_not_a_crash(tmp_path, monkeypatch):
    """A mid-batch OSError (permission denied, disk full, a vanished file, …)
    used to propagate out of the worker thread uncaught — Textual's
    run_worker defaults to exit_on_error=True, which tears down the whole
    app instead of showing a recoverable error (code review v0.4 #1)."""
    import mycom.app as app_module

    def raising_execute_plan(plan, cancel, conflict_policy, on_progress, **kwargs):
        raise OSError("Disk full")

    monkeypatch.setattr(app_module, "execute_plan", raising_execute_plan)

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

        await pilot.press("f5")
        await pilot.pause()
        await pilot.press("enter")
        await _wait_until(pilot, lambda: len(app.screen_stack) == 2)

        assert app.screen_stack[-1].__class__.__name__ == "ErrorDialog"
        await pilot.press("enter")
        await pilot.pause()
        assert len(app.screen_stack) == 1  # app is still alive and responsive
