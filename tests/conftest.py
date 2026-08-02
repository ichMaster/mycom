"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_log_file(tmp_path, monkeypatch):
    """Redirect MyCom's log file to a tmp path so tests never touch ~/.config."""
    monkeypatch.setenv("MYCOM_LOG_FILE", str(tmp_path / "mycom.log"))


@pytest.fixture(autouse=True)
def _isolated_state_db(tmp_path, monkeypatch):
    """Redirect MyCom's state.db to a tmp path so tests never touch ~/.config.

    All MyComApp() instances constructed within one test share the same
    tmp_path, so this also gives "restart" tests (build a second MyComApp
    against the same DB) a working shared path for free.
    """
    monkeypatch.setattr("mycom.state.DEFAULT_DB_PATH", tmp_path / "state.db")
