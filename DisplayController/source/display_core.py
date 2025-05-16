import time
import threading
import socket
import json
import functools
from abc import ABC, abstractmethod
from aspects.aop_decorators import log_call, catch_errors, measure_time


# === Display Interface ===
class DisplayInterface(ABC):
    @abstractmethod
    def show(self, title: str, lines: list[dict]):
        pass

# === Base State Pattern ===
class BaseState(ABC):
    def on_entry(self, client): pass
    def on_tick(self, client): pass

    def on_button(self, client, name):
        if name == "halt":
            client.change_state(PausedState())
        elif name == "cancel":
            client.change_state(CancelledState())
        elif name == "ventilate":
            client.change_state(VentilatingState())
        elif name == "start":
            client.change_state(LoadingState())

class IdleState(BaseState):
    @log_call
    def on_entry(self, client):
        client._stop_predictor()
        client.send_idle_message()
        client._last_heartbeat = time.time()

    def on_tick(self, client):
        if time.time() - client._last_heartbeat > client.keepalive:
            client.send_idle_message()
            client._last_heartbeat = time.time()

class LoadingState(BaseState):
    @log_call
    def on_entry(self, client):
        client._stop_predictor()
        client.timer_start = time.time()
        client._last_remaining = None
        client.send_loading(client.loading_duration)

    @measure_time
    def on_tick(self, client):
        rem = max(int(client.loading_duration - (time.time() - client.timer_start)), 0)
        if rem != client._last_remaining:
            client.send_loading(rem)
            client._last_remaining = rem
        if rem == 0:
            client.change_state(PredictingState())

class PredictingState(BaseState):
    @log_call
    def on_entry(self, client):
        client._start_predictor()

class VentilatingState(BaseState):
    @log_call
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

class PausedState(BaseState):
    @log_call
    def on_entry(self, client):
        client._stop_predictor()
        client.send_paused()
        client._last_heartbeat = time.time()

    def on_tick(self, client):
        if time.time() - client._last_heartbeat > client.keepalive:
            client.send_paused()
            client._last_heartbeat = time.time()

class CancelledState(BaseState):
    @log_call
    def on_entry(self, client):
        client._stop_predictor()
        client.send_message("Cancelled", ["Operation was cancelled."])
        threading.Timer(2, lambda: client.change_state(IdleState())).start()
