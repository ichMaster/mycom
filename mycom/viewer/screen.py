"""Read-only, windowed file viewer screen (F0.12) — F3."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from mycom.keymap import Keymap
from mycom.utils.fs import format_size
from mycom.viewer.buffer import ViewerBuffer
from mycom.widgets.status_bar import StatusBar

_DEFAULT_PAGE_LINES = 50
_CHROME_ROWS = 2  # info line + key bar


class ViewerScreen(Screen[str | None]):
    """`F3`: instant, read-only view of a file at any size.

    Not modal — a full screen like the panels, matching FAR's own full-screen
    viewer. The visible window is tracked purely by file *offset*
    (`_top_offset`), never a line index, so the wrap toggle — which changes
    how many file lines fit on screen — never loses the reader's place.

    Dismisses with `None` on a plain close (`F3`/`F10`/`Esc`), or `"edit"` on
    `F6` — the caller (`MyComApp`) interprets that result rather than this
    screen reaching into the editor directly, avoiding a forward-reference
    between the two screen modules.
    """

    DEFAULT_CSS = """
    ViewerScreen {
        background: $panel-bg;
    }
    ViewerScreen > #viewer-info {
        dock: top;
        height: 1;
        background: $pathbar-active-bg;
        color: $pathbar-active-fg;
        padding: 0 1;
    }
    ViewerScreen #viewer-body {
        width: 1fr;
        height: 1fr;
        color: $panel-fg;
    }
    """

    def __init__(self, path: Path, keymap: Keymap) -> None:
        super().__init__()
        self._path = path
        self._keymap = keymap
        self._buffer = ViewerBuffer(path)
        self._top_offset = 0
        self._wrap = False
        self._info = Static(id="viewer-info")
        self._body = Static(id="viewer-body")

    def compose(self) -> ComposeResult:
        yield self._info
        yield self._body
        yield StatusBar(keymap=self._keymap, scope="viewer")

    def on_mount(self) -> None:
        self._render_window()

    def on_unmount(self) -> None:
        self._buffer.close()

    def on_resize(self, event: object) -> None:
        self._render_window()

    def on_key(self, event) -> None:
        actions = self._keymap.actions_for_key(event.key, context="viewer")
        if not actions:
            return
        event.stop()
        event.prevent_default()
        {
            "viewer_line_up": self._nav_line_up,
            "viewer_line_down": self._nav_line_down,
            "viewer_page_up": self._nav_page_up,
            "viewer_page_down": self._nav_page_down,
            "viewer_home": self._nav_home,
            "viewer_end": self._nav_end,
            "viewer_wrap": self.toggle_wrap,
            "viewer_close": self.close_viewer,
            "viewer_edit": self.request_edit,
        }[actions[0]]()

    def _page_lines(self) -> int:
        height = self.size.height
        return max(1, height - _CHROME_ROWS) if height > _CHROME_ROWS else _DEFAULT_PAGE_LINES

    def _render_window(self) -> None:
        lines, _ = self._buffer.read_lines_forward(self._top_offset, self._page_lines())
        text = Text("\n".join(lines), no_wrap=not self._wrap)
        if not self._wrap:
            text.overflow = "crop"
        self._body.update(text)
        self._update_info()

    def _update_info(self) -> None:
        size = self._buffer.size
        percent = 0 if size == 0 else min(100, int(self._top_offset / size * 100))
        self._info.update(
            f"{self._path.name}  {format_size(size)}  offset {self._top_offset}  {percent}%"
        )

    def _nav_line_down(self) -> None:
        _, next_offset = self._buffer.read_lines_forward(self._top_offset, 1)
        self._top_offset = next_offset
        self._render_window()

    def _nav_line_up(self) -> None:
        _, start = self._buffer.read_lines_backward(self._top_offset, 1)
        self._top_offset = start
        self._render_window()

    def _nav_page_down(self) -> None:
        _, next_offset = self._buffer.read_lines_forward(self._top_offset, self._page_lines())
        self._top_offset = next_offset
        self._render_window()

    def _nav_page_up(self) -> None:
        _, start = self._buffer.read_lines_backward(self._top_offset, self._page_lines())
        self._top_offset = start
        self._render_window()

    def _nav_home(self) -> None:
        self._top_offset = 0
        self._render_window()

    def _nav_end(self) -> None:
        _, start = self._buffer.read_lines_backward(self._buffer.eof_offset, self._page_lines())
        self._top_offset = start
        self._render_window()

    def toggle_wrap(self) -> None:
        self._wrap = not self._wrap
        self._render_window()

    def close_viewer(self) -> None:
        self.dismiss(None)

    def request_edit(self) -> None:
        self.dismiss("edit")

    @property
    def top_offset(self) -> int:
        return self._top_offset
