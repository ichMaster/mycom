"""Tests for mycom.utils.fs module."""

from pathlib import Path

from mycom.utils.fs import FileEntry, format_date, format_permissions, format_size, list_directory

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_tree"


def test_list_directory_returns_entries():
    entries = list_directory(FIXTURES, show_hidden=False)
    names = {e.name for e in entries}
    assert "file1.txt" in names
    assert "file2.py" in names
    assert "subdir" in names


def test_list_directory_hides_hidden():
    entries = list_directory(FIXTURES, show_hidden=False)
    names = {e.name for e in entries}
    assert ".hidden" not in names


def test_list_directory_shows_hidden():
    entries = list_directory(FIXTURES, show_hidden=True)
    names = {e.name for e in entries}
    assert ".hidden" in names


def test_list_directory_identifies_dirs():
    entries = list_directory(FIXTURES)
    dirs = [e for e in entries if e.is_dir]
    dir_names = {e.name for e in dirs}
    assert "subdir" in dir_names


def test_list_directory_permission_error():
    entries = list_directory(Path("/root/nonexistent_private_dir"))
    assert entries == []


def test_list_directory_nonexistent():
    entries = list_directory(Path("/this/path/does/not/exist"))
    assert entries == []


def test_format_size_zero():
    assert format_size(0) == "0 B"


def test_format_size_bytes():
    assert format_size(500) == "500 B"
    assert format_size(1023) == "1023 B"


def test_format_size_kilobytes():
    assert format_size(1024) == "1.0 KB"
    assert format_size(1536) == "1.5 KB"


def test_format_size_megabytes():
    assert format_size(1_572_864) == "1.5 MB"


def test_format_size_gigabytes():
    result = format_size(2_469_606_195)
    assert "GB" in result


def test_format_date_zero():
    assert format_date(0) == ""


def test_format_date_valid():
    result = format_date(1704067200)  # 2024-01-01 00:00:00 UTC (approx)
    assert "2024" in result or "2023" in result  # timezone dependent


def test_format_permissions_zero():
    assert format_permissions(0) == ""


def test_format_permissions_755():
    assert format_permissions(0o755) == "rwxr-xr-x"


def test_format_permissions_644():
    assert format_permissions(0o644) == "rw-r--r--"


def test_format_permissions_700():
    assert format_permissions(0o700) == "rwx------"


def test_file_entry_dataclass():
    entry = FileEntry(
        name="test.txt",
        path=Path("/tmp/test.txt"),
        is_dir=False,
        is_symlink=False,
        size=1024,
        modified=1704067200,
        permissions=0o644,
    )
    assert entry.name == "test.txt"
    assert not entry.is_dir
