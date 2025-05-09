import time
import threading
import socket
import json
import pytest

import source.display_client as dc

class DummyClient:
    def __init__(self):
        self.loading_duration = 5
        self.ventilation_duration = 10
        self.timer_start = None
        self._last_remaining = None
        self._last_heartbeat = None
        self.sent = []
        self.predict_started = False
        self.predict_stopped = False
        self.current_state = None

    # methods called by states
    def send_idle_message(self):            self.sent.append("idle")
    def send_paused(self):                  self.sent.append("paused")
    def send_loading(self, rem):            self.sent.append(f"loading:{rem}")
    def send_prediction(self, scent, conf): self.sent.append(("prediction", scent, conf))
    def send_ventilation_timer(self, rem):  self.sent.append(f"vent:{rem}")
    def send_message(self, title, lines):   self.sent.append(("msg", title, lines))

    def _start_predictor(self):             self.predict_started = True
    def _stop_predictor(self):              self.predict_stopped = True

    def change_state(self, new_state):
        self.current_state = new_state

@pytest.fixture(autouse=True)
def stub_gpio(monkeypatch):
    monkeypatch.setattr(dc.GPIO, "setmode", lambda m: None)
    monkeypatch.setattr(dc.GPIO, "setup", lambda *a, **k: None)
    monkeypatch.setattr(dc.GPIO, "add_event_detect", lambda *a, **k: None)
    monkeypatch.setattr(dc.GPIO, "cleanup", lambda: None)

def test_state_default_on_button_dispatch():
    client = DummyClient()
    state = dc.State()
    for name, expected in [
        ("start", dc.LoadingState),
        ("ventilate", dc.VentilatingState),
        ("cancel", dc.CancelledState),
        ("halt", dc.PausedState),
    ]:
        state.on_button(client, name)
        assert isinstance(client.current_state, expected)

def test_idle_state_entry_and_tick(monkeypatch):
    client = DummyClient()
    state = dc.IdleState()
    t0 = 1000.0
    monkeypatch.setattr(dc.time, "time", lambda: t0)

    state.on_entry(client)
    assert client.predict_stopped is True
    assert "idle" in client.sent

    client.sent.clear()
    monkeypatch.setattr(dc.time, "time", lambda: t0 + dc.KEEPALIVE_INTERVAL - 1)
    state.on_tick(client)
    assert client.sent == []

    monkeypatch.setattr(dc.time, "time", lambda: t0 + dc.KEEPALIVE_INTERVAL + 1)
    state.on_tick(client)
    assert "idle" in client.sent

def test_loading_state_entry_and_tick(monkeypatch):
    client = DummyClient()
    state = dc.LoadingState()
    t0 = 2000.0
    monkeypatch.setattr(dc.time, "time", lambda: t0)

    state.on_entry(client)
    assert client.predict_stopped is True
    assert any(s.startswith("loading:") for s in client.sent)

    client.sent.clear()
    monkeypatch.setattr(dc.time, "time", lambda: t0 + 2)
    state.on_tick(client)
    assert any("loading:" in s for s in client.sent)

    client.sent.clear()
    monkeypatch.setattr(dc.time, "time", lambda: t0 + client.loading_duration)
    state.on_tick(client)
    assert isinstance(client.current_state, dc.PredictingState)

def test_predicting_state_starts_predictor():
    client = DummyClient()
    state = dc.PredictingState()
    state.on_entry(client)
    assert client.predict_started is True

def test_ventilating_state_entry_and_tick(monkeypatch):
    client = DummyClient()
    state = dc.VentilatingState()
    t0 = 3000.0
    monkeypatch.setattr(dc.time, "time", lambda: t0)

    state.on_entry(client)
    assert client.predict_stopped is True
    assert any(s.startswith("vent:") for s in client.sent)

    client.sent.clear()
    monkeypatch.setattr(dc.time, "time", lambda: t0 + 1)
    state.on_tick(client)
    assert any(s.startswith("vent:") for s in client.sent)

    client.sent.clear()
    monkeypatch.setattr(dc.time, "time", lambda: t0 + client.ventilation_duration)
    state.on_tick(client)
    assert isinstance(client.current_state, dc.IdleState)

def test_paused_state_entry_and_tick(monkeypatch):
    client = DummyClient()
    state = dc.PausedState()
    t0 = 4000.0
    monkeypatch.setattr(dc.time, "time", lambda: t0)

    state.on_entry(client)
    assert client.predict_stopped is True
    assert "paused" in client.sent

    client.sent.clear()
    monkeypatch.setattr(dc.time, "time", lambda: t0 + dc.KEEPALIVE_INTERVAL + 1)
    state.on_tick(client)
    assert "paused" in client.sent

