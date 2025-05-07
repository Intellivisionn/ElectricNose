import socket
import json
import time
import threading
import RPi.GPIO as GPIO
from enum import Enum

# === Configuration ===
SOCKET_PORT = 9999
SOCKET_HOST = "localhost"
# must be less than main.py’s OVERRIDE_TIMEOUT
KEEPALIVE_INTERVAL = 5  # seconds

BUTTON_PINS = {
    "start": 17,       # Button 1
    "ventilate": 22,   # Button 2
    "cancel": 23,      # Button 3
    "halt": 27         # Button 4
}


class DisplayState(Enum):
    IDLE = "idle"
    LOADING = "loading"
    PREDICTING = "predicting"
    VENTILATING = "ventilating"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class DisplayClient:
    def __init__(self, loading_duration=5, ventilation_duration=300):
        self.state = DisplayState.IDLE
        self.loading_duration = loading_duration
        self.ventilation_duration = ventilation_duration

        self.timer_start = None
        self._last_remaining = None

        self.on_predict = None
        self._prediction_data = None
        self._prediction_sent = False

        # heartbeat bookkeeping
        self.keepalive_interval = KEEPALIVE_INTERVAL
        self._last_idle_sent_time = 0

        self._lock = threading.Lock()
        self._running = False
        self._state_thread = threading.Thread(target=self._state_machine, daemon=True)

        self._setup_gpio()

    def start(self):
        # initial idle to populate the display
        self.send_idle_message()
        self._last_idle_sent_time = time.time()

        self._running = True
        self._state_thread.start()

    def stop(self):
        self._running = False
        self._state_thread.join()
        GPIO.cleanup()

    # === GPIO Setup ===
    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        for name, pin in BUTTON_PINS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin,
                GPIO.FALLING,
                callback=lambda channel, n=name: self._button_pressed(n),
                bouncetime=200
            )

    def _button_pressed(self, name):
        with self._lock:
            if name == "halt":
                self.state = DisplayState.PAUSED
            elif name == "cancel":
                self.state = DisplayState.CANCELLED
            elif name == "ventilate":
                self.state = DisplayState.VENTILATING
            elif name == "start":
                self.state = DisplayState.LOADING

    # === Socket Communication ===
    def _send_payload(self, payload):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SOCKET_HOST, SOCKET_PORT))
                s.sendall(json.dumps(payload).encode())
        except Exception as e:
            print(f"[DisplayClient] Socket error: {e}")

    def send_message(self, title, lines):
        formatted = []
        for line in lines:
            if isinstance(line, str):
                formatted.append({"text": line, "color": [255, 255, 255]})
            else:
                formatted.append(line)
        self._send_payload({"title": title, "lines": formatted})

    def send_idle_message(self):
        self.send_message("Ready", ["Insert sample and press START."])

    def send_paused(self):
        self.send_message("Paused", ["The process is currently halted."])

    def send_loading(self, remaining):
        self.send_message("Loading...", [f"{remaining} seconds remaining..."])

    def send_prediction(self, scent, confidence):
        pct = float(confidence) * 100
        self.send_message("Prediction", [
            {"text": scent, "color": [255, 255, 255]},
            {"text": f"Confidence: {pct:.1f}%", "color": [0, 255, 0]}
        ])

    def send_ventilation_timer(self, remaining):
        mins = remaining // 60
        secs = remaining % 60
        self.send_message("Ventilating", [f"{mins}:{secs:02d} remaining..."])

    # === External API ===
    def provide_prediction(self, scent, confidence):
        with self._lock:
            self._prediction_data = (scent, confidence)

    # === State Machine ===
    def _state_machine(self):
        last_state = None
        while self._running:
            with self._lock:
                state = self.state

                # === on-entry actions ===
                if state != last_state:
                    now = time.time()
                    self._last_remaining = None
                    self._prediction_sent = False

                    if state == DisplayState.IDLE:
                        self.send_idle_message()
                        self._last_idle_sent_time = now

                    elif state == DisplayState.LOADING:
                        self.timer_start = now
                        self.send_loading(self.loading_duration)

                    elif state == DisplayState.PREDICTING:
                        if self.on_predict:
                            threading.Thread(target=self._run_prediction, daemon=True).start()

                    elif state == DisplayState.VENTILATING:
                        self.timer_start = now
                        self.send_ventilation_timer(self.ventilation_duration)

                    elif state == DisplayState.PAUSED:
                        self.send_paused()

                    elif state == DisplayState.CANCELLED:
                        self.send_message("Cancelled", ["Operation was cancelled."])
                        time.sleep(2)
                        self.state = DisplayState.IDLE

                    last_state = state

                # === persistent-state actions ===
                else:
                    now = time.time()

                    if state == DisplayState.IDLE:
                        # heartbeat to keep override active
                        if now - self._last_idle_sent_time >= self.keepalive_interval:
                            self.send_idle_message()
                            self._last_idle_sent_time = now

                    elif state == DisplayState.LOADING:
                        remaining = max(int(self.loading_duration - (now - self.timer_start)), 0)
                        if remaining != self._last_remaining:
                            self.send_loading(remaining)
                            self._last_remaining = remaining
                        if remaining == 0:
                            self.state = DisplayState.PREDICTING

                    elif state == DisplayState.PREDICTING:
                        if self._prediction_data and not self._prediction_sent:
                            scent, conf = self._prediction_data
                            self.send_prediction(scent, conf)
                            self._prediction_sent = True

                    elif state == DisplayState.VENTILATING:
                        remaining = max(int(self.ventilation_duration - (now - self.timer_start)), 0)
                        if remaining != self._last_remaining:
                            self.send_ventilation_timer(remaining)
                            self._last_remaining = remaining
                        if remaining == 0:
                            self.state = DisplayState.IDLE

            time.sleep(0.1)

    def _run_prediction(self):
        try:
            result = self.on_predict()
            if isinstance(result, tuple) and len(result) == 2:
                with self._lock:
                    self._prediction_data = result
        except Exception as e:
            print(f"[DisplayClient] Prediction callback error: {e}")