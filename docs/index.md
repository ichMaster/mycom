# MyCom Documentation

This folder documents the **actual, implemented code** — not the design.

## Status: v0.3 — Selection model, hidden files, SQLite persistence

Dual panels navigate the filesystem with a data-driven keymap registry: Tab/Enter/Backspace
navigation, `Ctrl+U` panel swap (paths, cursor, **and selection**), cursor-restore on going up, an
error dialog instead of a silent-empty-panel on an unreadable/vanished/replaced directory,
resizable panels, three view modes (Brief/Full/Wide), and the four FAR sort keys with a header
direction glyph.

The Far classic palette lives in one theme file (`mycom/theme.py`) that every widget references
by CSS variable — no hard-coded colors anywhere. Every dialog is built on one keyboard-navigable
modal engine (`DialogKit`): Tab/arrow focus cycling (never stranding you in a text field),
underlined hotkey letters, Enter/Esc, stackable, no two buttons in one dialog sharing a hotkey.
The bottom key bar's ten F-key slots are generated from the same keymap registry that creates the
bindings, so a label can never drift from what a key actually does; unassigned slots render empty.

Per-panel selection (`Ins`/`Space`, mask select/deselect, invert) renders yellow and drives a live
footer count + size; `Ctrl+H` toggles hidden files globally, cursor-preserving. Panel paths, sort,
view mode, and the hidden toggle now survive a restart — persisted to a versioned, WAL-mode SQLite
database (`mycom/state.py`) separate from the user-authored `config.toml`, with a graceful
fallback when a saved path has vanished.

See [Key Bindings](keybindings.md) (incl. selection, the key bar, and the dialog keyboard model)
and [Configuration](configuration.md) (incl. persistence).

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
