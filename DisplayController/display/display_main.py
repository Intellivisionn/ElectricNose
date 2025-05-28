import asyncio
import sys
import os

# insert project root (one level up from DisplayController/source) onto PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DisplayController.display.display_controller import DisplayController

USE_HDMI = False
WS_URI   = "ws://localhost:8765"

async def main():
    conn = WebSocketConnection(WS_URI)
    controller = DisplayController("display", conn, use_hdmi=USE_HDMI)
    await controller.start()   # calls BaseDataClient.start(), which in turn runs run()

if __name__ == "__main__":
    asyncio.run(main())