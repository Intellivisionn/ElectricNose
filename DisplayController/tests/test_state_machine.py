import time
from DisplayController.io.state_machine import (
    IdleState, LoadingState, PredictingState,
    VentilatingState, CancelledState
)

class DummyHandler:
    def __init__(self):
        self.loading_duration = 0.05
        self.ventilation_duration = 0.05
        self.keepalive = 0.01
        self._last_heartbeat = time.time()
        self.state = None
        self.sent = []
    def _stop_predictor(self): pass
    def _start_predictor(self): pass
    def change_state(self, new_state): 
        # optionally record for assertions
        self.last_state = new_state
    def _stop_predictor(self): pass
    def _start_predictor(self): pass
    def change_state(self, new_state):
    # record the new state for assertions
        self._state = new_state
    def send_idle_message(self):     self.sent.append("idle")
    def send_loading(self, rem): self.sent.append(f"load{rem}")
    def send_prediction(self, s, c): self.sent.append("pred")
    def send_ventilation_timer(self, rem): self.sent.append(f"vent{rem}")
    def send_message(self, title, lines): self.sent.append(f"{title}:{lines}")

def test_idle_to_loading_and_timeout():
    h = DummyHandler()
    st = IdleState()
    st.on_entry(h)
    assert "idle" in h.sent
    # tick should re-send idle after keepalive
    time.sleep(0.02)
    st.on_tick(h)
    assert h.sent.count("idle") >= 2

    st.on_button(h, "start")
    assert isinstance(h._state, type(LoadingState()))

def test_loading_to_predicting_and_cancel():
    h = DummyHandler()
    st = LoadingState()
    st.on_entry(h)
    assert any("load" in s for s in h.sent)
    # simulate tick until zero; then next on_tick should trigger change_state to PredictingState
    time.sleep(0.06)
    st.on_tick(h)
    # no exception

def test_predicting_buttons_and_entry():
    h = DummyHandler()
    st = PredictingState()
    # no on_entry logic except predictor start (noop)
    st.on_button(h, "cancel")
    st.on_button(h, "ventilate")

def test_ventilating_cycle():
    h = DummyHandler()
    st = VentilatingState()
    st.on_entry(h)
    assert any("vent" in s for s in h.sent)
    time.sleep(0.06)
    st.on_tick(h)

def test_cancelled_auto_reset(monkeypatch):
    h = DummyHandler()
    st = CancelledState()
    # capturing threading.Timer call by overriding change_state
    calls = []
    h.change_state = lambda s: calls.append(type(s).__name__)
    st.on_entry(h)
    assert any("Cancelled" in s for s in h.sent)
    # wait >10s? instead force immediate call:
    monkeypatch.setattr("threading.Timer",
     lambda t, f: type("T",(object,),{"start": (lambda *args, **kw: f())})()
    )
    st = CancelledState()
    st.on_entry(h)
    assert "IdleState" in calls