import asyncio
import sys, os
# insert project root (one level up from DisplayController/source) onto PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DisplayController.io.io_handler import IOHandler
from DisplayController.io.io_input_handler import ButtonHandler

BUTTON_PINS = {
    "start":     17,
    "ventilate": 22,
    "cancel":    23,
    "halt":      27,
}

async def main():
    conn = WebSocketConnection("ws://localhost:8765")
    buttons = ButtonHandler(BUTTON_PINS)
    io = IOHandler(
        name="io",
        connection=conn,
        button_input=buttons,
        use_hdmi=False,
        loading_duration=250,
        ventilation_duration=300,
        keepalive=5
    )
    await io.start()

if __name__ == "__main__":
    asyncio.run(main())