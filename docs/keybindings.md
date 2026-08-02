# Key Bindings

Every binding is resolved through one keymap registry (`mycom/keymap.py`): a `Command`
dataclass maps `action -> key(s) -> context -> label`. `mycom/app.py` builds Textual's runtime
bindings from this registry (`App.bind`) instead of hard-coding key strings — the same registry
will drive the F0.14 key bar (v0.2) and the F9 menus (v1.8), so labels can never drift from
actual bindings.

Three actions (`switch_panel`, `open`, `go_up`) are handled in `MyComApp.on_key` instead of
`App.bind`, because they must intercept the key before Textual's own widget-level bindings see
it — the focused `DataTable` already claims `enter` for its own cursor-select action, and `Tab`
is the framework's default focus-cycling key.

## Implemented (v0.1)

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

## Overriding a binding

Any action name in the registry can be overridden in `config.toml`:

```toml
[keybindings]
copy = "ctrl+c"
quit = "ctrl+q"
```

An override for an action name that doesn't exist in the registry is silently ignored (same
behavior as the pre-registry `KeyBindings` class it replaced).
