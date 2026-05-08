# MyCom — Roadmap

## Phase 1: Foundation

**Goal:** Working dual-panel file browser with basic navigation and keyboard controls.

- [ ] Project scaffolding (pyproject.toml, package structure, dev tooling)
- [ ] Textual application shell with dual-panel layout
- [ ] File list widget (name, size, date, permissions columns)
- [ ] Directory navigation (enter, go up, go to path)
- [ ] Active panel switching (Tab key)
- [ ] Status bar with F-key hints
- [ ] Basic key binding system
- [ ] Configuration loading from TOML

## Phase 2: File Operations

**Goal:** Core file management capabilities.

- [ ] Copy files/directories (F5) with progress indication
- [ ] Move/rename files (F6)
- [ ] Delete files/directories (F8) with confirmation dialog
- [ ] Create new directory (F7)
- [ ] Multi-select files (Insert key / Shift+arrows)
- [ ] Inline rename (single file quick rename)
- [ ] Error handling and permission dialogs

## Phase 3: Search and Sort

**Goal:** Efficient file discovery and organization.

- [ ] Quick filter — type to filter current file list
- [ ] Sort by name, size, date, extension (with toggle direction)
- [ ] Sort indicator in column headers
- [ ] Directory size calculation on demand
- [ ] Show/hide hidden files toggle

## Phase 4: Command Line

**Goal:** Embedded shell command execution.

- [ ] Command line input widget at bottom of screen
- [ ] Execute shell commands in the active panel's directory
- [ ] Command output display (overlay or panel)
- [ ] Command history (up/down arrows)
- [ ] Working directory sync with active file browser panel

## Phase 5: Plugin System

**Goal:** Extensible viewer and editor framework.

- [ ] Plugin interface definitions (viewer base, editor base)
- [ ] Plugin registry with discovery via entry points
- [ ] File-to-plugin resolution by extension and MIME type
- [ ] Default text viewer plugin (F3)
- [ ] Default text editor plugin (F4)
- [ ] Plugin priority configuration in TOML
- [ ] Documentation for writing custom plugins

## Phase 6: Terminal Panel

**Goal:** Full terminal emulator embedded in any panel.

- [ ] PTY subprocess management
- [ ] Terminal rendering via pyte
- [ ] Input forwarding (keyboard → PTY)
- [ ] Async output reading and widget refresh
- [ ] Scrollback buffer
- [ ] Panel mode switching hotkey (Ctrl+T)
- [ ] Multiple independent terminal sessions

## Phase 7: LLM Chat Panel

**Goal:** Context-aware Claude assistant in any panel.

- [ ] Claude API client wrapper
- [ ] Chat panel UI (message history, input area)
- [ ] Context builder — inject current directory and selected files
- [ ] On-demand file content reading ("read file X")
- [ ] Conversation history per session
- [ ] Panel mode switching hotkey (Ctrl+L)
- [ ] Streaming response display
- [ ] Error handling (API key missing, rate limits, network errors)

## Phase 8: Bookmarks and Polish

**Goal:** Quality-of-life features and refinement.

- [ ] Bookmarks — save and jump to favorite directories
- [ ] Bookmark management dialog
- [ ] Consistent color theme and visual polish
- [ ] Help screen (F1) with all keybindings
- [ ] Mouse support for clicks and scrolling
- [ ] Performance optimization for large directories
- [ ] Packaging and distribution (pip install, optional homebrew)

## Future Considerations

Items not currently planned but may be revisited:

- Archive browsing (zip, tar, gz)
- Tabs within panels
- File comparison / diff view
- FTP/SFTP remote panel
- Custom themes / color schemes
- Macro recording and playback
