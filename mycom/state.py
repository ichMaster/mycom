"""SQLite (WAL) runtime state store: per-panel path/sort/view, app-level
toggles and window state, and (empty until v1.4) history tables.

Distinct from `config.py`'s user-authored TOML: this is app-owned, written
automatically, never hand-edited. Schema-versioned with migrations; a
corrupt or missing DB file recreates silently — startup must never be
blocked by state (spec/architecture.md §Persistence).
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from mycom.config import CONFIG_DIR

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = CONFIG_DIR / "state.db"

# Each entry: (version, statements-to-reach-it-from-the-previous-version).
_MIGRATIONS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (
        1,
        (
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)",
            """
            CREATE TABLE IF NOT EXISTS panel_state (
                side TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                sort_field TEXT NOT NULL,
                sort_ascending INTEGER NOT NULL,
                view_mode TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
            # Empty until v1.4 (histories) — created now so that phase doesn't
            # need its own migration just to add the tables.
            """
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                used_at REAL NOT NULL,
                pinned INTEGER NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS folder_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                used_at REAL NOT NULL,
                pinned INTEGER NOT NULL DEFAULT 0
            )
            """,
        ),
    ),
)

LATEST_SCHEMA_VERSION = _MIGRATIONS[-1][0]


@dataclass(frozen=True)
class PanelState:
    side: str
    path: str
    sort_field: str
    sort_ascending: bool
    view_mode: str


class StateDB:
    """The state.db engine: open/create, migrate, and typed accessors."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = self._open()

    def _open(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self._path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("SELECT count(*) FROM sqlite_master")  # forces validity check
            self._migrate(conn)
            return conn
        except sqlite3.DatabaseError:
            logger.warning("Corrupt or invalid state DB at %s — recreating", self._path)
            self._path.unlink(missing_ok=True)
            conn = sqlite3.connect(self._path)
            conn.execute("PRAGMA journal_mode=WAL")
            self._migrate(conn)
            return conn

    def _current_version(self, conn: sqlite3.Connection) -> int:
        try:
            row = conn.execute("SELECT version FROM schema_version").fetchone()
        except sqlite3.OperationalError:
            return 0
        return row[0] if row else 0

    def _migrate(self, conn: sqlite3.Connection) -> None:
        current = self._current_version(conn)
        for version, statements in _MIGRATIONS:
            if version <= current:
                continue
            for statement in statements:
                conn.execute(statement)
            conn.execute("DELETE FROM schema_version")
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- per-panel state --------------------------------------------------

    def get_panel_state(self, side: str) -> PanelState | None:
        row = self._conn.execute(
            "SELECT side, path, sort_field, sort_ascending, view_mode "
            "FROM panel_state WHERE side = ?",
            (side,),
        ).fetchone()
        if row is None:
            return None
        return PanelState(
            side=row[0],
            path=row[1],
            sort_field=row[2],
            sort_ascending=bool(row[3]),
            view_mode=row[4],
        )

    def save_panel_state(
        self,
        side: str,
        path: str,
        sort_field: str,
        sort_ascending: bool,
        view_mode: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO panel_state (side, path, sort_field, sort_ascending, view_mode)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(side) DO UPDATE SET
                path = excluded.path,
                sort_field = excluded.sort_field,
                sort_ascending = excluded.sort_ascending,
                view_mode = excluded.view_mode
            """,
            (side, path, sort_field, int(sort_ascending), view_mode),
        )
        self._conn.commit()

    # -- app-level state (hidden toggle, window state, ...) ---------------

    def get_app_state(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM app_state WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def save_app_state(self, key: str, value: str) -> None:
        self._conn.execute(
            """
            INSERT INTO app_state (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        self._conn.commit()
