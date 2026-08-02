"""Tests for mycom.theme: palette values and 256-color degradation."""

from __future__ import annotations

from rich.color import Color as RichColor
from rich.color import ColorSystem

from mycom.theme import FAR_CLASSIC_THEME, FG_BG_PAIRS


def test_theme_is_registered_as_dark():
    assert FAR_CLASSIC_THEME.dark is True


def test_theme_variables_cover_every_role():
    expected = {
        "panel-bg",
        "panel-fg",
        "panel-border",
        "pathbar-active-bg",
        "pathbar-active-fg",
        "pathbar-inactive-bg",
        "pathbar-inactive-fg",
        "header-fg",
        "cursor-bg",
        "cursor-fg",
        "selected-fg",
        "keybar-number-bg",
        "keybar-number-fg",
        "keybar-label-bg",
        "keybar-label-fg",
        "dialog-bg",
        "dialog-fg",
        "dialog-input-bg",
        "dialog-input-fg",
    }
    assert expected <= FAR_CLASSIC_THEME.variables.keys()


def test_fg_bg_pairs_distinct_at_truecolor():
    for fg, bg in FG_BG_PAIRS:
        assert fg != bg


def test_fg_bg_pairs_distinct_after_256_color_downgrade():
    """Every themed fg/bg pair must stay visually distinct once downgraded to
    the 256-color (EIGHT_BIT) depth — a terminal without truecolor support
    must never render invisible (fg == bg) text."""
    for fg, bg in FG_BG_PAIRS:
        fg_down = RichColor.parse(fg).downgrade(ColorSystem.EIGHT_BIT)
        bg_down = RichColor.parse(bg).downgrade(ColorSystem.EIGHT_BIT)
        assert fg_down.get_truecolor() != bg_down.get_truecolor(), (
            f"{fg!r} on {bg!r} collapses to the same 256-color value"
        )


def test_fg_bg_pairs_distinct_after_16_color_downgrade():
    """Same check at the even coarser 16-color (STANDARD) depth."""
    for fg, bg in FG_BG_PAIRS:
        fg_down = RichColor.parse(fg).downgrade(ColorSystem.STANDARD)
        bg_down = RichColor.parse(bg).downgrade(ColorSystem.STANDARD)
        assert fg_down.get_truecolor() != bg_down.get_truecolor(), (
            f"{fg!r} on {bg!r} collapses to the same 16-color value"
        )
