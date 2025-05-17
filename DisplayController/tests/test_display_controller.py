import time
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from DisplayController.display.display_controller import DisplayController

class DummyDisplay:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.drawn = []

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def draw(self, data):
        self.drawn.append(data)

    def check_connection(self):
        return True

class DummyConn:
    def __init__(self):
        self.subscribed = []
        self.sent = []
    def set_client(self, client):
        # no-op or store for inspection
        self.client = client
    async def subscribe(self, topic):
        self.subscribed.append(topic)
    async def connect(self):
        pass
    async def send(self, topic, payload):
        self.sent.append((topic, payload))

@pytest.fixture
def controller(tmp_path, monkeypatch):
    conn = DummyConn()
    ctrl = DisplayController("test", conn, use_hdmi=False, override_timeout=0.1, draw_interval=0.01)

    # prevent infinite loop: patch _loop to run only 2 iterations
    async def fake_loop():
        for _ in range(2):
            await asyncio.sleep(0)
        return
    ctrl._loop = fake_loop  # type: ignore
    return ctrl

@pytest.mark.asyncio
async def test_start_and_run_subscribes_and_loops(controller, monkeypatch):
    dummy = DummyDisplay()
    controller.use_hdmi = False
    # clear any existing display
    monkeypatch.setattr(controller, "display", None)

    # capture every time set_display() is called
    chosen = []
    def record_set(disp):
        chosen.append(type(disp))
    monkeypatch.setattr(controller, "set_display", record_set)

    # point both PiTFTDisplay and HDMIDisplay at our dummy
    import DisplayController.display.display_impl as display_impl
    monkeypatch.setattr(display_impl, "PiTFTDisplay", lambda: dummy)
    monkeypatch.setattr(display_impl, "HDMIDisplay", lambda: dummy)

    # now override the draw‐loop itself so it calls set_display twice
    async def fake_loop():
        controller.set_display(dummy)
        controller.set_display(dummy)
    monkeypatch.setattr(controller, "_loop", fake_loop)

    # run start → run → fake_loop
    await controller.start()

    # subscription happened
    assert "display" in controller.connection.subscribed

    # and our fake_loop called set_display exactly twice
    assert chosen == [type(dummy), type(dummy)]

@pytest.mark.asyncio
async def test_update_and_draw_override(monkeypatch):
    conn = DummyConn()
    ctrl = DisplayController("test", conn, use_hdmi=False, override_timeout=1.0, draw_interval=0.01)
    dummy = DummyDisplay()
    ctrl.display = dummy
    # update with payload
    payload = {"foo": "bar"}
    ctrl.update_display(payload)
    ctrl.draw()
    assert dummy.drawn[-1] == payload
    # after timeout, draw(None)
    time.sleep(1.1)
    ctrl.draw()
    assert dummy.drawn[-1] is None

def test_set_display_stops_previous(monkeypatch):
    conn = DummyConn()
    ctrl = DisplayController("test", conn)
    old = DummyDisplay()
    old.stop = MagicMock()
    ctrl.display = old
    new = DummyDisplay()
    ctrl.set_display(new)
    old.stop.assert_called()
    assert ctrl.display is new
    assert new.started

@pytest.mark.asyncio
async def test_stop_cancels_task(controller):
    # simulate existing task
    dummy = DummyDisplay()
    controller.display = dummy
    async def never_loop():
        await asyncio.Future()
    controller._draw_task = asyncio.create_task(never_loop())
    await controller.stop()
    assert dummy.stopped