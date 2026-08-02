"""Regression tests for spec/roadmap/implementation/v0.1-code-review.md findings 1-3."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from mycom.widgets.dialog import ErrorDialog


@pytest.mark.asyncio
async def test_vanished_directory_shows_error_and_stays_in_place(tmp_path):
    """Finding 1: a directory removed between selection and Enter must not
    silently render as an empty panel — it should error and stay put."""
    child = tmp_path / "child"
    child.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        before = app.active_panel.current_path

        child.rmdir()  # simulate the directory vanishing after listing/selection
        app.active_panel.navigate_to(child)
        await pilot.pause()

        assert isinstance(app.screen, ErrorDialog)
        assert app.active_panel.current_path == before

        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, ErrorDialog)
