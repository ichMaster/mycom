# Configuration

MyCom is configured via a TOML file at `~/.config/mycom/config.toml`.

If the file does not exist, all defaults are used.

## Config File Format

```toml
[general]
show_hidden = false          # Show hidden files (dotfiles)
confirm_delete = true        # Ask before deleting files
default_sort = "name"        # Sort by: name, size, date, extension
default_sort_direction = "asc"  # asc or desc

[keybindings]
copy = "f5"
move = "f6"
delete = "f8"
view = "f3"
edit = "f4"
mkdir = "f7"
quit = "f10"
terminal_toggle = "ctrl+t"
llm_toggle = "ctrl+l"

[llm]
api_key_env = "ANTHROPIC_API_KEY"   # Env var holding the API key
model = "claude-sonnet-4-6"           # Claude model to use
max_context_files = 10               # Max files sent as context

[plugins.viewers]
".json" = "json-pretty-viewer"
".md" = "markdown-viewer"

[plugins.editors]
".py" = "default-text-editor"
```

## Sections

### `[general]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `show_hidden` | bool | `false` | Show dotfiles in file listings |
| `confirm_delete` | bool | `true` | Prompt before delete operations |
| `default_sort` | string | `"name"` | Default sort field |
| `default_sort_direction` | string | `"asc"` | Default sort direction |

### `[keybindings]`

Override any default key binding. See [Keybindings](keybindings.md) for the full list.

### `[llm]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_key_env` | string | `"ANTHROPIC_API_KEY"` | Environment variable for API key |
| `model` | string | `"claude-sonnet-4-6"` | Claude model ID |
| `max_context_files` | int | `10` | Max files for LLM context |

### `[plugins.viewers]` / `[plugins.editors]`

Map file extensions to plugin names. See the plugin documentation for available plugins.

## Precedence

Config file values override defaults. Unknown keys are silently ignored for forward compatibility.
