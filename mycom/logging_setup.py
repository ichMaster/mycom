"""Structured, file-based logging setup.

Never logs to stdout/stderr — MyCom owns the full terminal screen (Textual),
and writing there would corrupt the TUI.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

DEFAULT_LOG_DIR = Path.home() / ".config" / "mycom"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "mycom.log"

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging() -> None:
    """Install a file handler on the "mycom" logger from env configuration.

    Reads ``MYCOM_LOG_LEVEL`` (default ``WARNING``) and ``MYCOM_LOG_FILE``
    (default: ``~/.config/mycom/mycom.log``). Idempotent: repeated calls
    replace any handler installed by a previous call instead of stacking.
    """
    level_name = os.environ.get("MYCOM_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)

    log_file = Path(os.environ.get("MYCOM_LOG_FILE", str(DEFAULT_LOG_FILE)))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    root = logging.getLogger("mycom")
    for existing in root.handlers[:]:
        root.removeHandler(existing)
        existing.close()
    root.setLevel(level)
    root.addHandler(handler)
