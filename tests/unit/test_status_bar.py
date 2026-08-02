"""Tests for StatusBar widget (F0.14 key bar, generated from the keymap registry)."""

import pytest
from textual.app import ComposeResult

from mycom.keymap import Keymap
from mycom.widgets.status_bar import StatusBar
from tests.support import ThemedApp


class StatusBarApp(ThemedApp):
    def compose(self) -> ComposeResult:
        yield StatusBar(keymap=Keymap(), scope="panel")


@pytest.mark.asyncio
async def test_status_bar_renders():
    async with StatusBarApp().run_test() as pilot:
        sb = pilot.app.query_one(StatusBar)
        assert sb is not None


def test_status_bar_slots_match_keymap():
    keymap = Keymap()
    sb = StatusBar(keymap=keymap, scope="panel")
    assert sb._slots() == keymap.key_bar_slots("panel")


def test_status_bar_without_keymap_renders_ten_empty_slots():
    sb = StatusBar()
    slots = sb._slots()
    assert len(slots) == 10
    assert all(action == "" and label == "" for _slot, action, _key, label in slots)


def test_status_bar_labels_match_keymap_resolve():
    keymap = Keymap()
    for _slot, action, _key_label, action_label in keymap.key_bar_slots("panel"):
        if action:
            assert keymap.resolve(action) is not None
            assert action_label  # non-empty for an assigned slot


def test_status_bar_unassigned_slots_are_empty():
    keymap = Keymap()
    slots = keymap.key_bar_slots("panel")
    assigned_slots = {2, 9}  # F2/F9 are reserved for menus (v1.8), not yet bound
    for slot, action, key_label, action_label in slots:
        if slot in assigned_slots:
            assert (action, key_label, action_label) == ("", "", "")
