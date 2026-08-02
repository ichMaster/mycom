"""Bounded output buffer: backs Ctrl+O recall without unbounded memory
growth on a command that prints a huge amount of output."""

from __future__ import annotations

from collections import deque


class RingBuffer:
    """Holds up to `max_lines` of decoded output; oldest lines are dropped
    once the bound is exceeded. `had_output` tracks whether anything was
    ever appended, independent of what's since been evicted — it's what
    decides whether "Press any key" shows at all (F0.11)."""

    def __init__(self, max_lines: int = 100_000) -> None:
        self._lines: deque[str] = deque(maxlen=max_lines)
        self._partial = ""
        self._had_output = False

    def append(self, data: bytes) -> None:
        if not data:
            return
        self._had_output = True
        text = self._partial + data.decode("utf-8", errors="replace")
        # A PTY's line discipline translates outgoing "\n" to "\r\n" by
        # default — normalize that back so recalled text doesn't carry a
        # stray \r per line. A lone "\r" (not followed by "\n", e.g. a
        # progress-bar overwriting its own line) is left alone: splitting on
        # every bare \r too would turn one progress bar into thousands of
        # ring-buffer lines.
        text = text.replace("\r\n", "\n")
        *complete, self._partial = text.split("\n")
        self._lines.extend(complete)

    def text(self) -> str:
        lines = list(self._lines)
        if self._partial:
            lines.append(self._partial)
        return "\n".join(lines)

    @property
    def had_output(self) -> bool:
        return self._had_output

    def clear(self) -> None:
        self._lines.clear()
        self._partial = ""
        self._had_output = False
