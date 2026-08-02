"""Tests for mycom.console.pty_runner.run_in_pty — real (non-interactive)
subprocess execution, never mocked, per the project's fixtures-over-mocks
rule for filesystem/process behavior."""

from __future__ import annotations

from pathlib import Path

from mycom.console.pty_runner import run_in_pty
from mycom.console.ring_buffer import RingBuffer


def test_echo_output_is_captured_and_exit_code_zero(tmp_path: Path) -> None:
    buf = RingBuffer()
    exit_code = run_in_pty("echo hello", tmp_path, buf.append)
    assert exit_code == 0
    assert "hello" in buf.text()


def test_pwd_proves_cwd_wrapping_lands_in_the_right_directory(tmp_path: Path) -> None:
    real = tmp_path.resolve()
    buf = RingBuffer()
    run_in_pty("pwd", tmp_path, buf.append)
    assert str(real) in buf.text()


def test_exit_code_is_propagated(tmp_path: Path) -> None:
    buf = RingBuffer()
    exit_code = run_in_pty("exit 7", tmp_path, buf.append)
    assert exit_code == 7


def test_silent_command_leaves_had_output_false(tmp_path: Path) -> None:
    buf = RingBuffer()
    run_in_pty("true", tmp_path, buf.append)
    assert buf.had_output is False


def test_large_output_does_not_hang_and_stays_bounded(tmp_path: Path) -> None:
    buf = RingBuffer(max_lines=1000)
    exit_code = run_in_pty(
        "i=0; while [ $i -lt 150000 ]; do echo line-$i; i=$((i+1)); done",
        tmp_path,
        buf.append,
    )
    assert exit_code == 0
    assert buf.had_output is True
    lines = buf.text().split("\n")
    assert len(lines) == 1000
    assert lines[-1] == "line-149999"
