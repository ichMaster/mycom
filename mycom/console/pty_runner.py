"""Runs a command in a real PTY with full passthrough (the `script(1)`
model): the child owns the real terminal (interactive programs like vim and
htop work), while every chunk read from it is teed through a callback before
being relayed on, unaltered, by `pty.spawn`'s own copy loop.

POSIX-only — `pty` is a POSIX-only stdlib module; a Windows conpty path (if
ever built) belongs in `mycom/platform/`, the only OS-conditional package.
"""

from __future__ import annotations

import os
import pty
import shlex
from collections.abc import Callable
from pathlib import Path

DEFAULT_SHELL = "/bin/sh"


def run_in_pty(command: str, cwd: Path, on_data: Callable[[bytes], None]) -> int:
    """Run `command` in a pty and return its exit code.

    `cwd` is applied via a `cd <cwd> && <command>` shell wrapper, letting
    the `-c` shell invocation interpret `command` as full shell syntax
    (pipes, `&&`, loops, semicolons) — this module never needs its own
    fork/chdir dance. `exec` in front of `command` would be wrong here: it
    directly execs a single binary rather than interpreting shell syntax,
    so anything beyond a bare command (a pipeline, a loop, `;`-separated
    statements) would fail. `on_data` is called with every chunk read from
    the child before it's relayed to the real terminal — a pure observer,
    it never alters what the user sees.
    """
    shell = os.environ.get("SHELL", DEFAULT_SHELL)
    wrapped = f"cd {shlex.quote(str(cwd))} && {command}"

    def tee_read(fd: int) -> bytes:
        data = os.read(fd, 1024)
        if data:
            on_data(data)
        return data

    status = pty.spawn([shell, "-c", wrapped], master_read=tee_read)
    return os.waitstatus_to_exitcode(status)
