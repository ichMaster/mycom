"""Shared test helpers."""

from __future__ import annotations

from textual.app import App

from mycom.theme import FAR_CLASSIC_THEME


class ThemedApp(App):
    """A minimal Textual App with the FAR classic theme registered.

    Any test harness that mounts MyCom widgets referencing theme CSS
    variables ($panel-bg, $dialog-fg, ...) needs a themed App — those
    variables only resolve against a running App's active theme.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.register_theme(FAR_CLASSIC_THEME)
        self.theme = "far-classic"
