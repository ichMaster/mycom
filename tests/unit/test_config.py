"""Tests for mycom.config module."""

from pathlib import Path

from mycom.config import AppConfig, GeneralConfig, LLMConfig, PluginConfig, load_config

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_defaults_when_no_config_file():
    config = load_config(Path("/nonexistent/config.toml"))
    assert config == AppConfig()
    assert config.general.show_hidden is False
    assert config.general.confirm_delete is True
    assert config.general.default_sort == "name"


def test_load_from_fixture():
    config = load_config(FIXTURES / "config.toml")
    assert config.general.show_hidden is True
    assert config.general.confirm_delete is False
    assert config.general.default_sort == "size"
    assert config.general.default_sort_direction == "desc"


def test_llm_config_from_fixture():
    config = load_config(FIXTURES / "config.toml")
    assert config.llm.api_key_env == "MY_CLAUDE_KEY"
    assert config.llm.model == "claude-opus-4-6"
    assert config.llm.max_context_files == 5


def test_plugin_config_from_fixture():
    config = load_config(FIXTURES / "config.toml")
    assert config.plugins.viewers[".json"] == "json-pretty-viewer"
    assert config.plugins.editors[".py"] == "default-text-editor"


def test_keybindings_from_fixture():
    config = load_config(FIXTURES / "config.toml")
    assert config.keybindings["copy"] == "ctrl+c"
    assert config.keybindings["quit"] == "ctrl+q"


def test_unknown_keys_ignored(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('[general]\nshow_hidden = true\nfuture_option = "yes"\n')
    config = load_config(cfg)
    assert config.general.show_hidden is True


def test_config_is_frozen():
    config = load_config(Path("/nonexistent/config.toml"))
    try:
        config.general = GeneralConfig(show_hidden=True)  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_empty_config_file(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text("")
    config = load_config(cfg)
    assert config == AppConfig()
