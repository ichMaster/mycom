"""The FAR classic theme: the single source of color for the whole app.

Source: FAR Manager's `colormix.cpp`/`palette.cpp`, confirmed against a live FAR
screenshot (see spec/architecture.md's palette table). Every widget references
these as Textual CSS variables (`$panel-bg`, `$dialog-fg`, ...) — no widget
defines a literal hex color.

Color-depth degradation (truecolor -> 256-color -> 16-color -> monochrome) is
handled entirely by Textual's own rendering pipeline based on the detected
terminal capability (`$COLORTERM`, terminfo, etc.) — MyCom does not hand-roll a
parallel fallback table. `tests/unit/test_theme.py` pins that every themed
foreground/background pair used together stays visually distinct after Rich
downgrades it to the 256-color depth, so a terminal without truecolor support
still renders legible text.
"""

from __future__ import annotations

from textual.theme import Theme

# FAR classic palette, by role. Values match the pre-v0.2 hard-coded hex
# exactly (relocation, not a palette change) and spec/architecture.md's table.
PANEL_BG = "#000080"
PANEL_FG = "#00ffff"
PANEL_BORDER = "#00ffff"
PATHBAR_ACTIVE_BG = "#008080"
PATHBAR_ACTIVE_FG = "#000000"
PATHBAR_INACTIVE_BG = "#000080"
PATHBAR_INACTIVE_FG = "#00ffff"
HEADER_FG = "#ffff00"
CURSOR_BG = "#008080"
CURSOR_FG = "#000000"
SELECTED_FG = "#ffff00"  # not yet consumed — selection model lands in v0.3
KEYBAR_NUMBER_BG = "#000000"
KEYBAR_NUMBER_FG = "#c0c0c0"
KEYBAR_LABEL_BG = "#008080"
KEYBAR_LABEL_FG = "#000000"
DIALOG_BG = "#c0c0c0"
DIALOG_FG = "#000000"
DIALOG_INPUT_BG = "#008080"
DIALOG_INPUT_FG = "#000000"

# Every themed (foreground, background) pair actually rendered together —
# the set test_theme.py checks for post-downgrade distinctness.
FG_BG_PAIRS: tuple[tuple[str, str], ...] = (
    (PANEL_FG, PANEL_BG),
    (PATHBAR_ACTIVE_FG, PATHBAR_ACTIVE_BG),
    (PATHBAR_INACTIVE_FG, PATHBAR_INACTIVE_BG),
    (HEADER_FG, PANEL_BG),
    (CURSOR_FG, CURSOR_BG),
    (SELECTED_FG, PANEL_BG),
    (KEYBAR_NUMBER_FG, KEYBAR_NUMBER_BG),
    (KEYBAR_LABEL_FG, KEYBAR_LABEL_BG),
    (DIALOG_FG, DIALOG_BG),
    (DIALOG_INPUT_FG, DIALOG_INPUT_BG),
)

FAR_CLASSIC_THEME = Theme(
    name="far-classic",
    dark=True,
    primary=PANEL_FG,
    secondary=PATHBAR_ACTIVE_BG,
    background=PANEL_BG,
    surface=PANEL_BG,
    panel=DIALOG_BG,
    accent=HEADER_FG,
    warning=HEADER_FG,
    error="#ff0000",
    success="#00ff00",
    foreground=PANEL_FG,
    variables={
        "panel-bg": PANEL_BG,
        "panel-fg": PANEL_FG,
        "panel-border": PANEL_BORDER,
        "pathbar-active-bg": PATHBAR_ACTIVE_BG,
        "pathbar-active-fg": PATHBAR_ACTIVE_FG,
        "pathbar-inactive-bg": PATHBAR_INACTIVE_BG,
        "pathbar-inactive-fg": PATHBAR_INACTIVE_FG,
        "header-fg": HEADER_FG,
        "cursor-bg": CURSOR_BG,
        "cursor-fg": CURSOR_FG,
        "selected-fg": SELECTED_FG,
        "keybar-number-bg": KEYBAR_NUMBER_BG,
        "keybar-number-fg": KEYBAR_NUMBER_FG,
        "keybar-label-bg": KEYBAR_LABEL_BG,
        "keybar-label-fg": KEYBAR_LABEL_FG,
        "dialog-bg": DIALOG_BG,
        "dialog-fg": DIALOG_FG,
        "dialog-input-bg": DIALOG_INPUT_BG,
        "dialog-input-fg": DIALOG_INPUT_FG,
    },
)
