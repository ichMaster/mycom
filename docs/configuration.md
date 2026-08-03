# Configuration

MyCom reads `~/.config/mycom/config.toml` at startup. If the file doesn't exist, built-in
defaults are used. Config is user-authored and read-only to the app — MyCom never writes to it.
Edits take effect at the next start.

## `[general]`

| Key | Default | Wired? |
|-----|---------|--------|
| `show_hidden` | `false` | Yes — first-run default; once `state.db` has a saved value it wins on later starts (see [Persistence](#persistence)) |
| `confirm_delete` | `true` | Yes — `false` skips F8's routine "Delete X?" prompt only; the non-empty-directory and read-only-file safety warnings always show regardless |
| `default_sort` | `"name"` | Yes — `"name"` \| `"extension"` \| `"date"` \| `"size"`; an unrecognized value falls back to `"name"` and logs a `WARNING`. First-run default; `state.db` wins once populated. |
| `default_sort_direction` | `"asc"` | Yes — `"asc"` \| `"desc"`. First-run default; `state.db` wins once populated. |

## `[keybindings]`

Overrides any action name declared in the keymap registry — see
[Key Bindings](keybindings.md#overriding-a-binding). An override for an unknown action name is
ignored.

## `[editor]`

| Key | Default | Wired? |
|-----|---------|--------|
| `external_default` | `false` | Yes (v0.6) — `true` makes plain `F4` always hand the cursor file to `$EDITOR` (via `App.suspend()`) instead of opening MyCom's own built-in editor; `Alt+F4` does this unconditionally regardless of this setting — see [Editor](keybindings.md#editor-v06) |

## `[llm]`

Not yet used — reserved for the AI command palette (v0.7).

## `[plugins]`

Not yet used — reserved for pluggable viewer/editor associations.

## Example

```toml
[general]
show_hidden = false
default_sort = "size"
default_sort_direction = "desc"

[keybindings]
copy = "ctrl+c"
quit = "ctrl+q"

[editor]
external_default = true
```

## Logging

MyCom never logs to stdout/stderr — it owns the whole terminal screen (Textual), and writing
there would corrupt the display. Logging is file-based, off by default (`WARNING` level), and
configured entirely through environment variables (not `config.toml`, since it's an operational
concern rather than a user preference):

| Variable | Default |
|----------|---------|
| `MYCOM_LOG_LEVEL` | `WARNING` |
| `MYCOM_LOG_FILE` | `~/.config/mycom/mycom.log` |

```bash
MYCOM_LOG_LEVEL=DEBUG MYCOM_LOG_FILE=/tmp/mycom.log uv run mycom
```

## Persistence

`mycom/state.py::StateDB` — a separate SQLite database (WAL mode) at `~/.config/mycom/state.db`,
app-owned and never hand-edited (distinct from the user-authored `config.toml` above). Schema is
versioned with migrations; a corrupt or missing file is recreated silently — startup is never
blocked by state, and only opening/validating the file counts as "corrupt" (a transient error
partway through, e.g. a locked database, does **not** wipe existing data).

Restored at startup, per panel: path (with a vanished-path fallback to the nearest existing
ancestor, then `$HOME`), sort field/direction, view mode. Restored globally: the hidden-files
toggle, which panel is active, and the panel split. Saves are debounced (~500ms after a
state-affecting action) and flushed synchronously on quit — a failed final save is logged, never
crashes the quit.

Deleting `state.db` is always safe: the next start just falls back to `config.toml`'s defaults
(or built-in defaults if that's absent too).
