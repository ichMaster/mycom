"""Filesystem helper functions for directory listing and formatting."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileEntry:
    """Represents a single file or directory entry."""

    name: str
    path: Path
    is_dir: bool
    is_symlink: bool
    size: int
    modified: float
    permissions: int


def list_directory(
    path: Path, show_hidden: bool = False, strict: bool = False
) -> list[FileEntry]:
    """List directory contents, returning FileEntry objects.

    Returns an empty list on permission errors rather than raising, unless
    ``strict`` is set — then a `PermissionError` (EACCES) is re-raised so
    callers can distinguish "unreadable" from "empty".
    """
    try:
        entries = []
        for item in path.iterdir():
            if not show_hidden and item.name.startswith("."):
                continue
            try:
                st = item.stat()
                is_symlink = item.is_symlink()
                entries.append(
                    FileEntry(
                        name=item.name,
                        path=item,
                        is_dir=stat.S_ISDIR(st.st_mode),
                        is_symlink=is_symlink,
                        size=st.st_size,
                        modified=st.st_mtime,
                        permissions=st.st_mode,
                    )
                )
            except OSError:
                # Broken symlink or inaccessible file
                entries.append(
                    FileEntry(
                        name=item.name,
                        path=item,
                        is_dir=False,
                        is_symlink=item.is_symlink(),
                        size=0,
                        modified=0,
                        permissions=0,
                    )
                )
        return entries
    except PermissionError:
        if strict:
            raise
        return []
    except OSError:
        return []


def format_size(size_bytes: int) -> str:
    """Format byte count as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ("KB", "MB", "GB", "TB"):
        size_bytes /= 1024
        if size_bytes < 1024 or unit == "TB":
            return f"{size_bytes:.1f} {unit}"
    return f"{size_bytes:.1f} TB"


def format_date(timestamp: float) -> str:
    """Format a Unix timestamp as a readable date string."""
    if timestamp == 0:
        return ""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")


def format_permissions(mode: int) -> str:
    """Format a file mode as a rwx permission string (e.g., 'rwxr-xr-x')."""
    if mode == 0:
        return ""
    parts = []
    for shift in (6, 3, 0):
        bits = (mode >> shift) & 0o7
        parts.append(
            ("r" if bits & 4 else "-") + ("w" if bits & 2 else "-") + ("x" if bits & 1 else "-")
        )
    return "".join(parts)
