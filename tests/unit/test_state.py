"""Unit tests for mycom.state.StateDB (MC-023)."""

from __future__ import annotations

import sqlite3

import pytest

from mycom.state import LATEST_SCHEMA_VERSION, PanelState, StateDB


def test_fresh_db_creates_schema_at_latest_version(tmp_path):
    db = StateDB(tmp_path / "state.db")
    version = db._conn.execute("SELECT version FROM schema_version").fetchone()[0]
    assert version == LATEST_SCHEMA_VERSION
    db.close()


def test_wal_mode_is_active(tmp_path):
    db = StateDB(tmp_path / "state.db")
    mode = db._conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"
    db.close()


def test_panel_state_round_trip(tmp_path):
    db = StateDB(tmp_path / "state.db")
    db.save_panel_state("left", "/home/user", "size", False, "wide")

    result = db.get_panel_state("left")
    assert result == PanelState(
        side="left", path="/home/user", sort_field="size", sort_ascending=False, view_mode="wide"
    )
    db.close()


def test_panel_state_missing_returns_none(tmp_path):
    db = StateDB(tmp_path / "state.db")
    assert db.get_panel_state("right") is None
    db.close()


def test_panel_state_upsert_overwrites(tmp_path):
    db = StateDB(tmp_path / "state.db")
    db.save_panel_state("left", "/a", "name", True, "full")
    db.save_panel_state("left", "/b", "size", False, "brief")

    result = db.get_panel_state("left")
    assert result.path == "/b"
    assert result.sort_field == "size"
    assert result.sort_ascending is False
    assert result.view_mode == "brief"
    db.close()


def test_app_state_round_trip(tmp_path):
    db = StateDB(tmp_path / "state.db")
    db.save_app_state("show_hidden", "true")
    assert db.get_app_state("show_hidden") == "true"
    db.close()


def test_app_state_missing_returns_default(tmp_path):
    db = StateDB(tmp_path / "state.db")
    assert db.get_app_state("nonexistent", default="fallback") == "fallback"
    assert db.get_app_state("nonexistent") is None
    db.close()


def test_app_state_upsert_overwrites(tmp_path):
    db = StateDB(tmp_path / "state.db")
    db.save_app_state("k", "v1")
    db.save_app_state("k", "v2")
    assert db.get_app_state("k") == "v2"
    db.close()


def test_corrupt_db_file_is_recreated_not_raised(tmp_path):
    db_path = tmp_path / "state.db"
    db_path.write_bytes(b"this is not a sqlite database, just garbage bytes" * 10)

    db = StateDB(db_path)  # must not raise
    version = db._conn.execute("SELECT version FROM schema_version").fetchone()[0]
    assert version == LATEST_SCHEMA_VERSION
    db.close()


def test_migration_from_empty_schema_creates_all_tables(tmp_path):
    db_path = tmp_path / "state.db"
    # An empty-but-valid SQLite file (schema version 0 — no schema_version row).
    raw = sqlite3.connect(db_path)
    raw.close()

    db = StateDB(db_path)
    tables = {
        row[0]
        for row in db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {
        "schema_version",
        "panel_state",
        "app_state",
        "command_history",
        "folder_history",
    } <= tables
    db.close()


def test_history_tables_exist_and_are_empty(tmp_path):
    db = StateDB(tmp_path / "state.db")
    for table in ("command_history", "folder_history"):
        count = db._conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        assert count == 0
    db.close()


@pytest.fixture
def isolated_default_db(tmp_path, monkeypatch):
    """No real ~/.config writes: point the default path at a tmp file."""
    monkeypatch.setattr("mycom.state.DEFAULT_DB_PATH", tmp_path / "state.db")


def test_default_path_used_when_none_given(isolated_default_db):
    db = StateDB()
    assert db._path.name == "state.db"
    db.close()
