import importlib

def test_display_main_importable():
    # just ensure it imports without error
    m = importlib.import_module("DisplayController.display.display_main")
    assert hasattr(m, "main")

def test_io_main_importable():
    m = importlib.import_module("DisplayController.io.io_main")
    assert hasattr(m, "main")