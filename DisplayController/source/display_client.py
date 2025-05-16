import time
import threading
import socket
import json
try:
    # real Pi
    import RPi.GPIO as GPIO
except ImportError:
    # off-Pi, fall back to fake-rpi stub
    import fake_rpi
    # fake_rpi.RPi is the top-level, and fake_rpi.RPi.GPIO the submodule
    sys.modules['RPi']      = fake_rpi.RPi
    sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO
    import RPi.GPIO as GPIO

from display_core import (
    DisplayInterface, BaseState, IdleState, LoadingState, PredictingState,
    VentilatingState, PausedState, CancelledState, log_call, catch_errors
)

# === Configuration ===
SOCKET_PORT = 9999
SOCKET_HOST = "localhost"

BUTTON_PINS = {
    "start": 17,
    "ventilate": 22,
    "cancel": 23,
    "halt": 27,
}

# === DisplayClient with State Pattern ===
class DisplayClient:
    def __init__(self, display: DisplayInterface, loading_duration=5, ventilation_duration=300, keepalive=5):
        self.display = display
        self.loading_duration = loading_duration
        self.ventilation_duration = ventilation_duration
        self.keepalive = keepalive

        self.timer_start = None
        self._last_remaining = None

        # prediction machinery
        self.on_predict = None
        self._predict_thread = None
        self._predict_stop_event = threading.Event()

        # heartbeat timestamp (used by Idle and Paused states)
        self._last_heartbeat = None

        self._lock = threading.Lock()
        self._running = False
        self._state = None
        self._state_thread = threading.Thread(target=self._state_machine, daemon=True)

        self._setup_gpio()

    @log_call
    def change_state(self, new_state: BaseState):
        self._state = new_state
        self._state.on_entry(self)

    def start(self):
        self._running = True
        # kickoff into IdleState (sends initial Ready)
        self.change_state(IdleState())
        self._state_thread.start()

    def stop(self):
        self._running = False
        self._state_thread.join()
        GPIO.cleanup()

    # === GPIO wiring ===
    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        for name, pin in BUTTON_PINS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin,
                GPIO.FALLING,
                callback=lambda ch, n=name: self._button_pressed(n),
                bouncetime=200
            )
    
    @log_call
    def _button_pressed(self, name):
        with self._lock:
            # delegate to state
            self._state.on_button(self, name)

    # === Socket communication ===
    @catch_errors
    def _send_payload(self, payload):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SOCKET_HOST, SOCKET_PORT))
            s.sendall(json.dumps(payload).encode())

    def send_message(self, title, lines):
        formatted = []
        for line in lines:
            if isinstance(line, str):
                formatted.append({"text": line, "color": [255, 255, 255]})
            else:
                formatted.append(line)
        self._send_payload({"title": title, "lines": formatted})

    def send_idle_message(self):
        self.send_message("READY", [
            {"text": "Insert sample", "color": [255, 255, 255]},
            {"text": "Press START to begin", "color": [0, 255, 0]}
        ])


    def send_paused(self):
        self.send_message("PAUSED", [
            {"text": "The process is currently halted.", "color": [255, 255, 0]},
            {"text": "Press any button to resume or cancel.", "color": [200, 200, 200]}
        ])


    def send_loading(self, remaining):
        dots = "." * ((int(time.time()) % 3) + 1)
        self.send_message("LOADING" + dots, [
            {"text": f"{remaining} seconds remaining", "color": [200, 200, 255]},
            {"text": "Detecting aroma", "color": [150, 150, 255]}
        ])

    def send_prediction(self, scent, confidence):
        pct = float(confidence) * 100

        if pct < 50:
            color = [255, 0, 0]       # Red for low confidence
        elif pct < 80:
            color = [255, 255, 0]     # Yellow for medium
        else:
            color = [0, 255, 0]       # Green for high

        self.send_message("PREDICTION RESULT", [
            {"text": scent.upper(), "color": [255, 255, 255]},
            {"text": f"Confidence: {pct:.1f}%", "color": color}
        ])



    def send_ventilation_timer(self, remaining):
        mins = remaining // 60
        secs = remaining % 60
        self.send_message("VENTILATING", [
            {"text": f"Time left: {mins}:{secs:02d}", "color": [0, 200, 255]},
            {"text": "Clearing air", "color": [150, 150, 200]}
        ])


    def _start_predictor(self):
        if not self.on_predict:
            return
        self._predict_stop_event.clear()

        def _loop():
            while not self._predict_stop_event.is_set():
                try:
                    scent, confidence = self.on_predict()
                    self.send_prediction(scent, confidence)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"[Predictor] Error: {e}")
                    break

        self._predict_thread = threading.Thread(target=_loop, daemon=True)
        self._predict_thread.start()

    def _stop_predictor(self):
        self._predict_stop_event.set()
        if self._predict_thread:
            self._predict_thread.join(timeout=0.5)
            self._predict_thread = None

    # === State machine loop ===
    def _state_machine(self):
        while self._running:
            with self._lock:
                self._state.on_tick(self)
            time.sleep(0.1)

# === HDMI and PiTFT display implementations ===
class HDMIDisplay(DisplayInterface):
    def show(self, title, lines):
        print(f"=== {title} ===")
        for line in lines:
            print(line["text"])

class PiTFTDisplay(DisplayInterface):
    def show(self, title, lines):
        print(f"[PiTFT] {title}")
        for line in lines:
            print(f"{line['text']}")
