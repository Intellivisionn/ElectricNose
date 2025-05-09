import os
import sys
import builtins
import subprocess
import pygame
import pytest
import time
import json
import threading

import source.main as main

HDMIStatusChecker = main.HDMIStatusChecker
DisplayManager    = main.DisplayManager
DisplayApp        = main.DisplayApp
OVERRIDE_TIMEOUT  = main.OVERRIDE_TIMEOUT

class DummyFile:
    def __init__(self, content): self._c = content
    def read(self):            return self._c
    def __enter__(self):       return self
    def __exit__(self, *a):    pass

class DummySurface:
    def __init__(self, text):  self.text = text
    def get_rect(self, **kw):  return None

class DummyFont:
    def __init__(self, path, size): pass
    def size(self, txt):              return (len(txt)*6, 10)
    def render(self, txt, aa, color): return DummySurface(txt)
    def get_linesize(self):           return 10

class DummyScreen:
    def __init__(self): self.drawn = []
    def get_width(self):  return 200
    def get_height(self): return 100
    def fill(self, c):    pass
    def blit(self, surf, rect):
        self.drawn.append(getattr(surf, "text", None))

# pygame internals so no display is needed
@pytest.fixture(autouse=True)
def fake_pygame(monkeypatch):
    monkeypatch.setattr(pygame.font,    "Font", DummyFont)
    monkeypatch.setattr(pygame.display, "flip", lambda: None)
    monkeypatch.setattr(pygame,         "init", lambda: None)
    monkeypatch.setattr(pygame.mouse,   "set_visible", lambda v: None)
    monkeypatch.setattr(pygame.display, "set_mode", lambda *args, **kwargs: DummyScreen())

def test_hdmi_connected(monkeypatch):
    monkeypatch.setattr(main.glob, "glob", lambda p: ["/fake"])
    monkeypatch.setattr(builtins, "open", lambda path, mode='r': DummyFile("connected"))
    assert HDMIStatusChecker.is_connected() is True

def test_hdmi_not_connected(monkeypatch):
    monkeypatch.setattr(main.glob, "glob", lambda p: ["/p1", "/p2"])
    seq = iter(["disconnected", "disconnected"])
    monkeypatch.setattr(builtins, "open", lambda path, mode='r': DummyFile(next(seq)))
    assert HDMIStatusChecker.is_connected() is False

def test_fallback_display_sensor_inactive(monkeypatch):
    dm = DisplayManager()
    dm.screen = DummyScreen()
    monkeypatch.setattr(main, "USE_SENSOR_CHECK", True)
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: b"inactive")
    dm._draw_fallback_display()
    assert dm.screen.drawn[-1] in ("Sensors Service is offline", "Display Client is offline")

def test_fallback_display_sensor_active(monkeypatch):
    dm = DisplayManager()
    dm.screen = DummyScreen()
    monkeypatch.setattr(main, "USE_SENSOR_CHECK", True)
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: b"active")
    dm._draw_fallback_display()
    assert dm.screen.drawn[-1] == "Display Client is offline"

def test_serialiser_drives_custom_display(monkeypatch):
    # Prepare payload
    payload = {"title": "T", "lines":[{"text":"L","color":[1,2,3]}]}
    msg = json.dumps(payload).encode()

    # Fake client/server
    class FakeClient:
        def __init__(self, m): self.msg = m; self.closed=False
        def recv(self, n): return self.msg
        def close(self): self.closed=True

    class FakeSocket:
        def __init__(self):
            self._accepted = False
        def bind(self, addr): pass
        def listen(self, n): pass
        def accept(self):
            if not self._accepted:
                self._accepted = True
                return FakeClient(msg), ("127.0.0.1", 1234)
            else:
                raise RuntimeError("done")
        def close(self): pass

    monkeypatch.setattr(main.socket, "socket", lambda *a, **k: FakeSocket())

    dm = DisplayManager()
    drawn = []
    dm._draw_custom_display = lambda p: drawn.append(p)

    with pytest.raises(RuntimeError):
        dm._start_socket_server()

    assert dm.override_data == payload
    assert drawn == [payload]

def test_draw_custom_display_simple_wrap():
    dm = DisplayManager()
    dm.screen = DummyScreen()
    payload = {"title": "SHORT", "lines":[{"text":"LINE","color":[1,2,3]}]}
    dm._draw_custom_display(payload)
    assert dm.screen.drawn == ["SHORT", "LINE"]

def test_draw_custom_display_line_wrap():
    dm = DisplayManager()
    dm.screen = DummyScreen()
    long_word = "X"*100
    payload = {"title": long_word, "lines":[{"text": long_word, "color":[4,5,6]}]}
    dm._draw_custom_display(payload)
    # should render that long word twice
    assert dm.screen.drawn.count(long_word) == 2

def test_draw_switches_between_custom_and_fallback():
    dm = DisplayManager()
    dm.screen = DummyScreen()
    calls = []
    dm._draw_custom_display = lambda p: calls.append("custom")
    dm._draw_fallback_display = lambda: calls.append("fallback")

    # fresh override -> custom
    dm.override_data = {"foo":"bar"}
    dm.override_last_update = time.time()
    dm.draw()
    assert calls == ["custom"]

    # stale override -> fallback
    calls.clear()
    dm.override_last_update = time.time() - (OVERRIDE_TIMEOUT + 1)
    dm.draw()
    assert calls == ["fallback"]

def test_start_and_stop(monkeypatch):
    cmds = []
    monkeypatch.setattr(main.os, "system", lambda c: cmds.append(c))
    started = {"n":0}
    monkeypatch.setattr(threading.Thread, "start", lambda self: started.__setitem__("n", started["n"]+1))

    dm = DisplayManager()
    dm.start()
    assert any("chvt" in c for c in cmds)
    assert any("fbset" in c for c in cmds)
    assert started["n"] == 1

    monkeypatch.setattr(pygame, "quit", lambda: cmds.append("pygame.quit"))
    dm.stop()
    assert "pygame.quit" in cmds

def test_DisplayApp_run_transitions(monkeypatch):
    seq = [False, True]
    monkeypatch.setattr(HDMIStatusChecker, "is_connected", staticmethod(lambda: seq.pop(0)))

    start_cnt = {"n": 0}
    stop_cnt  = {"n": 0}
    monkeypatch.setattr(DisplayManager, "start", lambda self: start_cnt.__setitem__("n", start_cnt["n"]+1))
    monkeypatch.setattr(DisplayManager, "stop",  lambda self: stop_cnt.__setitem__("n", stop_cnt["n"]+1))
    monkeypatch.setattr(DisplayManager, "draw",  lambda self: None)

    # Return an object with a .type attribute rather than a dict
    class DummyEvent:
        def __init__(self, t, key=None):
            self.type = t
            self.key  = key

    monkeypatch.setattr(pygame.event, "get", lambda: [DummyEvent(pygame.QUIT)])

    app = DisplayApp()
    app.run()

    assert start_cnt["n"] == 1
    assert stop_cnt["n"] == 0