"""Tests wiring AppConfig.general into panel construction (MC-010)."""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from mycom.config import AppConfig, GeneralConfig


@pytest.mark.asyncio
async def test_show_hidden_wired_from_config(tmp_path, monkeypatch):
    (tmp_path / "visible.txt").touch()
    (tmp_path / ".hidden.txt").touch()

    app = MyComApp()
    app._config = AppConfig(general=GeneralConfig(show_hidden=True))
    async with app.run_test():
        app.active_panel.navigate_to(tmp_path)

    assert app.active_panel._show_hidden is True


@pytest.mark.asyncio
async def test_default_sort_and_direction_wired_from_config():
    app = MyComApp()
    app._config = AppConfig(
        general=GeneralConfig(default_sort="size", default_sort_direction="desc")
    )
    async with app.run_test():
        assert app.active_panel.sort_field == "size"
        assert app.active_panel.sort_ascending is False
        assert app.inactive_panel.sort_field == "size"


@pytest.mark.asyncio
async def test_asc_direction_wired_from_config():
    app = MyComApp()
    app._config = AppConfig(general=GeneralConfig(default_sort_direction="asc"))
    async with app.run_test():
        assert app.active_panel.sort_ascending is True


def test_invalid_default_sort_falls_back_to_name(caplog):
    from mycom.panels.file_browser import FileBrowserPanel

    with caplog.at_level("WARNING"):
        panel = FileBrowserPanel(sort_field="not_a_real_field")

    assert panel.sort_field == "name"
    assert "not_a_real_field" in caplog.text
