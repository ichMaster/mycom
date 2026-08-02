"""Tests for mycom.console.cd.parse_cd."""

from __future__ import annotations

from pathlib import Path

from mycom.console.cd import parse_cd


def test_bare_cd_resolves_to_home():
    assert parse_cd("cd") == str(Path.home())
    assert parse_cd("  cd  ") == str(Path.home())


def test_cd_with_plain_path():
    assert parse_cd("cd /tmp") == "/tmp"


def test_cd_with_double_quoted_path_with_spaces():
    assert parse_cd('cd "path with spaces"') == "path with spaces"


def test_cd_with_single_quoted_path():
    assert parse_cd("cd 'another path'") == "another path"


def test_cd_expands_tilde():
    assert parse_cd("cd ~") == str(Path.home())
    assert parse_cd("cd ~/projects") == str(Path.home() / "projects")


def test_cd_dash_is_literal_no_oldpwd_tracking():
    assert parse_cd("cd -") == "-"


def test_cd_multiple_arguments_not_intercepted():
    assert parse_cd("cd foo bar") is None


def test_not_a_cd_command_returns_none():
    assert parse_cd("ls -la") is None
    assert parse_cd("echo cd") is None  # "cd" isn't the first token
    assert parse_cd("") is None
    assert parse_cd("   ") is None


def test_unbalanced_quotes_returns_none():
    assert parse_cd('cd "unterminated') is None
