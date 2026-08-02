"""File operations engine: plan -> execute pipeline for copy/move/delete.

An async worker walks a plan and executes it, reporting `OpProgress` to a
progress dialog and consulting an injected `ConflictPolicy` (the six-choice
dialog with sticky "All" answers) on collisions.
"""

from mycom.fileops.engine import (
    CancelToken,
    ConflictTypeMismatchError,
    ExecutionResult,
    OperationCancelledError,
    OpProgress,
    copy_entry,
    delete_entry,
    execute_delete_plan,
    execute_move_plan,
    execute_plan,
    move_entry,
    same_filesystem,
)
from mycom.fileops.plan import OpPlan, PlanEntry, build_delete_plan, build_plan, path_contains
from mycom.fileops.policy import ConflictAnswer, ConflictChoice, ConflictPolicy

__all__ = [
    "CancelToken",
    "ConflictAnswer",
    "ConflictChoice",
    "ConflictPolicy",
    "ConflictTypeMismatchError",
    "ExecutionResult",
    "OperationCancelledError",
    "OpPlan",
    "OpProgress",
    "PlanEntry",
    "build_delete_plan",
    "build_plan",
    "copy_entry",
    "delete_entry",
    "execute_delete_plan",
    "execute_move_plan",
    "execute_plan",
    "move_entry",
    "path_contains",
    "same_filesystem",
]
