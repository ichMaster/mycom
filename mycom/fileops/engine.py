"""Copy/move/delete execution engine: walks an OpPlan, applying an injected
conflict policy and reporting progress. No Textual dependency — a worker
thread drives this synchronously; the caller marshals OpProgress back to the
UI thread.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Event

from mycom.fileops.plan import OpPlan, PlanEntry
from mycom.fileops.policy import ConflictChoice, ConflictPolicy

DEFAULT_CHUNK_SIZE = 1 << 20  # 1 MiB


class OperationCancelledError(Exception):
    """Raised internally when a CancelToken is set mid-copy; caught by execute_plan."""


class ConflictTypeMismatchError(Exception):
    """A file exists where a directory is planned, or vice versa. Never offered
    the six-choice resolution — the caller shows a plain error instead."""

    def __init__(self, entry: PlanEntry) -> None:
        self.entry = entry
        super().__init__(f"type mismatch at destination: {entry.dst}")


class CancelToken:
    """Thin wrapper over threading.Event — a worker checks it between chunks."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class OpProgress:
    current_file: str
    bytes_done: int
    bytes_total: int
    files_done: int
    files_total: int
    speed_bps: float
    eta_seconds: float | None


@dataclass(frozen=True)
class ExecutionResult:
    completed: tuple[PlanEntry, ...]
    skipped: tuple[PlanEntry, ...]
    cancelled: bool


def copy_entry(entry: PlanEntry, cancel: CancelToken, chunk_size: int = DEFAULT_CHUNK_SIZE) -> None:
    """Copy one plan entry (file, dir, or symlink) from src to dst.

    Directories are created, not recursed — the plan already lists their
    contents as separate entries. Symlinks are recreated as symlinks, never
    followed/dereferenced. Regular files are copied in chunks, checking
    `cancel` between each — the chunk boundary is the cancellation guarantee.
    """
    if entry.is_symlink:
        target = os.readlink(entry.src)
        if os.path.lexists(entry.dst):
            os.unlink(entry.dst)
        os.symlink(target, entry.dst)
        return
    if entry.is_dir:
        os.makedirs(entry.dst, exist_ok=True)
        shutil.copystat(entry.src, entry.dst)
        return
    if entry.src.resolve() == entry.dst.resolve():
        # Opening dst in "wb" mode truncates it before a single byte is
        # read — if src and dst are the same file, that destroys the source.
        raise shutil.SameFileError(f"{entry.src} and {entry.dst} are the same file")
    entry.dst.parent.mkdir(parents=True, exist_ok=True)
    with open(entry.src, "rb") as fsrc, open(entry.dst, "wb") as fdst:
        while True:
            if cancel.is_cancelled():
                raise OperationCancelledError(str(entry.src))
            chunk = fsrc.read(chunk_size)
            if not chunk:
                break
            fdst.write(chunk)
    shutil.copystat(entry.src, entry.dst)


def same_filesystem(a: Path, b: Path) -> bool:
    """True if two paths live on the same filesystem. Compares `st_dev` of the
    nearest existing ancestor of each, since `b` may not exist yet."""
    return _device_of(a) == _device_of(b)


def _device_of(path: Path) -> int:
    candidate = path
    while not candidate.exists():
        candidate = candidate.parent
    return candidate.stat().st_dev


def move_entry(entry: PlanEntry, cancel: CancelToken, chunk_size: int = DEFAULT_CHUNK_SIZE) -> None:
    """Move one entry. Same-filesystem is an instant `rename()`. Cross-device
    is a verified copy-then-delete: the source is only removed after the
    destination is confirmed intact — never delete-before-copy. Directories
    are handled per-entry too; a cross-device directory's source is removed
    later, once all its (deeper-listed) children are gone — see
    `execute_move_plan`.
    """
    if entry.is_symlink:
        target = os.readlink(entry.src)
        if os.path.lexists(entry.dst):
            os.unlink(entry.dst)
        os.symlink(target, entry.dst)
        os.unlink(entry.src)
        return
    if entry.is_dir:
        if same_filesystem(entry.src, entry.dst.parent):
            entry.dst.parent.mkdir(parents=True, exist_ok=True)
            os.rename(entry.src, entry.dst)
        else:
            os.makedirs(entry.dst, exist_ok=True)
            shutil.copystat(entry.src, entry.dst)
        return
    if same_filesystem(entry.src, entry.dst.parent):
        entry.dst.parent.mkdir(parents=True, exist_ok=True)
        os.rename(entry.src, entry.dst)
        return
    copy_entry(entry, cancel, chunk_size)
    src_size = entry.src.stat().st_size
    dst_size = entry.dst.stat().st_size
    if src_size != dst_size:
        raise OSError(f"move verification failed: size mismatch for {entry.dst}")
    os.unlink(entry.src)


def delete_entry(entry: PlanEntry) -> None:
    """Delete one entry: unlink a file/symlink, rmdir an (already-emptied) directory."""
    if entry.is_dir:
        entry.src.rmdir()
    else:
        entry.src.unlink()


def _resolve_conflict(
    entry: PlanEntry,
    conflict_policy: ConflictPolicy,
    sticky: dict[str, ConflictChoice],
) -> tuple[ConflictChoice, Path]:
    """Ask the policy for one conflicting entry, or reuse a sticky ALL answer."""
    if "answer" in sticky:
        return sticky["answer"], entry.dst
    dst_stat = entry.dst.lstat()
    answer = conflict_policy(entry, dst_stat)
    choice, new_target = answer if isinstance(answer, tuple) else (answer, entry.dst)
    if choice is ConflictChoice.OVERWRITE_ALL:
        sticky["answer"] = ConflictChoice.OVERWRITE
        choice = ConflictChoice.OVERWRITE
    elif choice is ConflictChoice.SKIP_ALL:
        sticky["answer"] = ConflictChoice.SKIP
        choice = ConflictChoice.SKIP
    return choice, new_target


