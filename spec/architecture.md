# MyCom — Architecture

## Technology Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Language       | Python 3.11+                        |
| TUI Framework  | Textual                             |
| Terminal Embed | pyte (terminal emulator) + PTY      |
| LLM Client     | Anthropic Python SDK (Claude API)   |
| Config         | TOML                                |
| Packaging      | pip / pyproject.toml                |

## High-Level Structure

```
mycom/
├── app.py                 # Application entry point, Textual App subclass
├── config.py              # Configuration loading (TOML)
├── panels/
│   ├── base.py            # Base panel interface
│   ├── file_browser.py    # Dual-panel file browser
│   ├── terminal.py        # Embedded terminal panel
│   └── llm_chat.py        # LLM chat panel
├── operations/
│   ├── file_ops.py        # Copy, move, rename, delete
│   ├── search.py          # Quick search / filter
│   └── sort.py            # Sorting logic
├── plugins/
│   ├── registry.py        # Plugin discovery and registration
│   ├── viewer/
│   │   ├── base.py        # Viewer plugin interface
│   │   └── text.py        # Default text viewer
│   └── editor/
│       ├── base.py        # Editor plugin interface
│       └── text.py        # Default text editor
├── widgets/
│   ├── command_line.py    # Bottom command line widget
│   ├── file_list.py       # File listing table widget
│   ├── status_bar.py      # Status bar with hotkey hints
│   └── dialog.py          # Confirmation / input dialogs
├── llm/
│   ├── client.py          # Claude API client wrapper
│   └── context.py         # File manager context builder for LLM
└── utils/
    ├── fs.py              # Filesystem helpers
    └── keys.py            # Key binding definitions
```

## Core Concepts

### Panel System

The application is organized around a **panel system**. The main area is split into two panels (left and right). Each panel is an independent container that can host one of three modes:

```
┌─────────────────────────┬─────────────────────────┐
│                         │                         │
│      Left Panel         │      Right Panel        │
│   (any panel mode)      │   (any panel mode)      │
│                         │                         │
│                         │                         │
├─────────────────────────┴─────────────────────────┤
│ Command Line                                      │
├───────────────────────────────────────────────────┤
│ F1 Help  F3 View  F4 Edit  F5 Copy  F6 Move ...  │
└───────────────────────────────────────────────────┘
```

**Panel modes:**

| Mode         | Description                                      |
|--------------|--------------------------------------------------|
| File Browser | Directory listing with navigation and operations |
| Terminal     | Full interactive terminal (PTY-backed)           |
| LLM Chat    | Context-aware Claude chat interface              |

Panels are swappable at runtime. The user can press a hotkey to cycle a panel's mode or switch it to a specific mode.

### Plugin Architecture

Viewers and editors use a plugin system based on Python entry points and a simple registration API.

**Plugin interface (viewer example):**

```python
class ViewerPlugin:
    name: str                      # Display name
    extensions: list[str]          # Supported file extensions
    mime_types: list[str]          # Supported MIME types (optional)

    def can_handle(self, path: Path) -> bool: ...
    def render(self, path: Path) -> Widget: ...
```

**Plugin discovery:**
1. Built-in plugins are registered by default (text viewer, text editor).
2. External plugins are discovered via Python entry points (`mycom.viewers`, `mycom.editors`).
3. User can override plugin priority in config.

**Plugin resolution order:**
1. User-configured override for the extension
2. Highest-priority plugin that reports `can_handle() == True`
3. Default text viewer/editor as fallback

### Embedded Terminal

The terminal panel embeds a real PTY (pseudo-terminal) using Python's `pty` module and renders output via **pyte** (a terminal emulator library). This allows full interactive shell sessions including programs like vim, htop, or ssh.

Key design points:
- Each terminal panel owns its own PTY subprocess.
- Input is forwarded from Textual key events to the PTY.
- Output is read asynchronously and rendered into a Textual widget.
- Terminal state (scrollback, cursor) is managed by pyte.

### LLM Chat Integration

The LLM chat panel connects to the Claude API and provides a conversational interface.

**Context injection:**
- Current working directory of the active file browser panel
- List of selected files (names, sizes, types)
- On-demand file content reading (user can say "read file X" and the content is sent as context)

**Message flow:**
```
User input → Context builder → Claude API → Response → Chat widget
```

The context builder assembles a system prompt that includes the file manager state. Conversation history is maintained per chat session.

### Command Line

A persistent input widget at the bottom of the screen. Commands typed here are executed in the shell, with output shown in a transient overlay or piped to the active panel. The working directory is synced with the active file browser panel.

### Configuration

Configuration is stored in `~/.config/mycom/config.toml`:

```toml
[general]
show_hidden = false
confirm_delete = true

[keybindings]
copy = "f5"
move = "f6"
delete = "f8"
view = "f3"
edit = "f4"
terminal_toggle = "ctrl+t"
llm_toggle = "ctrl+l"

[llm]
api_key_env = "ANTHROPIC_API_KEY"
model = "claude-sonnet-4-6"
max_context_files = 10

[plugins.viewers]
".json" = "json-pretty-viewer"
".md" = "markdown-viewer"

[plugins.editors]
".py" = "default-text-editor"
```

## Data Flow

```
Keyboard Input
     │
     ▼
┌──────────┐     ┌──────────────┐
│ Textual  │────▶│ Active Panel │
│ App      │     └──────┬───────┘
└──────────┘            │
                        ├── File Browser → file_ops / viewer / editor
                        ├── Terminal     → PTY subprocess
                        └── LLM Chat    → Claude API client
```

## Error Handling

- File operations show confirmation dialogs before destructive actions.
- Permission errors are displayed inline, never crash the app.
- LLM API errors (rate limits, network) show a message in the chat panel with retry option.
- Terminal subprocess crashes are caught and allow respawn.
