# Navigation

## Directory Navigation

| Key | Action |
|-----|--------|
| Enter | Enter selected directory |
| Backspace | Go to parent directory |
| Up / Down | Move cursor |
| Home | Jump to first entry |
| End | Jump to last entry |
| Page Up / Page Down | Scroll by page |

If you attempt to enter a directory without permission, an error message is displayed and you stay in the current directory.

Symlinks are followed for navigation and displayed with a 🔗 icon in the file list.

## Quick Filter

Start typing to activate the quick filter:

1. Type any characters — the file list filters in real-time (case-insensitive substring match)
2. **Escape** — clear the filter and restore the full listing
3. **Enter** — navigate to the selected entry and clear the filter

## Sorting

Files can be sorted by four fields:

| Field | Description |
|-------|-------------|
| Name | Alphabetical by filename |
| Size | By file size |
| Date | By last modified date |
| Extension | By file extension |

Activating sort on the same field toggles between ascending (▲) and descending (▼).

**Directories are always listed before files**, regardless of the active sort field or direction.
