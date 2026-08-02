"""Regression tests: keys handled by an open dialog must not also reach the
panel underneath it.

Found while implementing MC-020 (mask select dialog): pressing Enter to
submit the mask dialog was ALSO reaching MyComApp.on_key's "open" handling
for the panel behind it (DialogKit's key_enter/key_escape convention methods
don't stop event bubbling), which — if the panel's cursor happened to be on
"..' — called navigate_up(), clearing the selection the dialog's own
callback had just set moments earlier. Fixed by (1) consolidating DialogKit's
Enter/Esc handling into on_key so it can call event.stop(), and (2) a
defense-in-depth guard in MyComApp.on_key that no-ops while any modal is on
the screen stack.
"""

from __future__ import annotations

import pytest

from mycom.app import MyComApp
from mycom.widgets.dialog import InputDialog


@pytest.mark.asyncio
async def test_enter_in_dialog_does_not_navigate_the_panel_behind_it(tmp_path):
    child = tmp_path / "child"
    child.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(tmp_path)
        await pilot.pause()
        # Cursor defaults to ".." — exactly the case that triggered the bug
        # (Enter in the dialog also calling the panel's navigate_up()).
        assert app.active_panel.file_list.selected_name == ".."
        before = app.active_panel.current_path

        app.push_screen(InputDialog("Prompt:", default="x"))
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert app.active_panel.current_path == before


@pytest.mark.asyncio
async def test_mask_dialog_selection_survives_the_submitting_enter_keypress(tmp_path):
    # A subdirectory, not tmp_path itself — conftest's autouse fixture points
    # MYCOM_LOG_FILE at tmp_path/mycom.log, which "*" would also select.
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "a.py").touch()
    (content_dir / "b.py").touch()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(content_dir)
        await pilot.pause()
        # Cursor on ".." at the time the dialog opens, same as the bug repro.
        assert app.active_panel.file_list.selected_name == ".."

        await pilot.press("plus")
        await pilot.pause()
        await pilot.press("enter")  # default pattern "*"
        await pilot.pause()

        assert app.active_panel.selected_names == {"a.py", "b.py"}


@pytest.mark.asyncio
async def test_backspace_in_a_dialog_does_not_go_up_the_panel_behind_it(tmp_path):
    child = tmp_path / "child"
    child.mkdir()

    app = MyComApp()
    async with app.run_test() as pilot:
        app.active_panel.navigate_to(child)
        await pilot.pause()
        before = app.active_panel.current_path

        app.push_screen(InputDialog("Prompt:", default="x"))
        await pilot.pause()
        await pilot.press("backspace")  # edits the Input's text, not go_up
        await pilot.pause()

        assert app.active_panel.current_path == before
