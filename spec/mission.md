# MyCom — Mission

## Vision

MyCom is a modern, keyboard-driven dual-panel file manager for the terminal, inspired by the classic FAR Manager. It combines the proven efficiency of orthodox file management with modern capabilities: pluggable viewers and editors, an integrated terminal, and a context-aware LLM assistant — all within a single TUI application.

## Goals

1. **Efficient file management** — Provide a fast, keyboard-first dual-panel interface for navigating and manipulating files, minimizing the need to leave the application for common tasks.

2. **Extensibility** — Offer a plugin architecture for viewers and editors so users and third parties can extend the application to handle any file type or workflow.

3. **Integrated environment** — Eliminate context switching by embedding a terminal emulator and an LLM chat assistant directly into the panel system, making MyCom a single workspace for file operations, shell commands, and AI-assisted tasks.

4. **Context-aware AI** — The built-in LLM chat (powered by Claude) is aware of the current directory, selected files, and file contents, enabling natural interactions like "explain this file", "summarize these logs", or "suggest a rename scheme."

5. **Simplicity** — Keep the codebase approachable and the UX intuitive. Avoid feature bloat. Every feature should earn its place by solving a real workflow problem.

## Target Users

- Developers and system administrators who live in the terminal
- Users familiar with FAR Manager, Midnight Commander, or similar orthodox file managers
- Power users who want a unified environment for files, shell, and AI assistance

## Principles

- **Keyboard first** — Every action is reachable without a mouse.
- **Panels are flexible** — Any panel can become a file browser, terminal, or LLM chat.
- **Plugins over built-ins** — Prefer a small core with a strong plugin API over a monolithic feature set.
- **Respect the terminal** — Work well in any modern terminal emulator, over SSH, and within tmux/screen.
