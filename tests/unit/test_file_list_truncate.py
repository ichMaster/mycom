"""Tests for the unicode-safe name truncation helper."""

from mycom.widgets.file_list import truncate_name


def test_short_name_unchanged():
    assert truncate_name("short.txt", 20) == "short.txt"


def test_long_name_truncated_with_ellipsis():
    result = truncate_name("a" * 50, 20)
    assert len(result) == 20
    assert result.endswith("…")


def test_exact_width_unchanged():
    assert truncate_name("x" * 10, 10) == "x" * 10


def test_unicode_name_truncated_by_codepoint():
    # Multi-byte (in UTF-8) but single-codepoint characters must not be split mid-byte.
    name = "档案" * 20
    result = truncate_name(name, 10)
    assert len(result) == 10
    assert result.endswith("…")
    # Every remaining character must be a valid, whole codepoint from the source.
    assert all(ch in name or ch == "…" for ch in result)
