import asyncio
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))
from DisplayController.io.io_handler import IOHandler
from DisplayController.io.io_input_handler import IButtonInput
from DataCommunicator.source.WebSocketConnection import WebSocketConnection

class MockButtonHandler(IButtonInput):
    def __init__(self):
        self._callback = None

    def listen(self, callback):
        self._callback = callback
        asyncio.create_task(self._simulate_buttons())

    async def _simulate_buttons(self):
        await asyncio.sleep(2)  # Give system time to initialize
        print("[MockIO] Simulating 'start' button press")
        self._callback("start")  # Triggers transition to LoadingState

    def on_button_press(self, name):
        pass

async def main():
    uri = "ws://localhost:8765"
    print(f"[MockIO] Connecting to {uri}")
    conn = WebSocketConnection(uri)
    button_handler = MockButtonHandler()
    io = IOHandler(
        name="io",
        connection=conn,
        button_input=button_handler,
        use_hdmi=False,
        loading_duration=250,
        ventilation_duration=10,
        keepalive=3
    )
    await io.start()

if __name__ == "__main__":
    asyncio.run(main())