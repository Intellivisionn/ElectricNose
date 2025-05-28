import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DisplayController.display.display_controller import DisplayController
from DataCommunicator.source.WebSocketConnection import WebSocketConnection

class NullDisplay:
    def start(self):
        print("[NullDisplay] start")

    def stop(self):
        print("[NullDisplay] stop")

    def draw(self, data):
        print(f"[NullDisplay] draw payload: {data}")

    def check_connection(self):
        return True
    
class PatchedDisplayController(DisplayController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display = NullDisplay()

    async def _loop(self):
        """Skip all fallback logic and just draw using mock display"""
        while True:
            self.draw()
            await asyncio.sleep(self.draw_interval)

async def main():
    uri = os.environ.get("BROKER_URI", "ws://localhost:8765")
    print(f"[MockDisplay] Connecting to {uri}")
    conn = WebSocketConnection(uri)

    controller = PatchedDisplayController("display", conn, use_hdmi=False)

    try:
        await controller.start()
    except Exception as e:
        print(f"[MockDisplay] Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())