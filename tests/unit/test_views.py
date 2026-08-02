"""Tests for mycom.panels.views (view mode -> column spec mapping)."""

from mycom.panels.views import FIELD_HEADERS, VIEW_SPECS, ViewMode


def test_brief_has_no_headers_and_no_fields():
    spec = VIEW_SPECS[ViewMode.BRIEF]
    assert spec.show_headers is False
    assert spec.fields == ()


def test_full_shows_name_size_modified():
    spec = VIEW_SPECS[ViewMode.FULL]
    assert spec.show_headers is True
    assert spec.fields == ("name", "size", "modified")


def test_wide_shows_name_size_only():
    spec = VIEW_SPECS[ViewMode.WIDE]
    assert spec.show_headers is True
    assert spec.fields == ("name", "size")


def test_every_field_has_a_header():
    for spec in VIEW_SPECS.values():
        for field in spec.fields:
            assert field in FIELD_HEADERS
