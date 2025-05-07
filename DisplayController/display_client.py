# display_client.py

import socket
import json
import time
import threading
import RPi.GPIO as GPIO

# === Configuration ===
SOCKET_PORT = 9999
SOCKET_HOST = "localhost"
KEEPALIVE_INTERVAL = 5  # seconds; keeps display alive during IDLE and PAUSED

BUTTON_PINS = {
    "start":      17,
    "ventilate":  22,
    "cancel":     23,
    "halt":       27,
}


# === State Pattern Base ===
class State:
    def on_entry(self, client):
        pass

    def on_tick(self, client):
        pass

    def on_button(self, client, name):
        # default: any button overrides into its state
        if name == "halt":
            client.change_state(PausedState())
        elif name == "cancel":
            client.change_state(CancelledState())
        elif name == "ventilate":
            client.change_state(VentilatingState())
        elif name == "start":
            client.change_state(LoadingState())


class IdleState(State):
    def on_entry(self, client):
        client._stop_predictor()
        client.send_idle_message()
        client._last_heartbeat = time.time()

    def on_tick(self, client):
        if time.time() - client._last_heartbeat > KEEPALIVE_INTERVAL:
            client.send_idle_message()
            client._last_heartbeat = time.time()


class LoadingState(State):
    def on_entry(self, client):
        client._stop_predictor()
        client.timer_start = time.time()
        client._last_remaining = None
        client.send_loading(client.loading_duration)

    def on_tick(self, client):
        rem = max(int(client.loading_duration - (time.time() - client.timer_start)), 0)
        if rem != client._last_remaining:
            client.send_loading(rem)
            client._last_remaining = rem
        if rem == 0:
            client.change_state(PredictingState())


class PredictingState(State):
    def on_entry(self, client):
        client._start_predictor()

    def on_tick(self, client):
        # predictor thread handles continuous send
        pass


class VentilatingState(State):
    def on_entry(self, client):
        client._stop_predictor()
        client.timer_start = time.time()
        client._last_remaining = None
        client.send_ventilation_timer(client.ventilation_duration)

    def on_tick(self, client):
        rem = max(int(client.ventilation_duration - (time.time() - client.timer_start)), 0)
        if rem != client._last_remaining:
            client.send_ventilation_timer(rem)
            client._last_remaining = rem
        if rem == 0:
            client.change_state(IdleState())


class PausedState(State):
    def on_entry(self, client):
        client._stop_predictor()
        client.send_paused()
        client._last_heartbeat = time.time()

    def on_tick(self, client):
        if time.time() - client._last_heartbeat > KEEPALIVE_INTERVAL:
            client.send_paused()
            client._last_heartbeat = time.time()


class CancelledState(State):
    def on_entry(self, client):
        client._stop_predictor()
        client.send_message("Cancelled", ["Operation was cancelled."])
        # after a brief pause, go back to idle
        threading.Timer(2, lambda: client.change_state(IdleState())).start()


# === DisplayClient with State Pattern ===
class DisplayClient:
    def __init__(self, loading_duration=5, ventilation_duration=300):
        self.loading_duration = loading_duration
        self.ventilation_duration = ventilation_duration

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

    def change_state(self, new_state):
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

    def _button_pressed(self, name):
        with self._lock:
            # delegate to state
            self._state.on_button(self, name)

    # === Socket communication ===
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

    # === Single-shot prediction API ===
    def provide_prediction(self, scent, confidence):
        self.send_prediction(scent, confidence)

    # === Continuous predictor control ===
    def _start_predictor(self):
        if not self.on_predict:
            return
        self._predict_stop_event.clear()

        def _loop():
            while not self._predict_stop_event.is_set():
                try:
                    res = self.on_predict()
                    if isinstance(res, tuple) and len(res) == 2:
                        self.send_prediction(*res)
                except Exception as e:
                    print(f"[DisplayClient] Prediction error: {e}")
                    break
                time.sleep(0.1)

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