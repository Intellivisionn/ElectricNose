import os
import glob
import subprocess
import pytest
from unittest.mock import patch, MagicMock
import pygame
from DisplayController.display.display_impl import (
    HDMIStatusChecker,
    SensorServiceMonitor,
    BasePygameDisplay,
    PiTFTDisplay,
    HDMIDisplay
)

def test_hdmi_status_checker(monkeypatch, tmp_path):
    fake_file = tmp_path / "card0-HDMI-A-1/status"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("connected\n")
    monkeypatch.setattr(glob, "glob", lambda pattern: [str(fake_file)])
    assert HDMIStatusChecker.is_connected()

    fake_file.write_text("disconnected")
    assert not HDMIStatusChecker.is_connected()

def test_sensor_service_monitor_active(monkeypatch):
    monitor = SensorServiceMonitor()
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kw: b"active\n")
    assert monitor.is_sensor_active()

    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kw: (_ for _ in ()).throw(Exception()))
    assert not monitor.is_sensor_active()

def test_wrap_text_and_fallback(monkeypatch):
    # set up a fake screen
    disp = BasePygameDisplay()
    class FakeFont:
        def __init__(self, size):
            self._size = size
        def size(self, text):
            return (len(text)*self._size, self._size)
    monkeypatch.setattr(pygame, "font", pygame.font)
    monkeypatch.init = MagicMock()
    disp.screen = MagicMock(get_size=lambda: (100, 50))
    # wrap text
    font = FakeFont(5)
    lines = disp._wrap_text("hello world", font, 90)
    assert any("hello" in w or "world" in w for w in lines)

    # check_connection when display not inited
    disp.screen = None
    pygame.display.get_init = MagicMock(return_value=False)
    assert not disp.check_connection()

def test_hdmi_status_checker(monkeypatch, tmp_path):
    # simulate a status file
    st = tmp_path / "card0-HDMI-A-1" / "status"
    st.parent.mkdir(parents=True)
    st.write_text("connected\n")
    monkeypatch.setattr(glob, "glob", lambda p: [str(st)])
    assert HDMIStatusChecker.is_connected() is True

    st.write_text("disconnected")
    assert HDMIStatusChecker.is_connected() is False

def test_sensor_service_monitor(monkeypatch):
    # active
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: b"active\n")
    assert SensorServiceMonitor().is_sensor_active() is True
    # exception => not active
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: (_ for _ in ()).throw(Exception()))
    assert SensorServiceMonitor().is_sensor_active() is False

def test_base_pygame_wrap_and_fallback(monkeypatch):
    d = BasePygameDisplay()
    # stub screen size & font
    d.screen = pygame.Surface((100, 40))
    class F:
        def __init__(self, s): self.s = s
        def size(self, txt): return (len(txt) * self.s, self.s)
    monkeypatch.setattr(pygame, "font", pygame.font)
    font = F(6)
    lines = d._wrap_text("hello world foo bar", font, 50)
    # at least splits into multiple segments
    assert len(lines) > 1

    # test check_connection fallback when display uninitialized
    d.screen = None
    monkeypatch.setattr(pygame.display, "get_init", lambda: False)
    assert d.check_connection() is False

def test_pitft_and_hdmi_display_check(monkeypatch, tmp_path):
    # Create mock devices
    drm_path = "/dev/dri/card2"  # The exact path we check in PiTFTDisplay
    fb_path = "/dev/fb0"         # The exact framebuffer path
    
    # Mock os.path.exists to return True for our devices
    def mock_exists(path):
        return path in [drm_path, fb_path]
    monkeypatch.setattr(os.path, "exists", mock_exists)
    
    # Mock os.access directly (not os.access.access)
    monkeypatch.setattr(os, "access", lambda p, m: True)
    
    # Stub the base class to always say "connected"
    monkeypatch.setattr(BasePygameDisplay, "check_connection", lambda self: True)
    
    # Test PiTFT
    pit = PiTFTDisplay()
    assert pit.check_connection() is True

    # HDMIDisplay test
    monkeypatch.setattr(HDMIStatusChecker, "is_connected", lambda: True)
    hd = HDMIDisplay()
    assert hd.check_connection() is True
