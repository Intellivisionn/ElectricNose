import os
import sys
import asyncio
import threading
import time

# ==== PYTHONPATH HACK ====
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DisplayController.aspects.aop_decorators import log_call, catch_errors
from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient   import BaseDataClient
from DisplayController.io.io_input_handler import IButtonInput
from DisplayController.io.io_interfaces import IIOHandler
from DisplayController.io.state_machine  import (
    IdleState, LoadingState, PredictingState,
    VentilatingState, CancelledState
)


class IOHandler(BaseDataClient, IIOHandler):
    """
    Handles hardware buttons + WebSocket 'control' messages,
    drives a FSM, and emits display payloads.
    """

    def __init__(
        self,
        name: str,
        connection: WebSocketConnection,
        button_input: IButtonInput,
        use_hdmi: bool = False,
        loading_duration: float = 250.0,
        ventilation_duration: float = 300.0,
        keepalive: float = 5.0
    ):
        super().__init__(name, connection)
        self._button_input        = button_input
        self.use_hdmi             = use_hdmi
        self.loading_duration     = loading_duration
        self.ventilation_duration = ventilation_duration
        self.keepalive            = keepalive

        # for scheduling sends from any thread
        self._event_loop: asyncio.AbstractEventLoop | None = None

        # FSM
        self._state = IdleState()
        self._lock  = threading.Lock()
        self._task: asyncio.Task | None = None

        # timers & predictor
        self.timer_start         = None
        self._last_remaining     = None
        self._last_heartbeat     = None
        self.on_predict          = None
        self._predict_thread     = None
        self._predict_stop_event = threading.Event()

    #
    # ─── LIFECYCLE ───────────────────────────────────────────────────────────────
    #

    @log_call
    async def start(self):
        # capture the running loop so we can schedule from sync context
        self._event_loop = asyncio.get_running_loop()
        return await super().start()

    @log_call
    async def run(self):
        # subscribe to prediction events
        await self.connection.subscribe("prediction")

        # initial entry into IdleState
        with self._lock:
            self._state.on_entry(self)

        # start FSM tick‐loop
        self._task = asyncio.create_task(self._loop())

        # start listening for hardware buttons
        try:
            self._button_input.listen(self._on_button)
        except Exception as e:
            print(f"[IOHandler] WARN button listen failed: {e}")

        await self._task

    @log_call
    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if hasattr(super(), "stop"):
            await super().stop()

    #
    # ─── INTERNAL DISPLAY SENDER ──────────────────────────────────────────────────
    #

    @catch_errors
    def _send_payload(self, payload: dict):
        # thread‐safe scheduling of the send coroutine
        if not self._event_loop:
            try:
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                return
        # **always** publish on topic:display
        self._event_loop.call_soon_threadsafe(
            self._event_loop.create_task,
            self.connection.send('topic:display', payload)
        )

    def send_message(self, title: str, lines: list[dict] | list[str]):
        formatted = []
        for ln in lines:
            if isinstance(ln, str):
                formatted.append({ "text": ln, "color": [255,255,255] })
            else:
                formatted.append(ln)
        self._send_payload({ "title": title, "lines": formatted })

    def send_idle_message(self):
        self.send_message("READY", [
            { "text": "Insert sample",        "color": [255,255,255] },
            { "text": "Press START to begin", "color": [0,255,0]     },
        ])

    def send_loading(self, remaining: int):
        dots = "." * ((int(time.time()) % 3) + 1)
        self.send_message("LOADING" + dots, [
            { "text": "Detecting aroma",                "color": [150,150,255] },
            { "text": f"{remaining} seconds remaining", "color": [200,200,255] },
        ])

    def send_prediction(self, scent: str, confidence: float):
        pct = confidence * 100.0
        if pct < 50:
            color = [255,0,0]
        elif pct < 80:
            color = [255,255,0]
        else:
            color = [0,255,0]
        self.send_message("PREDICTION RESULT", [
            { "text": scent.upper(),               "color": [255,255,255] },
            { "text": f"Confidence {pct:.1f}%",   "color": color         },
            { "text": "Press CONTINUE to proceed", "color": [200,200,200] },
        ])

    def send_ventilation_timer(self, remaining: int):
        mins = remaining // 60
        secs = remaining % 60
        self.send_message("VENTILATING", [
            { "text": f"Time left: {mins}:{secs:02d}", "color": [0,200,255] },
            { "text": "Clearing air",                  "color": [150,150,200] },
        ])

    #
    # ─── PREDICTOR THREAD MANAGEMENT ────────────────────────────────────────────
    #

    def _start_predictor(self):
        if not self.on_predict:
            return
        self._predict_stop_event.clear()
        def _loop():
            while not self._predict_stop_event.is_set():
                try:
                    scent, conf = self.on_predict()
                    self.send_prediction(scent, conf)
                    time.sleep(0.1)
                except Exception:
                    break
        self._predict_thread = threading.Thread(target=_loop, daemon=True)
        self._predict_thread.start()

    def _stop_predictor(self):
        self._predict_stop_event.set()
        if self._predict_thread:
            self._predict_thread.join(timeout=0.5)
            self._predict_thread = None

    #
    # ─── FSM TRANSITIONS ─────────────────────────────────────────────────────────
    #

    @log_call
    def change_state(self, new_state):
        # 1) stop any running predictor
        self._stop_predictor()

        # 2) swap in the new state
        self._state = new_state

        # 3) broadcast the state‐name: **always** on topic:state
        state_name = new_state.__class__.__name__
        payload = {"state": state_name}
        self._event_loop.call_soon_threadsafe(
            self._event_loop.create_task,
            self.connection.send("topic:state", payload)
        )

        # 4) fire its on_entry (sends the UI payload)
        self._state.on_entry(self)

    #
    # ─── EVENT HOOKS ─────────────────────────────────────────────────────────────
    #

    @catch_errors
    async def on_message(self, frm: str, payload: dict):
        # control messages
        if "cmd" in payload:
            with self._lock:
                self._state.on_button(self, payload["cmd"])

        # prediction messages
        elif "scent" in payload and "confidence" in payload:
            if isinstance(self._state, PredictingState):
                self._last_prediction = (payload["scent"], payload["confidence"])
                self._last_heartbeat = time.time()
                self.send_prediction(payload["scent"], payload["confidence"])

    def _on_button(self, name: str):
        # hardware button callback
        print(f"[IOHandler DEBUG] raw button → '{name}'")
        with self._lock:
            self._state.on_button(self, name)

    #
    # ─── FSM TICK LOOP ───────────────────────────────────────────────────────────
    #

    @log_call
    async def _loop(self):
        while True:
            with self._lock:
                # if we're in PredictingState and haven't heard anything for keepalive,
                # auto‐transition to VentilatingState
                if isinstance(self._state, PredictingState) and self._last_heartbeat is not None:
                    if time.time() - self._last_heartbeat > self.keepalive:
                        self.change_state(VentilatingState())
                        # skip on_tick for this iteration
                        continue

                self._state.on_tick(self)

            await asyncio.sleep(0.1)

    #
    # ─── IIOHandler plumbing ─────────────────────────────────────────────────────
    #

    async def connect(self, uri: str):
        return await self.connection.connect(uri)

    async def send(self, topic: str, payload: dict):
        return await self.connection.send(f"topic:{topic}", payload)

    def on_button_press(self, name: str):
        return self._on_button(name)