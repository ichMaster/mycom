"""View mode definitions: Brief / Full / Wide column layouts — data, not subclasses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ViewMode(Enum):
    BRIEF = "brief"
    FULL = "full"
    WIDE = "wide"


@dataclass(frozen=True)
class ColumnSpec:
    """Which fields a view mode shows (besides the leading type icon), and whether it
    renders column headers. Brief has no per-file metadata fields — names only,
    laid out in as many columns as fit the panel width."""

    show_headers: bool
    fields: tuple[str, ...]


VIEW_SPECS: dict[ViewMode, ColumnSpec] = {
    ViewMode.BRIEF: ColumnSpec(show_headers=False, fields=()),
    ViewMode.FULL: ColumnSpec(show_headers=True, fields=("name", "size", "modified")),
    ViewMode.WIDE: ColumnSpec(show_headers=True, fields=("name", "size")),
}

FIELD_HEADERS: dict[str, str] = {
    "name": "Name",
    "size": "Size",
    "modified": "Modified",
}
