import asyncio
import time
import pytest
from unittest.mock import MagicMock
from DisplayController.io.io_handler import IOHandler
import types

class DummyConn:
    def __init__(self):
        self.subs = []
        self.sent = []
    def set_client(self, client):
        # required by BaseDataClient.__init__
        self.client = client
    async def subscribe(self, topic): self.subs.append(topic)
    async def send(self, topic, payload): self.sent.append((topic, payload))
    async def connect(self): pass

class DummyButtonInput:
    def __init__(self): self.callbacks=[]
    def listen(self, cb): self.callbacks.append(cb)
    def on_button_press(self, name): pass

@pytest.fixture
def io_handler(monkeypatch):
    conn = DummyConn()
    btn = DummyButtonInput()
    h = IOHandler("io", conn, btn, use_hdmi=False, loading_duration=1, ventilation_duration=1, keepalive=0.1)

    # disable any real loops or predictor threads
    h._loop = lambda: None
    h.on_predict = None
    h._start_predictor = lambda: None
    h._stop_predictor  = lambda: None

    return h

@pytest.mark.asyncio
async def test_run_and_button_and_prediction(io_handler, monkeypatch):
    async def fake_loop():
        # allow subscribe to happen
        await asyncio.sleep(0)
        return
    monkeypatch.setattr(io_handler, "_loop", fake_loop)
    io_handler._event_loop = asyncio.get_running_loop()
    io_handler._send_payload = lambda payload: io_handler.connection.sent.append(("topic:display", payload))
    # start run → subscribes and enters IdleState
    task = asyncio.create_task(io_handler.run())
    await asyncio.sleep(0)  # allow subscribe
    assert "prediction" in io_handler.connection.subs
    # simulate a state change to PredictingState
    from DisplayController.io.state_machine import PredictingState
    io_handler.change_state(PredictingState())
    # send a prediction payload
    await io_handler.on_message("x", {"scent":"test","confidence":0.5})
    # let the scheduled send actually run on the loop
    await asyncio.sleep(0)
    assert any("topic:display" in t for t,_ in io_handler.connection.sent)
    task.cancel()

def test_send_message_formats(io_handler):
    io_handler._event_loop = asyncio.get_event_loop()
    io_handler.connection.send = MagicMock()
    io_handler.send_message("T", ["a","b"])
    # last sent payload:
    args = io_handler.connection.send.call_args[0][1]
    assert args["title"] == "T"
    assert isinstance(args["lines"][0]["text"], str)

@pytest.mark.asyncio
async def test_change_state_and_heartbeat(io_handler):
    io_handler._event_loop = asyncio.get_event_loop()
    io_handler.connection.send = MagicMock()
    # move to VentilatingState
    from DisplayController.io.state_machine import VentilatingState
    io_handler.change_state(VentilatingState())
    # should schedule a send state
    assert any("topic:state" in call[0][0] for call in io_handler.connection.send.call_args_list)


@pytest.mark.asyncio
async def test_connect_and_stop(monkeypatch):
    # stub out underlying connection
    sent = []
    class C:
        def __init__(self): self.client=None
        def set_client(self, c): self.client=c
        async def connect(self): sent.append("connected")
        async def subscribe(self,t): sent.append(f"sub:{t}")
        async def send(self, t,p): sent.append(f"send:{t}")
    handler = IOHandler("n", C(), MagicMock(), use_hdmi=False, loading_duration=1, ventilation_duration=1, keepalive=0.1)
    async def fake_loop():
        # simulates the background loop
        return
    handler._loop = fake_loop
    # call start (which calls connect & subscribe)
    await handler.start()
    assert "connected" in sent
    assert "sub:prediction" in sent

@pytest.mark.asyncio
async def test_send_payload_error(monkeypatch):
    # simulate event_loop closed
    class C:
        def set_client(self,c): pass
        async def connect(self): pass
        async def subscribe(self,t): pass
        async def send(self,t,p): pass
    h = IOHandler("x", C(), MagicMock(), use_hdmi=False, loading_duration=1, ventilation_duration=1, keepalive=0.1)
    # simulate call_soon_threadsafe failing
    h._event_loop = types.SimpleNamespace(
        call_soon_threadsafe=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("closed"))
    )
    # should catch & swallow
    h._send_payload({"a":1})