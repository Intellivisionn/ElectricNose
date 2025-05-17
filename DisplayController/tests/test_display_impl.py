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