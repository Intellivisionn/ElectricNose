# DisplayController/io/state_machine.py

import sys, os
# insert project root (one level up from DisplayController/source) onto PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

import time
import threading
from abc import ABC
from DisplayController.aspects.aop_decorators import log_call, catch_errors

class State(ABC):
    def on_entry(self, handler): pass
    def on_tick(self,  handler): pass
    def on_button(self, handler, name): pass

class IdleState(State):
    @log_call
    def on_entry(self, handler):
        handler._stop_predictor()
        handler.send_idle_message()
        handler._last_heartbeat = time.time()

    @log_call
    def on_tick(self, handler):
        if time.time() - handler._last_heartbeat > handler.keepalive:
            handler.send_idle_message()
            handler._last_heartbeat = time.time()

    @log_call
    def on_button(self, handler, name):
        if name == "start":
            handler.change_state(LoadingState())
        elif name == "ventilate":
            handler.change_state(VentilatingState())

class LoadingState(State):
    @log_call
    def on_entry(self, handler):
        handler._stop_predictor()
        handler.timer_start = time.time()
        handler._last_remaining = None
        handler.send_loading(handler.loading_duration)

    @log_call
    def on_tick(self, handler):
        rem = max(int(handler.loading_duration - (time.time() - handler.timer_start)), 0)
        if rem != handler._last_remaining:
            handler.send_loading(rem)
            handler._last_remaining = rem
        if rem == 0:
            handler.change_state(PredictingState())

    @log_call
    def on_button(self, handler, name):
        if name == "halt":
            handler.change_state(PausedState())
        elif name == "cancel":
            handler.change_state(CancelledState())
        elif name == "ventilate":
            handler.change_state(VentilatingState())

class PredictingState(State):
    @log_call
    def on_entry(self, handler):
        handler._start_predictor()

    @log_call
    def on_button(self, handler, name):
        if name == "cancel":
            handler.change_state(CancelledState())
        elif name == "halt":
            handler.change_state(PausedState())
        elif name == "ventilate":
            handler.change_state(VentilatingState())

class VentilatingState(State):
    @log_call
    def on_entry(self, handler):
        handler._stop_predictor()
        handler.timer_start = time.time()
        handler._last_remaining = None
        handler.send_ventilation_timer(handler.ventilation_duration)

    @log_call
    def on_tick(self, handler):
        rem = max(int(handler.ventilation_duration - (time.time() - handler.timer_start)), 0)
        if rem != handler._last_remaining:
            handler.send_ventilation_timer(rem)
            handler._last_remaining = rem
        if rem == 0:
            handler.change_state(IdleState())

    @log_call
    def on_button(self, handler, name):
        if name == "cancel":
            handler.change_state(CancelledState())
        elif name == "halt":
            handler.change_state(PausedState())

class PausedState(State):
    @log_call
    def on_entry(self, handler):
        handler._stop_predictor()
        handler.send_paused()
        handler._last_heartbeat = time.time()

    @log_call
    def on_tick(self, handler):
        if time.time() - handler._last_heartbeat > handler.keepalive:
            handler.send_paused()
            handler._last_heartbeat = time.time()

    @log_call
    def on_button(self, handler, name):
        # any button returns to ready
        handler.change_state(IdleState())

class CancelledState(State):
    @log_call
    def on_entry(self, handler):
        # stop any in-flight predictor
        handler._stop_predictor()
        # send the one and only “cancelled” payload
        handler.send_message("Cancelled", ["Operation was cancelled."])
        # bookmark the time so we can re-send every keepalive
        #handler._last_heartbeat = time.time()
        threading.Timer(10, lambda: handler.change_state(IdleState())).start()

    @log_call
    def on_tick(self, handler):
        # every keepalive seconds, re-send "Cancelled"
        if time.time() - handler._last_heartbeat > handler.keepalive:
            handler.send_message("Cancelled", ["Operation was cancelled."])
            handler._last_heartbeat = time.time()

    @log_call
    def on_button(self, handler, name):
        # only START will actually leave Cancelled
        if name == "start":
            handler.change_state(LoadingState())
        # all other buttons are ignored here to keep the "Cancelled" message up