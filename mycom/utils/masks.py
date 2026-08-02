"""Minimal glob-list mask matching for v0.3's selection dialogs.

Deliberately not the full masks grammar (exclude parts, `|`) — v1.1 builds
one shared masks engine (documented in spec/mission.md's glossary) that this
dialog will retrofit onto. This is just "`*.py;*.md`"-style include lists.
"""

from __future__ import annotations

import fnmatch
import re

_SPLIT_RE = re.compile(r"[;,]")


def match_any(name: str, pattern_list: str) -> bool:
    """True if `name` matches any pattern in a `;`/`,`-separated list, case-insensitively."""
    patterns = [p.strip() for p in _SPLIT_RE.split(pattern_list) if p.strip()]
    if not patterns:
        return False
    lowered = name.lower()
    return any(fnmatch.fnmatch(lowered, pattern.lower()) for pattern in patterns)
