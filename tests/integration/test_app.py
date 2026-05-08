"""Integration tests for the MyCom application shell."""

import pytest

from mycom.app import MyComApp
from mycom.panels.file_browser import FileBrowserPanel
from mycom.widgets.header import AppHeader
from mycom.widgets.status_bar import StatusBar


@pytest.mark.asyncio
async def test_app_starts_and_renders():
    async with MyComApp().run_test() as pilot:
        app = pilot.app
        assert app.title == "MyCom"


@pytest.mark.asyncio
async def test_app_has_two_panels():
    async with MyComApp().run_test() as pilot:
        panels = pilot.app.query(FileBrowserPanel)
        assert len(panels) == 2


@pytest.mark.asyncio
async def test_app_has_status_bar():
    async with MyComApp().run_test() as pilot:
        sb = pilot.app.query_one(StatusBar)
        assert sb is not None


@pytest.mark.asyncio
async def test_app_has_header():
    async with MyComApp().run_test() as pilot:
        header = pilot.app.query_one(AppHeader)
        assert header is not None


@pytest.mark.asyncio
async def test_left_panel_active_by_default():
    async with MyComApp().run_test() as pilot:
        app = pilot.app
        assert app._active_side == "left"
        assert app.active_panel.is_active


@pytest.mark.asyncio
async def test_tab_switches_panel():
    async with MyComApp().run_test() as pilot:
        app = pilot.app
        assert app._active_side == "left"
        await pilot.press("tab")
        assert app._active_side == "right"
        assert app.active_panel.is_active
        await pilot.press("tab")
        assert app._active_side == "left"


@pytest.mark.asyncio
async def test_f10_quits():
    async with MyComApp().run_test() as pilot:
        await pilot.press("f10")
        assert pilot.app._exit
