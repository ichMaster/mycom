"""Regression tests for spec/roadmap/implementation/v0.1-code-review.md findings 1-3."""

from __future__ import annotations

import os

import pytest

from mycom.app import MyComApp
from mycom.panels.file_browser import FileBrowserPanel
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


@pytest.mark.skipif(os.getuid() == 0, reason="permission bits are bypassed when running as root")
def test_unmounted_panel_does_not_crash_on_permission_error(tmp_path):
    """Finding 2: `_show_error`'s `self.app is not None` guard never fired
    (Widget.app raises NoActiveAppError, not None, when unmounted) — an
    unmounted panel hitting an error must no-op, not crash."""
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    try:
        panel = FileBrowserPanel()  # constructed outside any running App
        panel.navigate_to(locked)  # must not raise NoActiveAppError
    finally:
        locked.chmod(0o755)


@pytest.mark.asyncio
async def test_resize_follows_active_panel_across_tab_switch():
    """Finding 3: after a resize, Tab must move the "wide" width to the
    newly active panel instead of leaving it on the old one."""
    app = MyComApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+right")  # active (left) -> 70%
        await pilot.pause()
        assert app.active_panel.styles.width.value == 70

        await pilot.press("tab")  # active is now right
        await pilot.pause()

        assert app.active_panel.styles.width.value == 70
        assert app.inactive_panel.styles.width.value == 1  # 1fr
