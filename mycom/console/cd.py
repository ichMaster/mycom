"""cd interception: recognize a `cd` invocation so the app can apply it
directly to the active panel without ever spawning a shell — `cd` is a shell
builtin, not a real executable, so it could never run via exec anyway."""

from __future__ import annotations

import shlex
from pathlib import Path


def parse_cd(command: str) -> str | None:
    """Return the target path string if `command` is a `cd` invocation
    (`cd`, `cd <path>`, `cd -`), else None — the caller runs anything else
    normally. Quoted paths and a leading `~` are expanded. `cd -` has no
    OLDPWD history to fall back on in v0, so `-` is passed through as a
    literal (non-existent) target — the caller's normal "no such directory"
    handling reports it, rather than pretending to support history that
    isn't there. `cd` with more than one argument is deliberately not
    intercepted (ambiguous) and falls through to real execution instead.
    """
    text = command.strip()
    if not text:
        return None
    try:
        tokens = shlex.split(text)
    except ValueError:
        return None  # unbalanced quotes — let real execution report it
    if not tokens or tokens[0] != "cd":
        return None
    if len(tokens) > 2:
        return None
    if len(tokens) == 1:
        return str(Path.home())
    target = tokens[1]
    if target == "-":
        return target
    return str(Path(target).expanduser())
