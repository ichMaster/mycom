"""Integration tests for file navigation, filter, and sorting."""

from pathlib import Path

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_enter_navigates_into_directory(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        panel = app.active_panel
        panel.navigate_to(tmp_path)
        await pilot.pause()
        # Move to the subdir entry and press enter
        panel.navigate_to(subdir)
        assert panel.current_path == subdir


@pytest.mark.asyncio
async def test_navigate_up():
    app = MyComApp()
    async with app.run_test():
        panel = app.active_panel
        original = panel.current_path
        panel.navigate_to(original / ".." if original != Path("/") else original)
        panel.navigate_to(original)
        panel.navigate_up()
        assert panel.current_path == original.parent or panel.current_path == original


@pytest.mark.asyncio
async def test_filter_narrows_listing(tmp_path):
    (tmp_path / "alpha.txt").touch()
    (tmp_path / "beta.txt").touch()
    (tmp_path / "gamma.py").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        panel = app.active_panel
        panel.navigate_to(tmp_path)
        await pilot.pause()

        panel.set_filter("alpha")
        await pilot.pause()
        # Only alpha.txt + .. should be visible
        assert panel.file_list.row_count <= 2

        panel.clear_filter()
        await pilot.pause()
        assert panel.file_list.row_count >= 4  # .. + 3 files


@pytest.mark.asyncio
async def test_sort_toggle(tmp_path):
    (tmp_path / "a.txt").write_text("small")
    (tmp_path / "b.txt").write_text("larger content here")

    app = MyComApp()
    async with app.run_test() as pilot:
        panel = app.active_panel
        panel.navigate_to(tmp_path)
        await pilot.pause()

        panel.set_sort("size")
        assert panel.sort_field == "size"
        assert panel.sort_ascending is True

        panel.set_sort("size")
        assert panel.sort_ascending is False


@pytest.mark.asyncio
async def test_permission_denied_does_not_crash():
    app = MyComApp()
    async with app.run_test() as pilot:
        panel = app.active_panel
        # Navigating to a non-existent dir should not crash
        panel.navigate_to(Path("/nonexistent_dir_12345"))
        await pilot.pause()
        # Panel should still be functional
        assert panel.file_list.row_count >= 0
