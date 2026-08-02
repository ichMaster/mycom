"""Tests for panel system."""

from pathlib import Path

import pytest
from textual.app import App, ComposeResult

from mycom.panels.base import PanelMode
from mycom.panels.file_browser import FileBrowserPanel


class PanelTestApp(App):
    def compose(self) -> ComposeResult:
        yield FileBrowserPanel(start_path=Path.home())


@pytest.mark.asyncio
async def test_file_browser_panel_renders():
    async with PanelTestApp().run_test() as pilot:
        panel = pilot.app.query_one(FileBrowserPanel)
        assert panel is not None


@pytest.mark.asyncio
async def test_file_browser_panel_current_path():
    async with PanelTestApp().run_test() as pilot:
        panel = pilot.app.query_one(FileBrowserPanel)
        assert panel.get_current_path() == Path.home()


@pytest.mark.asyncio
async def test_file_browser_panel_activate_deactivate():
    async with PanelTestApp().run_test() as pilot:
        panel = pilot.app.query_one(FileBrowserPanel)
        panel.activate()
        assert panel.is_active
        panel.deactivate()
        assert not panel.is_active


@pytest.mark.asyncio
async def test_file_browser_panel_mode():
    async with PanelTestApp().run_test() as pilot:
        panel = pilot.app.query_one(FileBrowserPanel)
        assert panel.mode == PanelMode.FILE_BROWSER


@pytest.mark.asyncio
async def test_file_browser_get_selected_files():
    async with PanelTestApp().run_test() as pilot:
        panel = pilot.app.query_one(FileBrowserPanel)
        files = panel.get_selected_files()
        assert isinstance(files, list)


def test_panel_mode_enum():
    assert PanelMode.FILE_BROWSER.value == "file_browser"
    assert PanelMode.TERMINAL.value == "terminal"
    assert PanelMode.LLM_CHAT.value == "llm_chat"
