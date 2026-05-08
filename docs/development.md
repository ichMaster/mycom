# Development

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
git clone https://github.com/ichMaster/mycom.git
cd mycom
uv sync --all-groups
```

## Running the App

```bash
uv run mycom
```

## Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/unit/test_config.py
```

## Linting

```bash
# Check
uv run ruff check mycom/

# Auto-fix
uv run ruff check mycom/ --fix

# Format
uv run ruff format mycom/
```

## Building Documentation

```bash
# Build static site
uv run mkdocs build

# Serve locally with hot-reload
uv run mkdocs serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Project Structure

```
mycom/
├── app.py              # Main Textual application
├── app.tcss            # Textual CSS styles
├── config.py           # TOML configuration loader
├── panels/
│   ├── base.py         # BasePanel abstract class
│   └── file_browser.py # File browser panel
├── operations/
│   └── sort.py         # File sorting logic
├── plugins/
│   ├── viewer/         # Viewer plugins
│   └── editor/         # Editor plugins
├── widgets/
│   ├── dialog.py       # Modal dialogs
│   ├── file_list.py    # DataTable file listing
│   ├── header.py       # App header
│   ├── path_bar.py     # Path display bar
│   └── status_bar.py   # F-key hints bar
├── llm/                # LLM chat (Phase 7)
└── utils/
    ├── fs.py           # Filesystem helpers
    └── keys.py         # Key binding registry
```

## Version Scheme

`x.y.z` where:
- **x** — major version (0 during initial development)
- **y** — roadmap phase number
- **z** — fixes and patches within a phase
