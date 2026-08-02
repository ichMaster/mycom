"""Tests for mycom.logging_setup module."""

from __future__ import annotations

import logging

from mycom.logging_setup import configure_logging


def test_default_level_is_warning(tmp_path, monkeypatch):
    monkeypatch.delenv("MYCOM_LOG_LEVEL", raising=False)
    monkeypatch.setenv("MYCOM_LOG_FILE", str(tmp_path / "mycom.log"))
    configure_logging()
    assert logging.getLogger("mycom").level == logging.WARNING


def test_env_level_applied(tmp_path, monkeypatch):
    monkeypatch.setenv("MYCOM_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MYCOM_LOG_FILE", str(tmp_path / "mycom.log"))
    configure_logging()
    assert logging.getLogger("mycom").level == logging.DEBUG


def test_debug_lines_written_to_log_file(tmp_path, monkeypatch):
    log_file = tmp_path / "mycom.log"
    monkeypatch.setenv("MYCOM_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MYCOM_LOG_FILE", str(log_file))
    configure_logging()

    logging.getLogger("mycom.test").debug("hello from test")
    for handler in logging.getLogger("mycom").handlers:
        handler.flush()

    assert log_file.exists()
    assert "hello from test" in log_file.read_text()


def test_log_file_dir_created(tmp_path, monkeypatch):
    log_file = tmp_path / "nested" / "dir" / "mycom.log"
    monkeypatch.setenv("MYCOM_LOG_FILE", str(log_file))
    configure_logging()
    assert log_file.parent.is_dir()


def test_repeated_calls_do_not_stack_handlers(tmp_path, monkeypatch):
    monkeypatch.setenv("MYCOM_LOG_FILE", str(tmp_path / "mycom.log"))
    configure_logging()
    configure_logging()
    configure_logging()
    assert len(logging.getLogger("mycom").handlers) == 1
