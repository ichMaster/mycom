"""Pilot-driven integration tests for MC-017: key bar generated from the keymap."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mycom.app import MyComApp
from mycom.widgets.status_bar import StatusBar, _KeyBarSlot


@pytest.mark.asyncio
async def test_key_bar_labels_match_keymap_resolve():
    app = MyComApp()
    async with app.run_test():
        sb = app.query_one(StatusBar)
        for _slot, action, key_label, action_label in sb._slots():
            if action:
                assert app._keymap.resolve(action).upper() == key_label
                assert action_label


@pytest.mark.asyncio
async def test_unassigned_slots_render_empty_in_the_running_app():
    app = MyComApp()
    async with app.run_test():
        sb = app.query_one(StatusBar)
        slots = {slot: (action, label) for slot, action, _key, label in sb._slots()}
        assert slots[2] == ("", "")
        assert slots[9] == ("", "")


@pytest.mark.asyncio
async def test_clicking_key_bar_slot_reaches_same_action_as_its_key():
    """Clicking the "5Copy" slot must reach the same app.run_action("copy")
    call F5 would (both currently no-ops until v0.4 file operations land —
    this asserts the same dispatch path is reached, not a visible copy)."""
    app = MyComApp()
    async with app.run_test():
        sb = app.query_one(StatusBar)
        copy_slot = next(w for w in sb.query(_KeyBarSlot) if w._action == "copy")

        with patch.object(MyComApp, "run_action") as mock_run_action:
            await copy_slot.on_click(None)

        mock_run_action.assert_called_once()
        assert mock_run_action.call_args.args[0] == "copy"


@pytest.mark.asyncio
async def test_clicking_quit_slot_actually_quits_end_to_end():
    """Unmocked end-to-end check that the async on_click -> run_action path
    really executes the action (not just that it's awaited on a mock)."""
    app = MyComApp()
    async with app.run_test():
        sb = app.query_one(StatusBar)
        quit_slot = next(w for w in sb.query(_KeyBarSlot) if w._action == "quit")
        await quit_slot.on_click(None)
        assert app._exit
