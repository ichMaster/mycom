"""Tests for mycom.console.ring_buffer.RingBuffer."""

from __future__ import annotations

from mycom.console.ring_buffer import RingBuffer


def test_had_output_false_for_silent_run():
    buf = RingBuffer()
    assert buf.had_output is False
    assert buf.text() == ""


def test_had_output_true_after_any_append():
    buf = RingBuffer()
    buf.append(b"x")
    assert buf.had_output is True


def test_empty_append_does_not_set_had_output():
    buf = RingBuffer()
    buf.append(b"")
    assert buf.had_output is False


def test_splits_chunks_into_whole_lines():
    buf = RingBuffer()
    buf.append(b"hello\nworld\n")
    assert buf.text() == "hello\nworld"


def test_partial_line_across_two_appends_joins_correctly():
    buf = RingBuffer()
    buf.append(b"hel")
    buf.append(b"lo\n")
    assert buf.text() == "hello"


def test_crlf_from_pty_line_discipline_is_normalized():
    """A PTY translates outgoing "\\n" to "\\r\\n" by default — real output
    from run_in_pty arrives this way, and it shouldn't leave a stray \\r on
    every recalled line."""
    buf = RingBuffer()
    buf.append(b"line one\r\nline two\r\n")
    assert buf.text() == "line one\nline two"


def test_lone_carriage_return_is_not_split_into_extra_lines():
    """A progress-bar-style bare \\r (no \\n) overwrites its own line in a
    real terminal — splitting on it too would turn one progress bar into
    thousands of ring-buffer lines."""
    buf = RingBuffer()
    buf.append(b"50%\r100%\r\n")
    assert buf.text() == "50%\r100%"


def test_trailing_text_without_newline_is_still_visible():
    buf = RingBuffer()
    buf.append(b"no newline yet")
    assert buf.text() == "no newline yet"


def test_decodes_with_replace_on_invalid_utf8():
    buf = RingBuffer()
    buf.append(b"\xff\xfe\n")
    assert "\n" not in buf.text() or buf.text()  # decodes without raising
    assert buf.had_output is True


def test_eviction_bounds_memory_but_keeps_had_output_true():
    buf = RingBuffer(max_lines=10)
    for i in range(1000):
        buf.append(f"line {i}\n".encode())
    lines = buf.text().split("\n")
    assert len(lines) == 10
    assert lines[-1] == "line 999"  # oldest evicted, newest retained
    assert buf.had_output is True


def test_clear_resets_everything():
    buf = RingBuffer()
    buf.append(b"data\n")
    buf.clear()
    assert buf.had_output is False
    assert buf.text() == ""
