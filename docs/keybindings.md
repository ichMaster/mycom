# Key Bindings

Every binding is resolved through one keymap registry (`mycom/keymap.py`): a `Command`
dataclass maps `action -> key(s) -> context -> label -> slot`. `mycom/app.py` builds Textual's
runtime bindings from this registry (`App.bind`) instead of hard-coding key strings, and the key
bar (below) is generated from the same registry's `slot` field — the F9 menus (v1.8) will be
too — so labels can never drift from actual bindings.

Three actions (`switch_panel`, `open`, `go_up`) are handled in `MyComApp.on_key` instead of
`App.bind`, because they must intercept the key before Textual's own widget-level bindings see
it — the focused `DataTable` already claims `enter` for its own cursor-select action, and `Tab`
is the framework's default focus-cycling key.

## Implemented

| Key | Action | Behavior |
|-----|--------|----------|
| `Tab` | `switch_panel` | Switch the active panel |
| `Enter` | `open` | Enter a directory, or go up on `..` |
| `Backspace` | `go_up` | Go to the parent directory |
| `Ctrl+PageUp` | `go_up` | Go to the parent directory (alias) |
| `Ctrl+U` | `panel_swap` | Swap both panels' paths and cursor positions |
| `Ctrl+Right` | `resize_grow` | Grow the active panel (30% → 50% → 70%) |
| `Ctrl+Left` | `resize_shrink` | Shrink the active panel (70% → 50% → 30%) |
| `Ctrl+1` | `view_brief` | Brief view mode (names only, multi-column) |
| `Ctrl+2` | `view_full` | Full view mode (name/size/modified) |
| `Ctrl+3` | `view_wide` | Wide view mode (name/size) |
| `Ctrl+F3` | `sort_name` | Sort by name |
| `Ctrl+F4` | `sort_ext` | Sort by extension |
| `Ctrl+F5` | `sort_mtime` | Sort by modified date |
| `Ctrl+F6` | `sort_size` | Sort by size |
| `F10`, `Ctrl+Q` | `quit` | Quit |

Notes:

- Going up (`Backspace`/`Ctrl+PageUp`) restores the cursor onto the directory you just left; if
  that entry is gone, the cursor falls back to the first row.
- `Ctrl+U` swaps paths and cursor positions only — there is no selection model yet (lands v0.3),
  so nothing to swap there.
- Pressing the active sort key again reverses direction. The panel header shows a `▲`/`▼` glyph
  on the sorted column in Full/Wide modes (Brief has no per-file headers, so no glyph).
- Resize and view-mode state are in-memory only for v0.1 — they reset on restart until the
  state DB lands (v0.3) and starts persisting per-panel state.

## Reserved, not yet functional

`F1` (`help`), `F3` (`view`), `F4` (`edit`), `F5` (`copy`), `F6` (`move`), `F7` (`mkdir`), `F8`
(`delete`) are already declared in the keymap registry — pressing them is a safe no-op today.
They gain handlers with file operations (v0.4) and the viewer/editor (v0.6).

## Key bar

`mycom/widgets/status_bar.py`'s `StatusBar` renders the ten F1-F10 slots from
`Keymap.key_bar_slots("panel")` — each `Command` in the registry declares a `slot: int | None`
(FAR's F1-F10 convention; `None` for actions with no key-bar presence, e.g. `switch_panel` or the
sort/view/resize keys). A slot with no assigned action renders empty rather than a stale label.
Clicking a slot calls `App.run_action` with the same action name its key would — currently a
no-op for the reserved actions above, exactly like pressing the key itself.

## Dialogs

Every dialog (`mycom/widgets/dialog.py`) is a subclass of `DialogKit`, the one modal engine every
dialog builds on:

- `Tab`/`Shift+Tab` cycle focus through every focusable widget (Textual's default chain,
  including a text `Input` if the dialog has one).
- `Left`/`Up`/`Right`/`Down` cycle focus among the dialog's **buttons only** — they never land on
  an `Input`, so keyboard-only navigation can't get stranded there (an `Input`'s own arrow keys
  move the text cursor while it has focus, as expected).
- A button's hotkey letter (shown underlined) activates it: bare on a plain keypress when no
  `Input` is focused, or with `Alt+letter` unconditionally. Two buttons in the same dialog can't
  share a hotkey — `DialogKit` raises at construction if they do.
- `Enter` activates the dialog's default button; `Esc` always dismisses safely with a
  caller-supplied cancel value.
- Dialogs stack (Textual's native `ModalScreen` behavior) — a dialog can open another (e.g. an
  error) on top of itself.

## Overriding a binding

Any action name in the registry can be overridden in `config.toml`:

```toml
[keybindings]
copy = "ctrl+c"
quit = "ctrl+q"
```

An override for an action name that doesn't exist in the registry is silently ignored (same
behavior as the pre-registry `KeyBindings` class it replaced).
