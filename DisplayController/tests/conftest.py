# tests/conftest.py
import sys
import types
import os
import pytest

# ── 1) Stub out `websockets` ─────────────────────────────────────────────────────
# so DataCommunicator/source/WebSocketConnection can do `import websockets`
sys.modules['websockets'] = types.ModuleType('websockets')
sys.modules['websockets.server'] = types.ModuleType('websockets.server')
sys.modules['websockets.client'] = types.ModuleType('websockets.client')

# ── 2) Inject a fake_rpi stub as RPi and RPi.GPIO ────────────────────────────────
# so io_input_handler.py's `import RPi.GPIO as GPIO` picks up a harmless dummy.
fake_rpi = types.ModuleType('fake_rpi')
fake_gpio = types.ModuleType('RPi.GPIO')
# mirror the API they expect:
for const in ('BCM', 'IN', 'PUD_UP', 'FALLING'):
    setattr(fake_gpio, const, None)
fake_gpio.setmode = lambda *a, **k: None
fake_gpio.setup   = lambda *a, **k: None
fake_gpio.add_event_detect = lambda *a, **k: None
fake_gpio.input   = lambda *a, **k: True
fake_rpi.RPi      = types.SimpleNamespace(GPIO=fake_gpio)

sys.modules['RPi']      = fake_rpi.RPi
sys.modules['RPi.GPIO'] = fake_gpio

# ── 3) Your existing path hacks so imports like `from display_impl import ...` work ─
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
display_dir = os.path.join(root, 'display')
io_dir      = os.path.join(root, 'io')
for p in (root, display_dir, io_dir):
    if p not in sys.path:
        sys.path.insert(0, p)