def test_cancelled_state_entry(monkeypatch):
    client = DummyClient()
    # immediate timer
    orig = threading.Timer
    class ImmediateTimer:
        def __init__(self, interval, fn):
            fn()
        def start(self): pass
    monkeypatch.setattr(threading, "Timer", ImmediateTimer)

    client.sent.clear()
    state = dc.CancelledState()
    state.on_entry(client)

    assert client.predict_stopped is True
    assert ("msg", "Cancelled", ["Operation was cancelled."]) in client.sent
    assert isinstance(client.current_state, dc.IdleState)

    monkeypatch.setattr(threading, "Timer", orig)

def test_display_client_send_and_payload(monkeypatch):
    # fake socket for _send_payload success
    class FakeSocket:
        def __init__(self, *a, **k): self.sent = []
        def connect(self, addr): self.addr = addr
        def sendall(self, data): self.sent.append(data)
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr(dc.socket, "socket", lambda *a,**k: FakeSocket())

    client = dc.DisplayClient(loading_duration=3, ventilation_duration=4)
    # capture formatted payloads
    sent = []
    client._setup_gpio = lambda: None
    client._send_payload = lambda p: sent.append(p)

    client.send_idle_message()
    assert sent[-1]["title"] == "Ready"

    client.send_paused()
    assert sent[-1]["title"] == "Paused"

    client.send_loading(2)
    assert sent[-1]["title"] == "Loading..."

    client.send_prediction("S", 0.1)
    assert sent[-1]["title"] == "Prediction"

    client.send_ventilation_timer(60)
    assert sent[-1]["title"] == "Ventilating"

    # now test exception path
    class BadSocket:
        def __init__(self,*a,**k): pass
        def connect(self, addr): raise RuntimeError("fail")
        def sendall(self, data): pass
        def __enter__(self): return self
        def __exit__(self,*a): pass
    monkeypatch.setattr(dc.socket, "socket", lambda *a,**k: BadSocket())
    # should not raise
    client._send_payload({"x":1})

def test_continuous_predictor(monkeypatch):
    client = dc.DisplayClient()
    client._setup_gpio = lambda: None
    sent = []
    client.send_prediction = lambda s,c: sent.append((s,c))

    data = [("A",0.1), ("B",0.2)]
    def on_predict():
        if data:
            return data.pop(0)
        else:
            raise Exception("done")
    client.on_predict = on_predict

    client._predict_stop_event.clear()
    client._start_predictor()
    time.sleep(0.2)
    client._stop_predictor()

    assert ("A",0.1) in sent and ("B",0.2) in sent

def test_start_predictor_no_callback():
    client = dc.DisplayClient()
    client._setup_gpio = lambda: None
    client.on_predict = None
    client._predict_thread = None
    # should not error and no thread started
    client._start_predictor()
    assert client._predict_thread is None

def test_display_client_start_and_stop(monkeypatch):
    # stub gpio
    monkeypatch.setattr(dc.GPIO, "setmode", lambda m: None)
    monkeypatch.setattr(dc.GPIO, "setup", lambda *a, **k: None)
    monkeypatch.setattr(dc.GPIO, "add_event_detect", lambda *a, **k: None)
    monkeypatch.setattr(dc.GPIO, "cleanup", lambda: None)

    started = {"n":0}
    joined  = {"n":0}
    monkeypatch.setattr(threading.Thread, "start", lambda self: started.__setitem__("n", started["n"]+1))
    monkeypatch.setattr(threading.Thread, "join",  lambda self, timeout=None: joined.__setitem__("n", joined["n"]+1))

    client = dc.DisplayClient()
    client.send_idle_message = lambda: None

    client.start()
    assert client._running is True
    assert isinstance(client._state, dc.IdleState)
    assert started["n"] == 1

    client.stop()
    assert client._running is False
    assert joined["n"] == 1

def test_button_pressed_changes_state(monkeypatch):
    client = dc.DisplayClient()
    client._setup_gpio = lambda: None
    client._state = dc.IdleState()
    changes = []
    client.change_state = lambda st: changes.append(type(st))

    for btn, expected in [
        ("start", dc.LoadingState),
        ("ventilate", dc.VentilatingState),
        ("cancel", dc.CancelledState),
        ("halt", dc.PausedState),
    ]:
        client._button_pressed(btn)
        assert changes[-1] is expected