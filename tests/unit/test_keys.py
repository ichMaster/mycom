"""Tests for mycom.utils.keys module."""

from mycom.utils.keys import DEFAULTS, KeyBindings


def test_default_bindings():
    kb = KeyBindings()
    assert kb.get("copy") == "f5"
    assert kb.get("quit") == "f10"
    assert kb.get("switch_panel") == "tab"
    assert kb.get("terminal_toggle") == "ctrl+t"
    assert kb.get("llm_toggle") == "ctrl+l"


def test_override_binding():
    kb = KeyBindings(overrides={"copy": "ctrl+c", "quit": "ctrl+q"})
    assert kb.get("copy") == "ctrl+c"
    assert kb.get("quit") == "ctrl+q"
    # Non-overridden remain default
    assert kb.get("move") == "f6"


def test_unknown_override_ignored():
    kb = KeyBindings(overrides={"nonexistent_action": "f12"})
    assert kb.get("nonexistent_action") is None
    assert kb.get("copy") == "f5"


def test_all_returns_copy():
    kb = KeyBindings()
    bindings = kb.all()
    assert bindings == DEFAULTS
    # Modifying the copy does not affect the original
    bindings["copy"] = "ctrl+c"
    assert kb.get("copy") == "f5"


def test_actions_for_key():
    kb = KeyBindings()
    actions = kb.actions_for_key("f5")
    assert "copy" in actions


def test_actions_for_key_no_match():
    kb = KeyBindings()
    actions = kb.actions_for_key("f99")
    assert actions == []


def test_none_overrides():
    kb = KeyBindings(overrides=None)
    assert kb.get("copy") == "f5"
