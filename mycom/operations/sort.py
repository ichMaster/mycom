"""Sorting logic for file entries."""

from __future__ import annotations

from mycom.utils.fs import FileEntry

SORT_FIELDS = ("name", "size", "date", "extension")


def sort_entries(
    entries: list[FileEntry],
    field: str = "name",
    ascending: bool = True,
) -> list[FileEntry]:
    """Sort file entries with directories always before files.

    Args:
        entries: List of FileEntry objects.
        field: Sort field — one of 'name', 'size', 'date', 'extension'.
        ascending: Sort direction.

    Returns:
        Sorted list of FileEntry objects.
    """
    dirs = [e for e in entries if e.is_dir]
    files = [e for e in entries if not e.is_dir]

    key_func = _get_key_func(field)
    dirs.sort(key=key_func, reverse=not ascending)
    files.sort(key=key_func, reverse=not ascending)

    return dirs + files


def _get_key_func(field: str):
    if field == "name":
        return lambda e: e.name.lower()
    elif field == "size":
        return lambda e: e.size
    elif field == "date":
        return lambda e: e.modified
    elif field == "extension":
        return lambda e: _get_extension(e.name)
    return lambda e: e.name.lower()


def _get_extension(name: str) -> str:
    if "." in name:
        return name.rsplit(".", 1)[-1].lower()
    return ""
