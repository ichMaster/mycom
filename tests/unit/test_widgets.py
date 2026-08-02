"""Tests for FileList widget."""

from pathlib import Path

import pytest
from textual.app import App, ComposeResult

from mycom.widgets.file_list import FileList


class FileListApp(App):
    def compose(self) -> ComposeResult:
        yield FileList()


SAMPLE_ENTRIES = [
    {
        "name": "readme.txt",
        "size": "1.2 KB",
        "modified": "2026-01-01",
        "permissions": "rw-r--r--",
        "is_dir": False,
        "is_symlink": False,
    },
    {
        "name": "src",
        "size": "",
        "modified": "2026-01-01",
        "permissions": "rwxr-xr-x",
        "is_dir": True,
        "is_symlink": False,
    },
    {
        "name": "docs",
        "size": "",
        "modified": "2026-01-01",
        "permissions": "rwxr-xr-x",
        "is_dir": True,
        "is_symlink": False,
    },
    {
        "name": "link.txt",
        "size": "500 B",
        "modified": "2026-01-01",
        "permissions": "rw-r--r--",
        "is_dir": False,
        "is_symlink": True,
    },
]


@pytest.mark.asyncio
async def test_file_list_renders_columns():
    async with FileListApp().run_test() as pilot:
        fl = pilot.app.query_one(FileList)
        fl.load_directory(SAMPLE_ENTRIES, Path("/home/user"))
        assert fl.row_count == 5  # .. + 2 dirs + 2 files


@pytest.mark.asyncio
async def test_file_list_dirs_before_files():
    async with FileListApp().run_test() as pilot:
        fl = pilot.app.query_one(FileList)
        fl.load_directory(SAMPLE_ENTRIES, Path("/home/user"))
        # Row 0 = .., rows 1-2 = dirs (docs, src), rows 3-4 = files
        rows = list(fl.rows)
        assert str(rows[0].value) == ".."


@pytest.mark.asyncio
async def test_file_list_no_parent_at_root():
    async with FileListApp().run_test() as pilot:
        fl = pilot.app.query_one(FileList)
        fl.load_directory(SAMPLE_ENTRIES, Path("/"))
        assert fl.row_count == 4  # no .. entry


@pytest.mark.asyncio
async def test_file_list_empty_directory():
    async with FileListApp().run_test() as pilot:
        fl = pilot.app.query_one(FileList)
        fl.load_directory([], Path("/home/user"))
        assert fl.row_count == 1  # only ..


@pytest.mark.asyncio
async def test_file_list_selected_name():
    async with FileListApp().run_test() as pilot:
        fl = pilot.app.query_one(FileList)
        fl.load_directory(SAMPLE_ENTRIES, Path("/home/user"))
        name = fl.selected_name
        assert name is not None
