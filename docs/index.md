# MyCom Documentation

This folder documents the **actual, implemented code** — not the design.

## Status: v0.1 — Panel core retrofit

Dual panels navigate the filesystem with a data-driven keymap registry: Tab/Enter/Backspace
navigation, `Ctrl+U` panel swap, cursor-restore on going up, an error dialog instead of a
silent-empty-panel on an unreadable/vanished directory, resizable panels, three view modes
(Brief/Full/Wide), and the four FAR sort keys with a header direction glyph. Config-driven
`show_hidden`/default sort, and env-configurable file logging. See
[Key Bindings](keybindings.md) and [Configuration](configuration.md).

File operations, the command line/console, the viewer/editor, the AI command palette, and
Claude Code integration are not built yet — see `spec/roadmap.md` for what ships in which
phase.

As later roadmap phases ship, this section (and its pages) are updated to describe what
actually exists at that point — never what's planned.

The design lives in the repository's `spec/` folder:

- `spec/mission.md` — what MyCom is and its principles
- `spec/roadmap.md` — v0/v1 phases with DoD and tests
- `spec/architecture.md` — components, invariants, package layout
- `spec/far-spec/` — the FAR-derived feature scope and acceptance criteria
