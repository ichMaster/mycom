"""Conflict resolution policy seam: the engine asks, an adapter (dialog or
test fake) answers. `ConflictPolicy` is the injectable contract — MC-026's
`ConflictDialog` adapter is one implementation; tests supply plain fakes."""

from __future__ import annotations

import os
from collections.abc import Callable
from enum import Enum, auto
from pathlib import Path

from mycom.fileops.plan import PlanEntry


class ConflictChoice(Enum):
    OVERWRITE = auto()
    SKIP = auto()
    RENAME = auto()
    OVERWRITE_ALL = auto()
    SKIP_ALL = auto()
    CANCEL = auto()


ConflictAnswer = ConflictChoice | tuple[ConflictChoice, Path]
ConflictPolicy = Callable[[PlanEntry, os.stat_result], ConflictAnswer]
