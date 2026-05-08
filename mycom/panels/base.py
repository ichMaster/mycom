"""Base panel interface for all panel modes."""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from pathlib import Path

from textual.widget import Widget


class PanelMode(Enum):
    FILE_BROWSER = "file_browser"
    TERMINAL = "terminal"
    LLM_CHAT = "llm_chat"


class BasePanel(Widget):
    """Abstract base class for MyCom panels."""

    DEFAULT_CSS = """
    BasePanel {
        height: 1fr;
        border: solid $secondary;
    }
    BasePanel.active {
        border: solid $primary;
    }
    """

    def __init__(self, mode: PanelMode = PanelMode.FILE_BROWSER, **kwargs) -> None:
        super().__init__(**kwargs)
        self._mode = mode

    @property
    def mode(self) -> PanelMode:
        return self._mode

    def activate(self) -> None:
        """Set this panel as the active (focused) panel."""
        self.add_class("active")

    def deactivate(self) -> None:
        """Set this panel as inactive."""
        self.remove_class("active")

    @property
    def is_active(self) -> bool:
        return "active" in self.classes

    @abstractmethod
    def get_current_path(self) -> Path | None:
        """Return the current working directory of this panel, if applicable."""
        ...

    @abstractmethod
    def get_selected_files(self) -> list[Path]:
        """Return the list of selected file paths."""
        ...
