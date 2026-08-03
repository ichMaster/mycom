"""Pilot-driven regression test for code review v0.3 #2 (hardened, v0.6.1):
selection is keyed by bare filename only, so an external process replacing a
selected file with an unrelated same-named file must not leave the new file
silently selected after the next in-panel refresh (e.g. Ctrl+H)."""

from __future__ import annotations

import os
import time

import pytest

from mycom.app import MyComApp


@pytest.mark.asyncio
async def test_externally_replaced_file_is_dropped_from_selection_on_refresh(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"original content")
    (tmp_path / "b.txt").write_bytes(b"b")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()
        await pilot.press("insert")
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}

        # Externally replace "a.txt" with an unrelated file of the same
        # name but a different size (and, incidentally, mtime) — the
        # on-disk identity behind the selected name has changed completely.
        (tmp_path / "a.txt").unlink()
        (tmp_path / "a.txt").write_bytes(b"totally different replacement content, much longer")

        await pilot.press("ctrl+h")  # toggles hidden files -> refresh_listing()
        await pilot.pause()

        assert "a.txt" not in app.active_panel.selected_names


@pytest.mark.asyncio
async def test_untouched_selection_survives_a_refresh(tmp_path):
    """Guards against an over-broad fix: a selected file that wasn't
    touched must stay selected across a refresh triggered by something
    else in the same directory."""
    (tmp_path / "a.txt").write_bytes(b"unchanged content")
    (tmp_path / "b.txt").write_bytes(b"b")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()
        await pilot.press("insert")
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}

        await pilot.press("ctrl+h")
        await pilot.pause()

        assert app.active_panel.selected_names == {"a.txt"}


@pytest.mark.asyncio
async def test_replaced_file_with_same_size_but_different_mtime_is_dropped(tmp_path):
    """The identity signal is (is_dir, size, modified) together — a same-
    size replacement is still caught via its changed mtime."""
    (tmp_path / "a.txt").write_bytes(b"12345678")

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        app.active_panel.file_list.select_by_name("a.txt")
        await pilot.pause()
        await pilot.press("insert")
        await pilot.pause()
        assert app.active_panel.selected_names == {"a.txt"}

        (tmp_path / "a.txt").unlink()
        (tmp_path / "a.txt").write_bytes(b"ABCDEFGH")  # same size, different content
        future = time.time() + 120
        os.utime(tmp_path / "a.txt", (future, future))  # force a distinct mtime

        await pilot.press("ctrl+h")
        await pilot.pause()

        assert "a.txt" not in app.active_panel.selected_names
