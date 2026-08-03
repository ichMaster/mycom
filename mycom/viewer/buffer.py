"""Windowed, mmap-backed file reading for the viewer (F0.12).

Never loads a file whole and never indexes the full set of line offsets — a
Python list of line-start ints for a multi-GB, millions-of-lines file would
itself blow the RSS budget. Only the region a requested window needs is
scanned, so opening and paging a huge file stays fast with bounded memory.
Mirrors the pure, Textual-free shape of mycom.fileops and mycom.console.
"""

from __future__ import annotations

import mmap
from pathlib import Path

_PROBE_SIZE = 8192
# Caps a single backward scan so one pathologically long "line" (e.g. a
# minified JSON file with no newlines for megabytes) can't scan unboundedly.
_MAX_LOOKBACK = 4 * 1024 * 1024


def _looks_binary(sample: bytes) -> bool:
    if b"\x00" in sample:
        return True
    if not sample:
        return False
    non_printable = sum(1 for b in sample if b < 9 or 13 < b < 32)
    return non_printable / len(sample) > 0.3


class ViewerBuffer:
    """Read-only, windowed access to a file via mmap.

    Encoding is probed once at open from a small sample; decoding thereafter
    never raises (invalid UTF-8 falls back to ``errors="replace"``, and a
    binary-looking sample falls back to latin-1, which cannot fail to
    decode).
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._file = open(path, "rb")  # noqa: SIM115 — kept open for the object's lifetime
        try:
            self._size = self._file.seek(0, 2)
            self._file.seek(0)
            self._mmap: mmap.mmap | None = (
                mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
                if self._size > 0
                else None
            )
        except (OSError, ValueError):
            self._file.close()
            raise
        self._encoding = self._probe_encoding()

    def _probe_encoding(self) -> str:
        if self._mmap is None:
            return "utf-8"
        sample = bytes(self._mmap[: min(_PROBE_SIZE, self._size)])
        # Binary-ish content (embedded NUL, mostly non-printable) is checked
        # first: a NUL byte is technically valid UTF-8 (U+0000) and would
        # pass a strict decode, but it's still a strong binary signal that
        # should route to latin-1 rather than being treated as clean text.
        if _looks_binary(sample):
            return "latin-1"
        try:
            sample.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            return "utf-8"  # invalid but not binary-ish: decode via errors="replace"

    def _decode(self, data: bytes) -> str:
        if self._encoding == "latin-1":
            return data.decode("latin-1")
        return data.decode("utf-8", errors="replace")

    @property
    def size(self) -> int:
        return self._size

    @property
    def eof_offset(self) -> int:
        return self._size

    @property
    def encoding(self) -> str:
        return self._encoding

    def read_lines_forward(self, offset: int, count: int) -> tuple[list[str], int]:
        """Return up to `count` lines starting at `offset`, plus the file
        offset just past the last line returned (for chaining the next
        read)."""
        if self._mmap is None or offset >= self._size or count <= 0:
            return [], offset
        lines: list[str] = []
        pos = offset
        while len(lines) < count and pos < self._size:
            nl = self._mmap.find(b"\n", pos)
            if nl == -1:
                lines.append(self._decode(self._mmap[pos : self._size]))
                pos = self._size
                break
            lines.append(self._decode(self._mmap[pos:nl]))
            pos = nl + 1
        return lines, pos

    def read_lines_backward(self, offset: int, count: int) -> tuple[list[str], int]:
        """Return up to `count` lines ending just before `offset` (in file
        order), plus the file offset of the first line returned. Bounded by
        `_MAX_LOOKBACK`: if the requested lines can't be found within the
        lookback window (one huge line with no newline), the returned window
        starts at the lookback cap — a truncated first "line" — rather than
        scanning further back.
        """
        if self._mmap is None or offset <= 0 or count <= 0:
            return [], offset
        end = offset
        # A newline sitting right at `offset` means we're positioned just
        # after a line boundary; step back over it so we scan the line
        # before it, not an empty trailing one.
        if self._mmap[end - 1] == 0x0A:
            end -= 1
        lookback_limit = max(0, offset - _MAX_LOOKBACK)
        starts: list[int] = []
        cursor = end
        while len(starts) < count:
            nl = self._mmap.rfind(b"\n", lookback_limit, cursor)
            if nl == -1:
                starts.append(lookback_limit)
                break
            starts.append(nl + 1)
            cursor = nl
        start = starts[-1]
        lines: list[str] = []
        pos = start
        while pos < end:
            nl = self._mmap.find(b"\n", pos, end)
            if nl == -1:
                lines.append(self._decode(self._mmap[pos:end]))
                pos = end
            else:
                lines.append(self._decode(self._mmap[pos:nl]))
                pos = nl + 1
        return lines, start

    def close(self) -> None:
        if self._mmap is not None:
            self._mmap.close()
        self._file.close()

    def __enter__(self) -> ViewerBuffer:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
