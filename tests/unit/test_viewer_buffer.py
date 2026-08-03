"""Tests for mycom.viewer.buffer.ViewerBuffer."""

from __future__ import annotations

import resource
import sys
import time

from mycom.viewer.buffer import ViewerBuffer


def _rss_bytes() -> int:
    # ru_maxrss is KB on Linux, bytes on macOS/BSD.
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def _write_large_text_file(path, target_size: int) -> None:
    block = "".join(
        f"line {i:08d} - the quick brown fox jumps over the lazy dog\n" for i in range(2000)
    ).encode("utf-8")
    with open(path, "wb") as f:
        written = 0
        while written < target_size:
            f.write(block)
            written += len(block)


def test_empty_file_reads_nothing(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_bytes(b"")
    buf = ViewerBuffer(p)
    try:
        assert buf.size == 0
        assert buf.eof_offset == 0
        assert buf.read_lines_forward(0, 10) == ([], 0)
        assert buf.read_lines_backward(0, 10) == ([], 0)
    finally:
        buf.close()


def test_size_and_eof_offset(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"abc\ndef\n")
    buf = ViewerBuffer(p)
    try:
        assert buf.size == 8
        assert buf.eof_offset == 8
    finally:
        buf.close()


def test_forward_read_from_start(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo\nthree\n")
    buf = ViewerBuffer(p)
    try:
        lines, next_offset = buf.read_lines_forward(0, 2)
        assert lines == ["one", "two"]
        assert next_offset == 8  # just past "two\n"
    finally:
        buf.close()


def test_forward_read_chains_via_returned_offset(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo\nthree\n")
    buf = ViewerBuffer(p)
    try:
        lines1, offset = buf.read_lines_forward(0, 2)
        lines2, offset = buf.read_lines_forward(offset, 2)
        assert lines1 == ["one", "two"]
        assert lines2 == ["three"]
        assert offset == buf.eof_offset
    finally:
        buf.close()


def test_forward_read_last_line_without_trailing_newline(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo")
    buf = ViewerBuffer(p)
    try:
        lines, offset = buf.read_lines_forward(0, 10)
        assert lines == ["one", "two"]
        assert offset == buf.size
    finally:
        buf.close()


def test_forward_read_at_eof_returns_empty(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")
    buf = ViewerBuffer(p)
    try:
        assert buf.read_lines_forward(buf.eof_offset, 5) == ([], buf.eof_offset)
    finally:
        buf.close()


def test_backward_read_from_end_matches_forward(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo\nthree\n")
    buf = ViewerBuffer(p)
    try:
        forward_lines, _ = buf.read_lines_forward(0, 10)
        backward_lines, start = buf.read_lines_backward(buf.eof_offset, 10)
        assert backward_lines == forward_lines
        assert start == 0
    finally:
        buf.close()


def test_backward_read_partial_window(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo\nthree\nfour\n")
    buf = ViewerBuffer(p)
    try:
        lines, start = buf.read_lines_backward(buf.eof_offset, 2)
        assert lines == ["three", "four"]
        assert start == 8  # offset of "three"
    finally:
        buf.close()


def test_backward_read_near_start_returns_fewer_lines_than_requested(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo\n")
    buf = ViewerBuffer(p)
    try:
        lines, start = buf.read_lines_backward(buf.eof_offset, 10)
        assert lines == ["one", "two"]
        assert start == 0
    finally:
        buf.close()


def test_backward_read_zero_offset_returns_nothing(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\ntwo\n")
    buf = ViewerBuffer(p)
    try:
        assert buf.read_lines_backward(0, 5) == ([], 0)
    finally:
        buf.close()


def test_encoding_valid_utf8_decodes_correctly(tmp_path):
    p = tmp_path / "f.txt"
    p.write_text("héllo wörld\n", encoding="utf-8")
    buf = ViewerBuffer(p)
    try:
        assert buf.encoding == "utf-8"
        lines, _ = buf.read_lines_forward(0, 1)
        assert lines == ["héllo wörld"]
    finally:
        buf.close()


def test_encoding_invalid_utf8_falls_back_without_raising(tmp_path):
    p = tmp_path / "f.txt"
    # A lone invalid continuation byte in otherwise-plausible text: not
    # "binary-ish" enough to trip the latin-1 heuristic, so it stays in
    # utf-8 mode and must decode via errors="replace" instead of raising.
    p.write_bytes(b"hello \xff world\n")
    buf = ViewerBuffer(p)
    try:
        lines, _ = buf.read_lines_forward(0, 1)
        assert len(lines) == 1
        assert "hello" in lines[0]
    finally:
        buf.close()


def test_encoding_embedded_nul_uses_latin1_fallback(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"\x00\x01\x02binary\x00data\n")
    buf = ViewerBuffer(p)
    try:
        assert buf.encoding == "latin-1"
        lines, _ = buf.read_lines_forward(0, 1)
        assert len(lines) == 1  # never raises
    finally:
        buf.close()


def test_context_manager_closes_underlying_resources(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"one\n")
    with ViewerBuffer(p) as buf:
        assert buf.read_lines_forward(0, 1) == (["one"], 4)
    # Second close() must not raise (idempotent close via __exit__ already ran).
    buf.close()


def test_backward_read_bounded_by_lookback_cap_on_pathologically_long_line(tmp_path):
    p = tmp_path / "longline.txt"
    preamble = b"preamble\n"
    huge_line = b"A" * 6_000_000  # bigger than the 4MB lookback cap
    p.write_bytes(preamble + huge_line)

    buf = ViewerBuffer(p)
    try:
        # Position well inside the huge line, far enough from its real start
        # (offset 9) that a full backward scan to find it would exceed the cap.
        offset = len(preamble) + 5_000_000
        start = time.monotonic()
        lines, start_offset = buf.read_lines_backward(offset, 5)
        elapsed = time.monotonic() - start
    finally:
        buf.close()

    assert elapsed < 1.0
    # Bounded: did not scan all the way back to the real line start (9).
    assert start_offset > len(preamble)
    assert len(lines) == 1
    assert len(lines[0]) <= 4 * 1024 * 1024


def test_backward_read_finds_real_boundary_within_lookback_range(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"preamble\n" + b"B" * 1000 + b"\n")
    buf = ViewerBuffer(p)
    try:
        lines, start = buf.read_lines_backward(buf.eof_offset, 1)
        assert start == 9  # real boundary right after "preamble\n"
        assert lines == ["B" * 1000]
    finally:
        buf.close()


def test_large_file_opens_and_reads_ends_quickly(tmp_path):
    big = tmp_path / "big.log"
    _write_large_text_file(big, 300 * 1024 * 1024)

    start = time.monotonic()
    buf = ViewerBuffer(big)
    try:
        lines, _ = buf.read_lines_forward(0, 50)
        elapsed_open = time.monotonic() - start
        assert len(lines) == 50

        start_end = time.monotonic()
        tail, _ = buf.read_lines_backward(buf.eof_offset, 50)
        elapsed_end = time.monotonic() - start_end
    finally:
        buf.close()

    assert elapsed_open < 0.3
    assert elapsed_end < 0.3
    assert len(tail) == 50


def test_rereading_the_same_window_does_not_accumulate_memory(tmp_path):
    """`ViewerBuffer` retains no history across reads — re-scrolling the same
    small region thousands of times must not grow memory with the call
    count. (Sequentially touching *new*, previously-unvisited regions of an
    mmap necessarily grows the OS's resident page-cache for this process —
    that's the kernel keeping recently-used file pages around, reclaimable
    under pressure, not a leak in our code — so that scenario isn't a useful
    growth assertion here; revisiting the *same* pages is.)
    """
    big = tmp_path / "big.log"
    _write_large_text_file(big, 300 * 1024 * 1024)

    buf = ViewerBuffer(big)
    try:
        buf.read_lines_forward(0, 50)  # warm up mmap paging/imports
        baseline = _rss_bytes()

        for _ in range(5000):
            lines, _ = buf.read_lines_forward(0, 50)
            assert len(lines) == 50

        growth = _rss_bytes() - baseline
    finally:
        buf.close()

    assert growth < 20 * 1024 * 1024


def test_paging_forward_through_large_file_completes_quickly(tmp_path):
    big = tmp_path / "big.log"
    _write_large_text_file(big, 300 * 1024 * 1024)

    buf = ViewerBuffer(big)
    try:
        start = time.monotonic()
        offset = 0
        pages = 0
        while offset < buf.size and pages < 200_000:
            lines, offset = buf.read_lines_forward(offset, 100)
            if not lines:
                break
            pages += 1
        elapsed = time.monotonic() - start
    finally:
        buf.close()

    assert pages > 0
    assert elapsed < 10.0
