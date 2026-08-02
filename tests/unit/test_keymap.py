"""Tests for mycom.keymap module."""

from mycom.keymap import DEFAULT_COMMANDS, Keymap


def test_default_bindings():
    km = Keymap()
    assert km.resolve("copy") == "f5"
    assert km.resolve("quit") == "f10"
    assert km.resolve("switch_panel") == "tab"
    assert km.resolve("panel_swap") == "ctrl+u"
    assert km.resolve("sort_size") == "ctrl+f6"


def test_override_binding():
    km = Keymap(overrides={"copy": "ctrl+c", "quit": "ctrl+q"})
    assert km.resolve("copy") == "ctrl+c"
    assert km.resolve("quit") == "ctrl+q"
    # Non-overridden remain default
    assert km.resolve("move") == "f6"


def test_unknown_override_ignored():
    km = Keymap(overrides={"nonexistent_action": "f12"})
    assert km.resolve("nonexistent_action") is None
    assert km.resolve("copy") == "f5"


def test_none_overrides():
    km = Keymap(overrides=None)
    assert km.resolve("copy") == "f5"


def test_all_returns_primary_keys():
    km = Keymap()
    bindings = km.all()
    assert bindings["copy"] == "f5"
    assert bindings["panel_swap"] == "ctrl+u"
    # Every default command with keys is present
    for cmd in DEFAULT_COMMANDS:
        assert bindings[cmd.action] == cmd.keys[0]


def test_actions_for_key():
    km = Keymap()
    actions = km.actions_for_key("f5")
    assert "copy" in actions


def test_actions_for_key_no_match():
    km = Keymap()
    actions = km.actions_for_key("f99")
    assert actions == []


def test_actions_for_key_scoped_to_context():
    km = Keymap()
    assert km.actions_for_key("f5", context="panel") == ["copy"]
    assert km.actions_for_key("f5", context="viewer") == []


def test_bindings_for_context():
    km = Keymap()
    bindings = km.bindings_for_context("panel")
    triples = {(key, action) for key, action, _label in bindings}
    assert ("ctrl+u", "panel_swap") in triples
    assert ("f5", "copy") in triples
    assert len(bindings) == len(DEFAULT_COMMANDS)


def test_bindings_for_context_no_match():
    km = Keymap()
    assert km.bindings_for_context("viewer") == []


def test_override_preserves_context_and_label():
    km = Keymap(overrides={"copy": "ctrl+c"})
    bindings = km.bindings_for_context("panel")
    match = [b for b in bindings if b[1] == "copy"]
    assert match == [("ctrl+c", "copy", "Copy")]
