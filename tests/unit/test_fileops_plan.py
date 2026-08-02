"""Tests for mycom.fileops.plan."""

from __future__ import annotations

from pathlib import Path

from mycom.fileops.plan import build_delete_plan, build_plan, path_contains


def test_build_plan_mixed_tree_counts_bytes_and_files(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"12345")
    nested = src / "nested"
    nested.mkdir()
    (nested / "b.txt").write_bytes(b"1234567890")
    (nested / "link.txt").symlink_to(src / "a.txt")

    dest = tmp_path / "dest"
    dest.mkdir()

    plan = build_plan([src], dest)

    assert plan.total_bytes == 15
    assert plan.total_files == 2  # dirs and symlinks don't count

    by_src = {str(e.src): e for e in plan.entries}
    assert by_src[str(src)].is_dir is True
    assert by_src[str(nested)].is_dir is True
    assert by_src[str(nested / "link.txt")].is_symlink is True
    assert by_src[str(nested / "link.txt")].dst == dest / "src" / "nested" / "link.txt"

    # directory entries precede their children
    order = [str(e.src) for e in plan.entries]
    assert order.index(str(src)) < order.index(str(nested))
    assert order.index(str(nested)) < order.index(str(nested / "b.txt"))


def test_build_plan_single_file(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_bytes(b"hello")
    dest = tmp_path / "dest"
    dest.mkdir()

    plan = build_plan([src], dest)

    assert len(plan.entries) == 1
    entry = plan.entries[0]
    assert entry.src == src
    assert entry.dst == dest / "a.txt"
    assert entry.size == 5
    assert entry.is_dir is False
    assert entry.is_symlink is False


def test_build_plan_does_not_follow_symlinked_directory(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "inside.txt").write_bytes(b"x")
    link = tmp_path / "link_to_real"
    link.symlink_to(real_dir)

    dest = tmp_path / "dest"
    dest.mkdir()

    plan = build_plan([link], dest)

    assert len(plan.entries) == 1
    assert plan.entries[0].is_symlink is True
    assert plan.entries[0].is_dir is False


def test_build_delete_plan_dst_mirrors_src(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"x")

    plan = build_delete_plan([src])

    for entry in plan.entries:
        assert entry.dst == entry.src


def test_path_contains_self_and_descendant(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()
    sibling = tmp_path / "sibling"
    sibling.mkdir()

    assert path_contains(parent, parent) is True
    assert path_contains(parent, child) is True
    assert path_contains(parent, sibling) is False
    assert path_contains(child, parent) is False
