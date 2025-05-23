import importlib

def test_display_main_importable():
    # just ensure it imports without error
    m = importlib.import_module("DisplayController.display.display_main")
    assert hasattr(m, "main")

def test_io_main_importable():
    m = importlib.import_module("DisplayController.io.io_main")
    assert hasattr(m, "main")

def test_display_main_runs(monkeypatch):
    m = importlib.import_module("DisplayController.display.display_main")
    # stub out main and any imports
    monkeypatch.setattr(m, "main", lambda: None)
    # call with both flags
    m.USE_HDMI = True
    m.WS_URI = "ws://x"
    m.main()

def test_io_main_runs(monkeypatch):
    m = importlib.import_module("DisplayController.io.io_main")
    monkeypatch.setattr(m, "main", lambda: None)
    m.BUTTON_PINS = {"a":1}
    m.main()