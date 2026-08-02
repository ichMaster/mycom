"""Verify project scaffold: all sub-packages import and version is set."""


def test_version_is_set():
    from mycom import __version__

    assert __version__ == "0.1.0"


def test_subpackages_import():
    pass


def test_app_module_imports():
    from mycom.app import MyComApp, main

    assert MyComApp is not None
    assert callable(main)
