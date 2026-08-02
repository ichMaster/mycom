"""Unit tests for mycom.utils.masks.match_any (MC-020)."""

from mycom.utils.masks import match_any


def test_single_pattern():
    assert match_any("readme.py", "*.py")
    assert not match_any("readme.md", "*.py")


def test_multi_pattern_semicolon():
    assert match_any("a.py", "*.py;*.md")
    assert match_any("a.md", "*.py;*.md")
    assert not match_any("a.txt", "*.py;*.md")


def test_multi_pattern_comma():
    assert match_any("a.py", "*.py,*.md")
    assert match_any("a.md", "*.py,*.md")


def test_case_insensitive():
    assert match_any("README.PY", "*.py")
    assert match_any("readme.py", "*.PY")


def test_empty_pattern_list_matches_nothing():
    assert not match_any("a.py", "")
    assert not match_any("a.py", "   ")


def test_star_matches_everything():
    assert match_any("anything.at.all", "*")


def test_whitespace_around_patterns_ignored():
    assert match_any("a.py", " *.py ; *.md ")
