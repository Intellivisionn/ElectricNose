import socket
import json
import time
import RPi.GPIO as GPIO
from enum import Enum


# === Configuration ===
SOCKET_PORT = 9999
SOCKET_HOST = "localhost"

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


class DisplayManager:
    def __init__(self, loading_duration=5, ventilation_duration=300):
        self.state = DisplayState.IDLE
        self.last_states = {}
        self.last_sent_state = None
        self.timer_start = None

        self.loading_duration = loading_duration
        self.ventilation_duration = ventilation_duration
        self.prediction_data = None  # scent, confidence

        self._setup_gpio()
        self.send_idle_message()

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        for name, pin in BUTTON_PINS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.last_states[pin] = GPIO.input(pin)

    def cleanup(self):
        GPIO.cleanup()

    # === Socket Communication ===
    def _send_payload(self, payload):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SOCKET_HOST, SOCKET_PORT))
                s.sendall(json.dumps(payload).encode())
                print(f"[DisplayManager] Sent: {payload['title']}")
        except Exception as e:
            print(f"[DisplayManager] Socket error: {e}")

    def send_message(self, title, lines):
        formatted_lines = []
        for line in lines:
            if isinstance(line, str):
                formatted_lines.append({"text": line, "color": [255, 255, 255]})
            else:
                formatted_lines.append(line)
        self._send_payload({"title": title, "lines": formatted_lines})

    def send_idle_message(self):
        self.send_message("Ready", ["Insert sample and press START."])

    def send_paused(self):
        self.send_message("Paused", ["The process is currently halted."])

    def send_loading(self, remaining):
        self.send_message("Loading...", [f"{remaining} seconds remaining..."])

    def send_prediction(self, scent, confidence):
        confidence = float(confidence) * 100
        self.send_message("Prediction", [
            {"text": scent, "color": [255, 255, 255]},
            {"text": f"Confidence: {confidence:.1f}%", "color": [0, 255, 0]}
        ])

    def send_ventilation_timer(self, remaining):
        mins = remaining // 60
        secs = remaining % 60
        self.send_message("Ventilating", [f"{mins}:{secs:02d} remaining..."])

    # === Button Handling ===
    def _button_pressed(self, name):
        pin = BUTTON_PINS[name]
        current = GPIO.input(pin)
        if self.last_states[pin] == GPIO.HIGH and current == GPIO.LOW:
            self.last_states[pin] = current
            return True
        self.last_states[pin] = current
        return False

    # === Public API ===
    def step(self):
        now = time.time()

        # === Prioritize all button inputs BEFORE state logic ===
        pressed = {
            name: self._button_pressed(name)
            for name in BUTTON_PINS
        }

        # Define priority: halt > cancel > ventilate > start
        if pressed["halt"]:
            self._enter_state(DisplayState.PAUSED)
        elif pressed["cancel"]:
            self._enter_state(DisplayState.CANCELLED)
        elif pressed["ventilate"]:
            self._enter_state(DisplayState.VENTILATING)
        elif pressed["start"]:
            self._enter_state(DisplayState.LOADING)

        # === STATE-BASED ACTIONS ===
        if self.state == DisplayState.IDLE:
            if self.last_sent_state != DisplayState.IDLE:
                self.send_idle_message()
                self.last_sent_state = DisplayState.IDLE

        elif self.state == DisplayState.LOADING:
            elapsed = int(now - self.timer_start)
            remaining = max(self.loading_duration - elapsed, 0)
            self.send_loading(remaining)
            if remaining <= 0:
                self._enter_state(DisplayState.PREDICTING)

        elif self.state == DisplayState.PREDICTING:
            if self.prediction_data:
                scent, confidence = self.prediction_data
                self.send_prediction(scent, confidence)
                self.last_sent_state = DisplayState.PREDICTING
                self.prediction_data = None

        elif self.state == DisplayState.VENTILATING:
            elapsed = int(now - self.timer_start)
            remaining = max(self.ventilation_duration - elapsed, 0)
            self.send_ventilation_timer(remaining)
            if remaining <= 0:
                self._enter_state(DisplayState.IDLE)

        elif self.state == DisplayState.PAUSED:
            self.send_paused()

        elif self.state == DisplayState.CANCELLED:
            self.send_message("Cancelled", ["Operation was cancelled."])
            self._enter_state(DisplayState.IDLE)


    def _enter_state(self, new_state):
        if self.state != new_state:
            print(f"[STATE] {self.state.value} → {new_state.value}")
            self.state = new_state
            self.last_sent_state = None
            self.timer_start = time.time()

    def provide_prediction(self, scent, confidence):
        self.prediction_data = (scent, confidence)