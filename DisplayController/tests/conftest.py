# tests/conftest.py
import sys
import types
import os
import pytest

# ── 1) Stub out `websockets` ─────────────────────────────────────────────────────
# so DataCommunicator/source/WebSocketConnection can import & await websockets.connect()
fake_ws = types.ModuleType('websockets')
async def fake_connect(uri, *args, **kwargs):
    # return any dummy object (we don’t actually use it in tests)
    return types.SimpleNamespace()
fake_ws.connect = fake_connect
sys.modules['websockets'] = fake_ws
sys.modules['websockets.server'] = types.ModuleType('websockets.server')
sys.modules['websockets.client'] = types.ModuleType('websockets.client')

# ── 2) Inject a fake_rpi stub as RPi and RPi.GPIO ────────────────────────────────
fake_gpio = types.ModuleType('RPi.GPIO')
for const in ('BCM', 'IN', 'PUD_UP', 'FALLING'):
    setattr(fake_gpio, const, None)
fake_gpio.setmode = lambda *a, **k: None
fake_gpio.setup = lambda *a, **k: None
fake_gpio.add_event_detect = lambda *a, **k: None
fake_gpio.input = lambda *a, **k: True
sys.modules['RPi'] = types.SimpleNamespace(GPIO=fake_gpio)
sys.modules['RPi.GPIO'] = fake_gpio

# ── 3) Path hacks ──────────────────────────────────────────────────────────────────
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
display_dir = os.path.join(root, 'display')
io_dir      = os.path.join(root, 'io')
for p in (root, display_dir, io_dir):
    if p not in sys.path:
        sys.path.insert(0, p)