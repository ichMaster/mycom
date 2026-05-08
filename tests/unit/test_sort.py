"""Tests for mycom.operations.sort module."""

from pathlib import Path

from mycom.operations.sort import sort_entries
from mycom.utils.fs import FileEntry


def _entry(name: str, is_dir: bool = False, size: int = 0, modified: float = 0) -> FileEntry:
    return FileEntry(
        name=name,
        path=Path(f"/tmp/{name}"),
        is_dir=is_dir,
        is_symlink=False,
        size=size,
        modified=modified,
        permissions=0o644,
    )


ENTRIES = [
    _entry("readme.txt", size=500, modified=3),
    _entry("src", is_dir=True, modified=1),
    _entry("app.py", size=1000, modified=2),
    _entry("docs", is_dir=True, modified=4),
    _entry("zebra.log", size=200, modified=5),
]


def test_sort_by_name_ascending():
    result = sort_entries(ENTRIES, "name", ascending=True)
    names = [e.name for e in result]
    # Dirs first (alphabetical), then files (alphabetical)
    assert names == ["docs", "src", "app.py", "readme.txt", "zebra.log"]


def test_sort_by_name_descending():
    result = sort_entries(ENTRIES, "name", ascending=False)
    names = [e.name for e in result]
    assert names == ["src", "docs", "zebra.log", "readme.txt", "app.py"]


def test_sort_by_size():
    result = sort_entries(ENTRIES, "size", ascending=True)
    files = [e for e in result if not e.is_dir]
    sizes = [e.size for e in files]
    assert sizes == [200, 500, 1000]


def test_sort_by_date():
    result = sort_entries(ENTRIES, "date", ascending=True)
    files = [e for e in result if not e.is_dir]
    dates = [e.modified for e in files]
    assert dates == [2, 3, 5]


def test_sort_by_extension():
    result = sort_entries(ENTRIES, "extension", ascending=True)
    files = [e for e in result if not e.is_dir]
    exts = [e.name.rsplit(".", 1)[-1] if "." in e.name else "" for e in files]
    assert exts == ["log", "py", "txt"]


def test_dirs_always_first():
    for field in ("name", "size", "date", "extension"):
        for asc in (True, False):
            result = sort_entries(ENTRIES, field, ascending=asc)
            dir_indices = [i for i, e in enumerate(result) if e.is_dir]
            file_indices = [i for i, e in enumerate(result) if not e.is_dir]
            if dir_indices and file_indices:
                assert max(dir_indices) < min(file_indices), f"Dirs not first for {field} asc={asc}"


def test_empty_list():
    result = sort_entries([], "name", ascending=True)
    assert result == []


def test_only_dirs():
    entries = [_entry("b", is_dir=True), _entry("a", is_dir=True)]
    result = sort_entries(entries, "name", ascending=True)
    assert [e.name for e in result] == ["a", "b"]


def test_only_files():
    entries = [_entry("b.txt", size=2), _entry("a.txt", size=1)]
    result = sort_entries(entries, "name", ascending=True)
    assert [e.name for e in result] == ["a.txt", "b.txt"]