def _report(
    on_progress: Callable[[OpProgress], None],
    entry: PlanEntry,
    bytes_done: int,
    files_done: int,
    plan: OpPlan,
    start: float,
    clock: Callable[[], float],
) -> None:
    elapsed = clock() - start
    speed = bytes_done / elapsed if elapsed > 0 else 0.0
    remaining = plan.total_bytes - bytes_done
    eta = remaining / speed if speed > 0 else None
    on_progress(
        OpProgress(
            current_file=str(entry.src),
            bytes_done=bytes_done,
            bytes_total=plan.total_bytes,
            files_done=files_done,
            files_total=plan.total_files,
            speed_bps=speed,
            eta_seconds=eta,
        )
    )


def execute_plan(
    plan: OpPlan,
    cancel: CancelToken,
    conflict_policy: ConflictPolicy,
    on_progress: Callable[[OpProgress], None],
    *,
    perform: Callable[[PlanEntry, CancelToken], None] = copy_entry,
    clock: Callable[[], float] = time.monotonic,
) -> ExecutionResult:
    """Drive the per-entry loop: conflict-check, perform, report progress.

    Used directly for copy, and for move via `execute_move_plan` (which wraps
    it with `perform=move_entry` plus post-loop source-directory cleanup).
    """
    completed: list[PlanEntry] = []
    skipped: list[PlanEntry] = []
    sticky: dict[str, ConflictChoice] = {}
    bytes_done = 0
    files_done = 0
    start = clock()

    for entry in plan.entries:
        if cancel.is_cancelled():
            return ExecutionResult(tuple(completed), tuple(skipped), cancelled=True)

        target = entry
        if os.path.lexists(entry.dst):
            dst_is_dir = entry.dst.is_dir() and not os.path.islink(entry.dst)
            if entry.is_dir != dst_is_dir:
                raise ConflictTypeMismatchError(entry)
            if not entry.is_dir:
                choice, new_target = _resolve_conflict(entry, conflict_policy, sticky)
                if choice is ConflictChoice.CANCEL:
                    return ExecutionResult(tuple(completed), tuple(skipped), cancelled=True)
                if choice is ConflictChoice.SKIP:
                    skipped.append(entry)
                    continue
                if choice is ConflictChoice.RENAME:
                    target = PlanEntry(
                        entry.src, new_target, entry.is_dir, entry.is_symlink, entry.size
                    )
            # entry.is_dir and dst_is_dir: a directory-over-directory merge —
            # not a conflict, fall through to perform() (idempotent makedirs).

        try:
            perform(target, cancel)
        except OperationCancelledError:
            return ExecutionResult(tuple(completed), tuple(skipped), cancelled=True)

        completed.append(target)
        if not target.is_dir:
            files_done += 1
            bytes_done += target.size
        _report(on_progress, target, bytes_done, files_done, plan, start, clock)

    return ExecutionResult(tuple(completed), tuple(skipped), cancelled=False)


def execute_move_plan(
    plan: OpPlan,
    cancel: CancelToken,
    conflict_policy: ConflictPolicy,
    on_progress: Callable[[OpProgress], None],
    *,
    clock: Callable[[], float] = time.monotonic,
) -> ExecutionResult:
    """Move every entry (same-FS rename or cross-device copy-and-verified-
    delete), then remove now-empty cross-device source directories bottom-up.
    Same-filesystem directories are already gone — `rename()` moved them
    directly, so `entry.src` won't exist by the time cleanup runs.
    """
    result = execute_plan(
        plan, cancel, conflict_policy, on_progress, perform=move_entry, clock=clock
    )
    if not result.cancelled:
        for entry in reversed(result.completed):
            if entry.is_dir and entry.src.exists():
                # rmdir silently no-ops via suppress when not empty — a child was
                # skipped (conflict SKIP) rather than moved. Leaving the source
                # dir behind in that case is correct: no data loss.
                with contextlib.suppress(OSError):
                    entry.src.rmdir()
    return result


def execute_delete_plan(
    plan: OpPlan,
    cancel: CancelToken,
    on_progress: Callable[[OpProgress], None],
    *,
    clock: Callable[[], float] = time.monotonic,
) -> ExecutionResult:
    """Delete every entry in `plan`, deepest-first (files and leaf symlinks
    before the directories that contain them) so `rmdir` always finds an
    empty directory. No conflict policy — delete has nothing to conflict with.

    A directory that turns out non-empty (a caller excluded one of its
    children — e.g. a declined read-only-file prompt) is left in place
    rather than raising: no data loss, the excluded child is exactly why
    it's non-empty.
    """
    completed: list[PlanEntry] = []
    bytes_done = 0
    files_done = 0
    start = clock()

    for entry in reversed(plan.entries):
        if cancel.is_cancelled():
            return ExecutionResult(tuple(completed), (), cancelled=True)
        if entry.is_dir:
            try:
                delete_entry(entry)
            except OSError:
                continue
        else:
            delete_entry(entry)
        completed.append(entry)
        if not entry.is_dir:
            files_done += 1
            bytes_done += entry.size
        _report(on_progress, entry, bytes_done, files_done, plan, start, clock)

    return ExecutionResult(tuple(completed), (), cancelled=False)
