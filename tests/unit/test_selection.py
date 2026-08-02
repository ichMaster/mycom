"""Unit tests for MC-019: selection model invariants (no Textual app needed)."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_selection_survives_sort_change(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        app.active_panel.toggle_selection_at_cursor()
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}

        await pilot.press("ctrl+f6")  # sort by size
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}


@pytest.mark.asyncio
async def test_selection_survives_view_mode_change(tmp_path):
    (tmp_path / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        app.active_panel.toggle_selection_at_cursor()
        await pilot.pause()

        await pilot.press("ctrl+1")  # Brief
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}


@pytest.mark.asyncio
async def test_selection_resets_on_directory_change(tmp_path):
    child = tmp_path / "child"
    child.mkdir()
    (tmp_path / "a.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        app.active_panel.toggle_selection_at_cursor()
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}

        app.active_panel.navigate_to(child)
        await pilot.pause()
        assert app.active_panel.selected_names == frozenset()


@pytest.mark.asyncio
async def test_dotdot_never_selectable(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("..")
        app.active_panel.toggle_selection_at_cursor()
        await pilot.pause()
        assert app.active_panel.selected_names == frozenset()


@pytest.mark.asyncio
async def test_get_selected_files_prefers_selection_over_cursor(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        app.active_panel.toggle_selection_at_cursor()
        await pilot.pause()

        app.active_panel.file_list.select_by_name("b.txt")  # cursor elsewhere now
        files = app.active_panel.get_selected_files()
        assert {p.name for p in files} == {"a.txt"}


@pytest.mark.asyncio
async def test_get_selected_files_falls_back_to_cursor_when_empty(tmp_path):
    (tmp_path / "only.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("only.txt")

        files = app.active_panel.get_selected_files()
        assert {p.name for p in files} == {"only.txt"}


@pytest.mark.asyncio
async def test_get_selected_files_returns_sorted_order(tmp_path):
    """A plain set has no reproducible iteration order — file operations
    (v0.4) process entries in this order, so an arbitrary hash-based order
    would make cancellation and "which files got processed" unpredictable."""
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    for name in ("zeta.txt", "alpha.txt", "mu.txt"):
        (content_dir / name).touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)

        files = app.active_panel.get_selected_files()
        assert [p.name for p in files] == ["alpha.txt", "mu.txt", "zeta.txt"]


@pytest.mark.asyncio
async def test_deselect_removes_exactly_given_names(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    (tmp_path / "c.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        for name in ("a.txt", "b.txt", "c.txt"):
            app.active_panel.file_list.select_by_name(name)
            app.active_panel.toggle_selection_at_cursor()
            await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt", "b.txt", "c.txt"}

        app.active_panel.deselect(["a.txt", "b.txt"])
        assert app.active_panel.selected_names == {"c.txt"}
