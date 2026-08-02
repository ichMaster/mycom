# Configuration

MyCom reads `~/.config/mycom/config.toml` at startup. If the file doesn't exist, built-in
defaults are used. Config is user-authored and read-only to the app — MyCom never writes to it.
Edits take effect at the next start.

## `[general]`

| Key | Default | Wired? |
|-----|---------|--------|
| `show_hidden` | `false` | Yes — both panels start with hidden files shown/hidden accordingly |
| `confirm_delete` | `true` | Not yet — arrives with delete (v0.4) |
| `default_sort` | `"name"` | Yes — `"name"` \| `"extension"` \| `"date"` \| `"size"`; an unrecognized value falls back to `"name"` and logs a `WARNING` |
| `default_sort_direction` | `"asc"` | Yes — `"asc"` \| `"desc"` |

## `[keybindings]`

Overrides any action name declared in the keymap registry — see
[Key Bindings](keybindings.md#overriding-a-binding). An override for an unknown action name is
ignored.

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
