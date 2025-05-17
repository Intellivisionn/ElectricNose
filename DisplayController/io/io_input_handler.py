# DisplayController/io/io_input_handler.py

import os
import sys
import threading
import time

# ==== PYTHONPATH HACK ====
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

# Try real RPi.GPIO, else use fake_rpi stub
try:
    import RPi.GPIO as GPIO
except ImportError:
    import fake_rpi
    sys.modules['RPi']      = fake_rpi.RPi
    sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO
    import RPi.GPIO as GPIO

from abc import ABC, abstractmethod
from DisplayController.aspects.aop_decorators import log_call

class IButtonInput(ABC):
    @abstractmethod
    def on_button_press(self, name: str): ...
    @abstractmethod
    def listen(self, callback: callable): ...

class ButtonHandler(IButtonInput):
    def __init__(self, button_pins: dict[str,int]):
        """
        button_pins: mapping from button-name -> BCM pin number
        """
        self.button_pins = button_pins
        # for polling fallback
        self._poll_pins: dict[int,str] = {}
        self._last_states: dict[int,bool] = {}
        self._stop_poll = threading.Event()
        self._poll_thread: threading.Thread | None = None

    @log_call
    def listen(self, callback: callable):
        GPIO.setmode(GPIO.BCM)
        for name, pin in self.button_pins.items():
            try:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(
                    pin,
                    GPIO.FALLING,
                    callback=lambda ch, n=name: callback(n),
                    bouncetime=200
                )
            except Exception as e:
                print(f"[ButtonHandler] WARN: cannot add edge detection on pin {pin}: {e}")
                # fall back to polling
                self._poll_pins[pin] = name
                # initialize last state
                try:
                    self._last_states[pin] = GPIO.input(pin)
                except Exception:
                    self._last_states[pin] = True  # assume not-pressed

        if self._poll_pins:
            self._start_polling(callback)

    def _start_polling(self, callback: callable):
        if self._poll_thread:
            return
        def poll_loop():
            while not self._stop_poll.is_set():
                for pin, name in self._poll_pins.items():
                    try:
                        state = GPIO.input(pin)
                    except Exception:
                        state = True
                    last = self._last_states.get(pin, True)
                    # detect falling edge: HIGH -> LOW
                    if last and not state:
                        callback(name)
                        # simple debounce
                        time.sleep(0.2)
                    self._last_states[pin] = state
                time.sleep(0.05)
        self._poll_thread = threading.Thread(target=poll_loop, daemon=True)
        self._poll_thread.start()

    @log_call
    def on_button_press(self, name: str):
        # satisfies interface – actual presses come via listen()
        pass

    def stop(self):
        """Call this on shutdown to stop the polling thread."""
        self._stop_poll.set()
        if self._poll_thread:
            self._poll_thread.join(timeout=0.5)