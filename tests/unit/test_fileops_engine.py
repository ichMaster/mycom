"""Tests for mycom.fileops.engine: copy correctness, cancellation, conflicts."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from mycom.fileops.engine import (
    CancelToken,
    ConflictTypeMismatchError,
    copy_entry,
    execute_delete_plan,
    execute_move_plan,
    execute_plan,
    move_entry,
    same_filesystem,
)
from mycom.fileops.plan import OpPlan, PlanEntry, build_delete_plan, build_plan
from mycom.fileops.policy import ConflictChoice


def _fake_clock():
    ticks = iter(range(0, 10_000))

    def clock() -> float:
        return next(ticks)

    return clock


def test_copy_entry_preserves_content_and_mtime(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_bytes(b"hello world" * 100)
    os.utime(src, (1000, 123456))
    dst = tmp_path / "dest" / "a.txt"
    dst.parent.mkdir()

    plan = build_plan([src], dst.parent)
    entry = plan.entries[0]
    copy_entry(entry, CancelToken())

    assert dst.read_bytes() == src.read_bytes()
    assert dst.stat().st_mtime == pytest.approx(src.stat().st_mtime)


def test_copy_entry_recreates_symlink_without_following(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_bytes(b"x")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    plan = build_plan([link], dest_dir)
    copy_entry(plan.entries[0], CancelToken())

    copied = dest_dir / "link.txt"
    assert copied.is_symlink()
    assert os.readlink(copied) == str(target)


def test_copy_entry_refuses_to_copy_a_file_onto_itself(tmp_path: Path) -> None:
    """Opening dst in "wb" mode truncates it first — if src and dst resolve
    to the same file, that would destroy the source before any byte is read."""
    src = tmp_path / "a.txt"
    src.write_bytes(b"precious data")
    entry = PlanEntry(src=src, dst=src, is_dir=False, is_symlink=False, size=13)

    with pytest.raises(shutil.SameFileError):
        copy_entry(entry, CancelToken())

    assert src.read_bytes() == b"precious data"


def test_execute_plan_reports_monotonic_progress(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    for i in range(3):
        (src / f"f{i}.txt").write_bytes(b"x" * 10)
    dest = tmp_path / "dest"
    dest.mkdir()

    plan = build_plan([src], dest)
    progress_log = []

    def on_progress(p):
        progress_log.append((p.bytes_done, p.files_done))

    def deny_conflict(entry, stat):
        raise AssertionError("no conflicts expected")

    result = execute_plan(plan, CancelToken(), deny_conflict, on_progress, clock=_fake_clock())

    assert result.cancelled is False
    assert [b for b, _ in progress_log] == sorted(b for b, _ in progress_log)
    assert progress_log[-1] == (30, 3)


def test_execute_plan_cancellation_mid_tree_leaves_files_intact(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"A" * 10)
    (src / "b.txt").write_bytes(b"B" * 10)
    (src / "c.txt").write_bytes(b"C" * 10)
    dest = tmp_path / "dest"
    dest.mkdir()

    plan = build_plan([src], dest)
    cancel = CancelToken()
    completed_count = 0

    def on_progress(p):
        nonlocal completed_count
        completed_count += 1
        if completed_count == 2:
            cancel.cancel()

    def deny_conflict(entry, stat):
        raise AssertionError("no conflicts expected")

    result = execute_plan(plan, cancel, deny_conflict, on_progress)

    assert result.cancelled is True
    for entry in result.completed:
        if not entry.is_dir:
            assert entry.dst.read_bytes() == entry.src.read_bytes()
    assert (src / "a.txt").exists()
    assert (src / "b.txt").exists()
    assert (src / "c.txt").exists()


@pytest.mark.parametrize(
    "choice",
    [ConflictChoice.OVERWRITE, ConflictChoice.SKIP, ConflictChoice.CANCEL],
)
def test_execute_plan_honors_conflict_choice(tmp_path: Path, choice: ConflictChoice) -> None:
    src = tmp_path / "a.txt"
    src.write_bytes(b"new")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "a.txt").write_bytes(b"old")

    plan = build_plan([src], dest)
    result = execute_plan(plan, CancelToken(), lambda entry, stat: choice, lambda p: None)

    if choice is ConflictChoice.OVERWRITE:
        assert (dest / "a.txt").read_bytes() == b"new"
        assert result.cancelled is False
        assert len(result.completed) == 1
    elif choice is ConflictChoice.SKIP:
        assert (dest / "a.txt").read_bytes() == b"old"
        assert result.skipped == plan.entries
        assert result.cancelled is False
    else:
        assert (dest / "a.txt").read_bytes() == b"old"
        assert result.cancelled is True


def test_execute_plan_rename_choice_uses_new_target(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_bytes(b"new")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "a.txt").write_bytes(b"old")
    renamed = dest / "a (2).txt"

    def policy(entry, stat):
        return ConflictChoice.RENAME, renamed

    plan = build_plan([src], dest)
    result = execute_plan(plan, CancelToken(), policy, lambda p: None)

    assert renamed.read_bytes() == b"new"
    assert (dest / "a.txt").read_bytes() == b"old"
    assert result.completed[0].dst == renamed


def test_execute_plan_directory_over_directory_merges(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "new.txt").write_bytes(b"n")
    dest = tmp_path / "dest"
    existing = dest / "src"
    existing.mkdir(parents=True)
    (existing / "old.txt").write_bytes(b"o")

    plan = build_plan([src], dest)

    def deny_conflict(entry, stat):
        raise AssertionError("directory-over-directory must not be treated as a conflict")

    result = execute_plan(plan, CancelToken(), deny_conflict, lambda p: None)

    assert result.cancelled is False
    assert (existing / "new.txt").read_bytes() == b"n"
    assert (existing / "old.txt").read_bytes() == b"o"


def test_execute_plan_file_over_directory_raises_type_mismatch(tmp_path: Path) -> None:
    src = tmp_path / "a"
    src.mkdir()
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "a").write_bytes(b"i am a file")

    plan = build_plan([src], dest)

    with pytest.raises(ConflictTypeMismatchError):
        execute_plan(plan, CancelToken(), lambda e, s: ConflictChoice.CANCEL, lambda p: None)


def test_same_filesystem_true_for_same_device(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    assert same_filesystem(a, b) is True


def test_same_filesystem_uses_nearest_existing_ancestor(monkeypatch, tmp_path: Path) -> None:
    devices = {str(tmp_path): 1}

    class FakeStat:
        def __init__(self, dev):
            self.st_dev = dev

    real_stat = Path.stat

    def fake_stat(self, *a, **kw):
        if str(self) in devices:
            return FakeStat(devices[str(self)])
        return real_stat(self, *a, **kw)

    monkeypatch.setattr(Path, "stat", fake_stat)
    other = tmp_path.parent / "elsewhere-does-not-exist" / "sub"
    devices[str(tmp_path.parent)] = 2
    assert same_filesystem(tmp_path, other) is False


def test_move_entry_same_filesystem_is_rename(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_bytes(b"x")
    dest = tmp_path / "dest"
    dest.mkdir()
    plan = build_plan([src], dest)

    move_entry(plan.entries[0], CancelToken())

    assert not src.exists()
    assert (dest / "a.txt").read_bytes() == b"x"


def test_move_entry_cross_device_verifies_before_deleting_source(
    monkeypatch, tmp_path: Path
) -> None:
    src = tmp_path / "a.txt"
    src.write_bytes(b"x" * 100)
    dest = tmp_path / "dest"
    dest.mkdir()
    plan = build_plan([src], dest)
    entry = plan.entries[0]

    monkeypatch.setattr("mycom.fileops.engine.same_filesystem", lambda a, b: False)

    move_entry(entry, CancelToken())

    assert not src.exists()
    assert (dest / "a.txt").read_bytes() == b"x" * 100


def test_move_entry_cross_device_leaves_source_when_verification_fails(
    monkeypatch, tmp_path: Path
) -> None:
    src = tmp_path / "a.txt"
    src.write_bytes(b"x" * 100)
    dest = tmp_path / "dest"
    dest.mkdir()
    plan = build_plan([src], dest)
    entry = plan.entries[0]

    monkeypatch.setattr("mycom.fileops.engine.same_filesystem", lambda a, b: False)

    def fake_copy(e, cancel, chunk_size=1 << 20):
        e.dst.write_bytes(b"short")  # simulates a truncated/corrupt copy

    monkeypatch.setattr("mycom.fileops.engine.copy_entry", fake_copy)

    with pytest.raises(OSError):
        move_entry(entry, CancelToken())

    assert src.exists()
    assert src.read_bytes() == b"x" * 100


def test_execute_move_plan_cross_device_removes_emptied_source_dirs(
    monkeypatch, tmp_path: Path
) -> None:
    src = tmp_path / "src"
    nested = src / "nested"
    nested.mkdir(parents=True)
    (nested / "f.txt").write_bytes(b"data")
    dest = tmp_path / "dest"
    dest.mkdir()

    monkeypatch.setattr("mycom.fileops.engine.same_filesystem", lambda a, b: False)

    plan = build_plan([src], dest)
    def deny_conflict(entry, stat):
        raise AssertionError("no conflicts expected")

    result = execute_move_plan(plan, CancelToken(), deny_conflict, lambda p: None)

    assert result.cancelled is False
    assert not src.exists()
    assert (dest / "src" / "nested" / "f.txt").read_bytes() == b"data"


def test_execute_move_plan_cross_device_keeps_source_dir_with_skipped_child(
    monkeypatch, tmp_path: Path
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "keep.txt").write_bytes(b"data")
    dest = tmp_path / "dest"
    existing = dest / "src"
    existing.mkdir(parents=True)
    (existing / "keep.txt").write_bytes(b"already there")

    monkeypatch.setattr("mycom.fileops.engine.same_filesystem", lambda a, b: False)

    plan = build_plan([src], dest)
    def always_skip(entry, stat):
        return ConflictChoice.SKIP

    result = execute_move_plan(plan, CancelToken(), always_skip, lambda p: None)

    assert result.cancelled is False
    assert src.exists()  # not empty — the skipped file is still there
    assert (src / "keep.txt").read_bytes() == b"data"


def test_execute_delete_plan_removes_files_then_dirs(tmp_path: Path) -> None:
    root = tmp_path / "root"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (nested / "f.txt").write_bytes(b"x" * 5)
    (root / "top.txt").write_bytes(b"y" * 3)

    plan = build_delete_plan([root])
    result = execute_delete_plan(plan, CancelToken(), lambda p: None)

    assert result.cancelled is False
    assert not root.exists()
    assert result.completed[-1].src == root  # the root dir is removed last


def test_execute_delete_plan_leaves_nonempty_dir_when_a_child_was_excluded(tmp_path: Path) -> None:
    """A caller can exclude specific entries from a plan (e.g. a declined
    read-only-file prompt) before executing it — the containing directory's
    rmdir then legitimately fails (not empty). That must not crash the rest
    of the delete or raise: no data loss, the excluded child is exactly why
    it's non-empty."""
    root = tmp_path / "root"
    root.mkdir()
    (root / "excluded.txt").write_bytes(b"keep me")
    (root / "other.txt").write_bytes(b"delete me")
    other_root = tmp_path / "other_root"
    other_root.mkdir()

    full_plan = build_delete_plan([root, other_root])
    entries = tuple(e for e in full_plan.entries if e.src.name != "excluded.txt")
    plan = OpPlan(entries, full_plan.total_bytes - 7, full_plan.total_files - 1)

    result = execute_delete_plan(plan, CancelToken(), lambda p: None)

    assert result.cancelled is False
    assert root.exists()  # left behind — still contains excluded.txt
    assert (root / "excluded.txt").read_bytes() == b"keep me"
    assert not (root / "other.txt").exists()
    assert not other_root.exists()  # unrelated dir still removed normally


def test_execute_delete_plan_cancellation_leaves_remainder_intact(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_bytes(b"a")
    (root / "b.txt").write_bytes(b"b")

    plan = build_delete_plan([root])
    cancel = CancelToken()
    seen = 0

    def on_progress(p):
        nonlocal seen
        seen += 1
        if seen == 1:
            cancel.cancel()

    result = execute_delete_plan(plan, cancel, on_progress)

    assert result.cancelled is True
    assert root.exists()
    assert (root / "a.txt").exists()
