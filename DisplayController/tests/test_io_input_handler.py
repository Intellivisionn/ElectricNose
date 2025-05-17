import threading
import time
import pytest
from DisplayController.io.io_input_handler import ButtonHandler, IButtonInput

class DummyGPIO:
    BCM = None
    IN = None
    PUD_UP = None
    FALLING = None
    @staticmethod
    def setmode(m): pass
    @staticmethod
    def setup(pin, mode, pull_up_down=None): pass
    @staticmethod
    def add_event_detect(pin, edge, callback, bouncetime=None): 
        callback(pin)
    @staticmethod
    def input(pin): return True

@pytest.fixture(autouse=True)
def gpio_stub(monkeypatch):
    import sys
    fake = DummyGPIO()
    monkeypatch.setitem(sys.modules, "RPi.GPIO", fake)
    yield

def test_listen_edge_and_poll(monkeypatch):
    # force the handler to use our DummyGPIO
    import DisplayController.io.io_input_handler as ioh
    monkeypatch.setattr(ioh, "GPIO", DummyGPIO)
    bh = ButtonHandler({"a":1})

    # force edge‐detect setup failure
    monkeypatch.setattr(DummyGPIO, "setup", lambda *a, **k: (_ for _ in ()).throw(Exception("no irq")))
    monkeypatch.setattr(DummyGPIO, "add_event_detect", lambda *a, **k: (_ for _ in ()).throw(Exception("no irq")))

    # simulate one HIGH→LOW transition: first True, then False
    state = {"first": True}
    def fake_input(pin):
        if state["first"]:
            state["first"] = False
            return True
        return False
    monkeypatch.setattr(DummyGPIO, "input", fake_input)

    got = []
    bh.listen(lambda name: got.append(name))
    import time; time.sleep(0.3)
    assert got == ["a"]

def test_on_button_press_noop():
    bh = ButtonHandler({})
    # should not raise
    bh.on_button_press("x")