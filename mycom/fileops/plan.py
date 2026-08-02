"""Plan builder: walks source paths into a flat, ready-to-execute entry list."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlanEntry:
    """One file, directory, or symlink to process, with its resolved destination."""

    src: Path
    dst: Path
    is_dir: bool
    is_symlink: bool
    size: int


@dataclass(frozen=True)
class OpPlan:
    """A walked, ready-to-execute set of entries."""

    entries: tuple[PlanEntry, ...]
    total_bytes: int
    total_files: int


def build_plan(sources: list[Path], dest_dir: Path) -> OpPlan:
    """Walk each source into a flat list of PlanEntry for a copy/move.

    A lone file becomes one entry. A directory recurses, preserving its
    subtree under ``dest_dir/source.name/...``. Symlinks are recorded as leaf
    entries and never followed/recursed into. Directory entries always
    precede the entries nested inside them, so execute_plan can create
    parents before children.
    """
    return _build(sources, lambda src: dest_dir / src.name)


def build_delete_plan(sources: list[Path]) -> OpPlan:
    """Walk each source for deletion. `dst` mirrors `src` — delete_entry only
    reads `.src`/`.is_dir`/`.is_symlink`, never `.dst`."""
    return _build(sources, lambda src: src)


def path_contains(container: Path, path: Path) -> bool:
    """True if `path` is `container` itself or nested inside it (both resolved)."""
    container = container.resolve()
    path = path.resolve()
    return path == container or container in path.parents


def _build(sources: list[Path], dst_of: Callable[[Path], Path]) -> OpPlan:
    entries: list[PlanEntry] = []
    total_bytes = 0
    total_files = 0
    for source in sources:
        dst = dst_of(source)
        if os.path.islink(source):
            entries.append(PlanEntry(source, dst, False, True, 0))
            continue
        if source.is_dir():
            entries.append(PlanEntry(source, dst, True, False, 0))
            sub_bytes, sub_files, sub_entries = _walk_dir(source, dst)
            entries.extend(sub_entries)
            total_bytes += sub_bytes
            total_files += sub_files
        else:
            size = source.stat().st_size
            entries.append(PlanEntry(source, dst, False, False, size))
            total_bytes += size
            total_files += 1
    return OpPlan(tuple(entries), total_bytes, total_files)


def _walk_dir(src_dir: Path, dst_dir: Path) -> tuple[int, int, list[PlanEntry]]:
    entries: list[PlanEntry] = []
    total_bytes = 0
    total_files = 0
    for item in sorted(src_dir.iterdir()):
        dst = dst_dir / item.name
        if os.path.islink(item):
            entries.append(PlanEntry(item, dst, False, True, 0))
            continue
        if item.is_dir():
            entries.append(PlanEntry(item, dst, True, False, 0))
            sub_bytes, sub_files, sub_entries = _walk_dir(item, dst)
            entries.extend(sub_entries)
            total_bytes += sub_bytes
            total_files += sub_files
        else:
            size = item.stat().st_size
            entries.append(PlanEntry(item, dst, False, False, size))
            total_bytes += size
            total_files += 1
    return total_bytes, total_files, entries
