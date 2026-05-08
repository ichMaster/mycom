# Keybindings

MyCom is keyboard-first. All operations are accessible via hotkeys.

## Default Bindings

| Action | Default Key | Description |
|--------|-------------|-------------|
| Help | F1 | Show help screen |
| View | F3 | View selected file |
| Edit | F4 | Edit selected file |
| Copy | F5 | Copy selected files |
| Move | F6 | Move / rename selected files |
| MkDir | F7 | Create new directory |
| Delete | F8 | Delete selected files |
| Quit | F10 | Exit MyCom |
| Switch Panel | Tab | Toggle active panel |
| Open | Enter | Enter directory or open file |
| Go Up | Backspace | Navigate to parent directory |
| First | Home | Jump to first file |
| Last | End | Jump to last file |
| Terminal | Ctrl+T | Toggle terminal panel mode |
| LLM Chat | Ctrl+L | Toggle LLM chat panel mode |

## Customizing

Override any binding in `~/.config/mycom/config.toml`:

```toml
[keybindings]
copy = "ctrl+c"
quit = "ctrl+q"
delete = "delete"
```

Only known action names are accepted. Unknown action names in the config are ignored.
