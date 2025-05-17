import sys
import os
import time
import threading
import asyncio

# insert project root (three levels up) so we can import DisplayController.aspects and DataCommunicator.source
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DisplayController.aspects.aop_decorators import log_call, catch_errors

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient import BaseDataClient

from display_impl import PiTFTDisplay, HDMIDisplay, HDMIStatusChecker


class DisplayController(BaseDataClient):
    """
    Subscribes to 'display' messages over WebSocket,
    maintains an IDisplay (PiTFT or HDMI), and
    re-renders every draw_interval seconds.
    """

    def __init__(
        self,
        name: str,
        connection: WebSocketConnection,
        use_hdmi: bool = False,
        override_timeout: float = 10.0,
        draw_interval: float = 0.2,
    ):
        # Initialize BaseDataClient (sets self.name & self.connection)
        super().__init__(name, connection)

        # Configuration
        self.use_hdmi = use_hdmi
        self.override_timeout = override_timeout
        self.draw_interval = draw_interval

        # State for incoming display payload overrides
        self.override_data = None
        self.override_ts = 0.0
        self.lock = threading.Lock()

        # The active IDisplay implementation
        self.display = None

        # The background draw-loop task
        self._draw_task: asyncio.Task | None = None

    @log_call
    async def start(self):
        """
        Overrides BaseDataClient.start so we can AOP-log it.
        This will connect the WebSocket and then invoke run().
        """
        return await super().start()

    @log_call
    async def stop(self):
        """
        Cleanly shut down:
         - cancel the draw loop
         - stop the current display
         - then call BaseDataClient.stop (if implemented)
        """
        if self._draw_task:
            self._draw_task.cancel()
            try:
                await self._draw_task
            except asyncio.CancelledError:
                pass

        if self.display:
            self.display.stop()

        # If BaseDataClient provides a stop/cleanup, call it
        if hasattr(super(), "stop"):
            return await super().stop()

    @log_call
    async def run(self):
        """
        Called by BaseDataClient after connect:
         1) Subscribe to the 'display' topic
         2) Launch the async draw-loop
         3) Await it forever to keep the client alive
        """
        await self.connection.subscribe("display")

        # BaseDataClient wiring will ensure on_message is called below
        self._draw_task = asyncio.create_task(self._loop())
        await self._draw_task

    @catch_errors
    async def on_message(self, frm: str, payload: dict):
        """
        Receives any incoming messages on 'display'; update override.
        """
        self.update_display(payload)

    @log_call
    def update_display(self, data: dict):
        """
        Thread-safe update of the override payload and timestamp.
        """
        with self.lock:
            self.override_data = data
            self.override_ts = time.time()

    @log_call
    def set_display(self, disp):
        """
        Stop any existing display and start the new one.
        """
        if self.display:
            self.display.stop()
        self.display = disp
        self.display.start()

    @log_call
    def draw(self):
        """
        Chooses override vs. fallback and calls IDisplay.draw(...)
        """
        now = time.time()
        with self.lock:
            valid = (
                self.override_data is not None
                and (now - self.override_ts) <= self.override_timeout
            )
            data = self.override_data if valid else None

        self.display.draw(data)

    @log_call
    async def _loop(self):
        """
        The main draw-loop:
         - Every draw_interval seconds:
            1. Pick PiTFT vs HDMI (auto-detect)
            2. set_display(...) if it changed
            3. draw()
        """
        while True:
            # decide which impl we want
            Desired = PiTFTDisplay if not self.use_hdmi else HDMIDisplay

            # if display has been unplugged / failed, recreate it
            if (
                self.display is None
                or not self.display.check_connection()
                or not isinstance(self.display, Desired)
            ):
                if self.display:
                    self.display.stop()
                self.display = Desired()
                self.display.start()

            # render
            self.draw()
            await asyncio.sleep(self.draw_interval)