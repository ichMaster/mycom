"""EOL/trailing-newline detection and binary/size gating for the editor (F0.13).

The editor's contract is *trust*: a file saved without content changes must
produce zero diff. That means capturing exactly what's needed to write a file
back byte-identical (its line-ending convention, its trailing-newline state)
before a single edit happens, and refusing — not silently mis-decoding — a
file the editor can't safely round-trip (binary, or too large).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

_PROBE_SIZE = 8192
MAX_EDITABLE_SIZE = 10 * 1024 * 1024


class EolStyle(Enum):
    LF = "LF"
    CRLF = "CRLF"
    MIXED_LF_DOMINANT = "MIXED_LF_DOMINANT"
    MIXED_CRLF_DOMINANT = "MIXED_CRLF_DOMINANT"


class NotEditableError(Exception):
    """Raised by `read_text` when a file can't be safely loaded into the
    editor. `reason` is `"binary"` or `"too_large"` — the editor screen uses
    it to redirect to the viewer with an accurate notice."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: not editable ({reason})")


def detect_eol(text: str) -> EolStyle:
    """Detect a text's line-ending convention. A file with no line endings
    at all (empty, or a single line) has nothing to detect — `LF` is the
    save-time default in that case, not a claim about what was found."""
    crlf_count = text.count("\r\n")
    bare_lf_count = text.count("\n") - crlf_count
    if crlf_count == 0:
        return EolStyle.LF
    if bare_lf_count == 0:
        return EolStyle.CRLF
    # Mixed: dominant is whichever is more frequent; ties favor LF, the more
    # common convention.
    if bare_lf_count >= crlf_count:
        return EolStyle.MIXED_LF_DOMINANT
    return EolStyle.MIXED_CRLF_DOMINANT


def has_trailing_newline(text: str) -> bool:
    return text.endswith("\n")


def apply_eol(text: str, style: EolStyle) -> str:
    """Convert `\\n`-normalized text back to `style` for writing. A mixed
    style saves as its dominant convention — the standard editor behavior of
    normalizing mixed line endings on save."""
    if style in (EolStyle.CRLF, EolStyle.MIXED_CRLF_DOMINANT):
        return text.replace("\n", "\r\n")
    return text


def is_binary(sample: bytes) -> bool:
    """A pragmatic heuristic over a probe of a file's leading bytes: an
    embedded NUL, or a high proportion of non-printable/control bytes,
    signals binary content that the editor should refuse rather than
    mis-decode."""
    if b"\x00" in sample:
        return True
    if not sample:
        return False
    non_printable = sum(1 for b in sample if b < 9 or 13 < b < 32)
    return non_printable / len(sample) > 0.3


def too_large(path: Path) -> bool:
    return path.stat().st_size > MAX_EDITABLE_SIZE


def read_text(path: Path) -> tuple[str, EolStyle, bool]:
    """Read `path` as UTF-8 text for editing.

    Returns `(text, eol_style, had_trailing_newline)` with `text` normalized
    to `\\n` line endings (Textual's `TextArea` works in normalized text
    internally regardless of source EOL). Raises `NotEditableError` — never
    silently mis-decodes — for a file that's too large or not valid UTF-8
    text.
    """
    if too_large(path):
        raise NotEditableError(path, "too_large")
    raw = path.read_bytes()
    if is_binary(raw[:_PROBE_SIZE]):
        raise NotEditableError(path, "binary")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise NotEditableError(path, "binary") from exc
    eol = detect_eol(text)
    trailing_newline = has_trailing_newline(text)
    normalized = text.replace("\r\n", "\n")
    return normalized, eol, trailing_newline
