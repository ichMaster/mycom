"""Verify project scaffold: all sub-packages import and version is set."""


def test_version_is_set():
    from mycom import __version__

    assert __version__ == "0.1.0"


def test_subpackages_import():
    import mycom.panels
    import mycom.operations
    import mycom.plugins
    import mycom.plugins.viewer
    import mycom.plugins.editor
    import mycom.widgets
    import mycom.llm
    import mycom.utils


def test_app_module_imports():
    from mycom.app import MyComApp, main

    assert MyComApp is not None
    assert callable(main)
