"""Tests for mycom.editor.detect."""

from __future__ import annotations

import pytest

from mycom.editor.detect import (
    MAX_EDITABLE_SIZE,
    EolStyle,
    NotEditableError,
    apply_eol,
    detect_eol,
    has_trailing_newline,
    is_binary,
    read_text,
    too_large,
)


def test_detect_eol_pure_lf():
    assert detect_eol("one\ntwo\nthree\n") == EolStyle.LF


def test_detect_eol_pure_crlf():
    assert detect_eol("one\r\ntwo\r\nthree\r\n") == EolStyle.CRLF


def test_detect_eol_empty_defaults_to_lf():
    assert detect_eol("") == EolStyle.LF


def test_detect_eol_single_line_no_newline_defaults_to_lf():
    assert detect_eol("no newline here") == EolStyle.LF


def test_detect_eol_mixed_lf_dominant():
    text = "one\ntwo\nthree\nfour\r\n"  # 3 bare LF, 1 CRLF
    assert detect_eol(text) == EolStyle.MIXED_LF_DOMINANT


def test_detect_eol_mixed_crlf_dominant():
    text = "one\r\ntwo\r\nthree\r\nfour\n"  # 3 CRLF, 1 bare LF
    assert detect_eol(text) == EolStyle.MIXED_CRLF_DOMINANT


def test_detect_eol_mixed_tie_breaks_to_lf():
    text = "one\ntwo\r\n"  # 1 bare LF, 1 CRLF
    assert detect_eol(text) == EolStyle.MIXED_LF_DOMINANT


def test_has_trailing_newline_true():
    assert has_trailing_newline("line\n") is True


def test_has_trailing_newline_false():
    assert has_trailing_newline("line") is False


def test_has_trailing_newline_empty_string_is_false():
    assert has_trailing_newline("") is False


def test_apply_eol_lf_is_a_no_op():
    text = "one\ntwo\n"
    assert apply_eol(text, EolStyle.LF) == text


def test_apply_eol_crlf_converts_every_newline():
    text = "one\ntwo\nthree"
    assert apply_eol(text, EolStyle.CRLF) == "one\r\ntwo\r\nthree"


def test_apply_eol_mixed_lf_dominant_saves_as_pure_lf():
    text = "one\ntwo\n"
    assert apply_eol(text, EolStyle.MIXED_LF_DOMINANT) == text


def test_apply_eol_mixed_crlf_dominant_saves_as_pure_crlf():
    text = "one\ntwo\n"
    assert apply_eol(text, EolStyle.MIXED_CRLF_DOMINANT) == "one\r\ntwo\r\n"


def test_apply_eol_preserves_absence_of_trailing_newline():
    text = "one\ntwo"
    assert apply_eol(text, EolStyle.CRLF) == "one\r\ntwo"
    assert not apply_eol(text, EolStyle.CRLF).endswith("\n")


def test_apply_eol_preserves_presence_of_trailing_newline():
    text = "one\ntwo\n"
    result = apply_eol(text, EolStyle.CRLF)
    assert result.endswith("\r\n")


def test_is_binary_detects_embedded_nul():
    assert is_binary(b"hello\x00world") is True


def test_is_binary_false_for_plain_text():
    assert is_binary(b"just some ordinary ASCII text\n") is False


def test_is_binary_empty_sample_is_false():
    assert is_binary(b"") is False


def test_is_binary_high_control_byte_ratio():
    assert is_binary(bytes(range(0, 32)) * 10) is True


def test_too_large_boundary_just_under(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"x" * (MAX_EDITABLE_SIZE - 1))
    assert too_large(p) is False


def test_too_large_boundary_exact_size_is_not_too_large(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"x" * MAX_EDITABLE_SIZE)
    assert too_large(p) is False


def test_too_large_boundary_just_over(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"x" * (MAX_EDITABLE_SIZE + 1))
    assert too_large(p) is True


def test_read_text_returns_normalized_text_and_metadata(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\r\ntwo\r\nthree\r\n")
    text, eol, trailing = read_text(p)
    assert text == "one\ntwo\nthree\n"
    assert eol == EolStyle.CRLF
    assert trailing is True


def test_read_text_no_trailing_newline(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo")
    text, eol, trailing = read_text(p)
    assert text == "one\ntwo"
    assert eol == EolStyle.LF
    assert trailing is False


def test_read_text_raises_not_editable_for_binary(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"\x00\x01\x02binary data")
    with pytest.raises(NotEditableError) as exc_info:
        read_text(p)
    assert exc_info.value.reason == "binary"


def test_read_text_raises_not_editable_for_invalid_utf8(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"valid start \xff\xfe invalid utf-8 tail")
    with pytest.raises(NotEditableError) as exc_info:
        read_text(p)
    assert exc_info.value.reason == "binary"


def test_read_text_raises_not_editable_for_too_large(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"x" * (MAX_EDITABLE_SIZE + 1))
    with pytest.raises(NotEditableError) as exc_info:
        read_text(p)
    assert exc_info.value.reason == "too_large"


def test_read_text_valid_utf8_with_multibyte_chars(tmp_path):
    p = tmp_path / "f.txt"
    p.write_text("héllo wörld\n", encoding="utf-8")
    text, eol, trailing = read_text(p)
    assert text == "héllo wörld\n"
    assert eol == EolStyle.LF
    assert trailing is True
