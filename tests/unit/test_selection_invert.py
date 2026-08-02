"""Unit tests for MC-021: invert_selection invariants."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_invert_flips_partial_selection(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    for name in ("a.txt", "b.txt", "c.txt", "d.txt", "e.txt"):
        (content_dir / name).touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("a.txt;b.txt", True)
        assert app.active_panel.selected_names == {"a.txt", "b.txt"}

        app.active_panel.invert_selection()
        assert app.active_panel.selected_names == {"c.txt", "d.txt", "e.txt"}


@pytest.mark.asyncio
async def test_invert_empty_selects_everything(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.txt").touch()
    (content_dir / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        assert app.active_panel.selected_names == frozenset()

        app.active_panel.invert_selection()
        assert app.active_panel.selected_names == {"a.txt", "b.txt"}


@pytest.mark.asyncio
async def test_invert_full_selection_clears_it(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.txt").touch()
    (content_dir / "b.txt").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        app.active_panel.select_by_mask("*", True)
        assert app.active_panel.selected_names == {"a.txt", "b.txt"}

        app.active_panel.invert_selection()
        assert app.active_panel.selected_names == frozenset()


@pytest.mark.asyncio
async def test_invert_never_selects_dotdot(tmp_path):
    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.invert_selection()
        assert ".." not in app.active_panel.selected_names
