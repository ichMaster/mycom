"""TOML-based configuration loader for MyCom."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "mycom"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass(frozen=True)
class GeneralConfig:
    show_hidden: bool = False
    confirm_delete: bool = True
    default_sort: str = "name"
    default_sort_direction: str = "asc"


@dataclass(frozen=True)
class LLMConfig:
    api_key_env: str = "ANTHROPIC_API_KEY"
    model: str = "claude-sonnet-4-6"
    max_context_files: int = 10


@dataclass(frozen=True)
class PluginConfig:
    viewers: dict[str, str] = field(default_factory=dict)
    editors: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    keybindings: dict[str, str] = field(default_factory=dict)
    llm: LLMConfig = field(default_factory=LLMConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)


def _build_section(cls: type, data: dict[str, Any]) -> Any:
    known = {f.name for f in cls.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in known}
    return cls(**filtered)


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from TOML file, merging with defaults."""
    config_path = path or CONFIG_FILE
    if not config_path.exists():
        return AppConfig()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    general = _build_section(GeneralConfig, raw.get("general", {}))
    llm = _build_section(LLMConfig, raw.get("llm", {}))

    plugins_raw = raw.get("plugins", {})
    plugins = PluginConfig(
        viewers=plugins_raw.get("viewers", {}),
        editors=plugins_raw.get("editors", {}),
    )

    keybindings = raw.get("keybindings", {})

    return AppConfig(
        general=general,
        keybindings=keybindings,
        llm=llm,
        plugins=plugins,
    )
