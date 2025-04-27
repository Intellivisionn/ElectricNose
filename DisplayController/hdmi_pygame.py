import pygame
import json
import os
import time
import socket
import threading
import glob

# Constants
SOCKET_PORT = 9999
OVERRIDE_TIMEOUT = 10  # seconds before falling back

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (30, 144, 255)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)


class HDMIStatusChecker:
    @staticmethod
    def is_connected():
        hdmi_ports = glob.glob("/sys/class/drm/card*-HDMI-*/status")
        for port in hdmi_ports:
            with open(port, "r") as f:
                status = f.read().strip()
                if status == "connected":
                    return True
        return False


class DisplayManager:
    def __init__(self):
        self.screen = None
        self.fonts = {}
        self.override_data = None
        self.override_last_update = 0
        self.lock = threading.Lock()
        self.socket_thread = threading.Thread(target=self._start_socket_server, daemon=True)

    def start(self):
        print("Initializing Pygame...")
        os.system("chvt 7")
        os.system("fbset -depth 32 && fbset -depth 16")

        pygame.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)

        screen_height = self.screen.get_height()

        self.fonts = {
            "title": pygame.font.Font(None, int(screen_height * 0.06)),
            "data": pygame.font.Font(None, int(screen_height * 0.045)),
            "small": pygame.font.Font(None, int(screen_height * 0.035)),
        }

        self.socket_thread.start()

    def stop(self):
        pygame.quit()
        self.screen = None
        self.fonts = {}

    def _start_socket_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("localhost", SOCKET_PORT))
        server.listen(1)
        print(f"Listening for display data on port {SOCKET_PORT}...")

        while True:
            client, _ = server.accept()
            data = client.recv(4096)
            try:
                incoming = json.loads(data.decode())
                with self.lock:
                    self.override_data = incoming
                    self.override_last_update = time.time()
                    self._draw_custom_display(self.override_data)
                    print("Display updated.")
            except Exception as e:
                print(f"Invalid data received: {e}")
            finally:
                client.close()

    def _render_text_centered(self, text, font, color, y):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, y))
        self.screen.blit(text_surface, text_rect)

    def _draw_custom_display(self, payload):
        self.screen.fill(BLACK)
        title = payload.get("title", "Invalid Payload")
        self._render_text_centered(title, self.fonts["title"], YELLOW, int(self.screen.get_height() * 0.1))

        y_offset = int(self.screen.get_height() * 0.25)
        lines = payload.get("lines", [])

        for line in lines:
            text = line.get("text", "")
            color = tuple(line.get("color", WHITE))
            self._render_text_centered(text, self.fonts["data"], color, y_offset)
            y_offset += int(self.screen.get_height() * 0.05)

        pygame.display.flip()

    def _draw_fallback_display(self):
        self.screen.fill(BLACK)
        self._render_text_centered("Display Controller Not Initialised", self.fonts["title"], YELLOW, self.screen.get_height() // 2)
        pygame.display.flip()

    def draw(self):
        with self.lock:
            if self.override_data and time.time() - self.override_last_update <= OVERRIDE_TIMEOUT:
                self._draw_custom_display(self.override_data)
            else:
                self._draw_fallback_display()


class DisplayApp:
    def __init__(self):
        self.running = True
        self.display_active = False
        self.display = DisplayManager()

    def run(self):
        while self.running:
            hdmi_connected = HDMIStatusChecker.is_connected()

            if hdmi_connected and not self.display_active:
                print("HDMI connected, starting display...")
                self.display.start()
                self.display_active = True

            elif not hdmi_connected and self.display_active:
                print("HDMI disconnected, stopping display...")
                self.display.stop()
                self.display_active = False

            if self.display_active:
                # Only draw fallback periodically; socket triggers redraws when active
                self.display.draw()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        self.running = False
            else:
                print("No display detected. Waiting for HDMI...")
                time.sleep(5)
                continue

            time.sleep(0.2)

        pygame.quit()


if __name__ == "__main__":
    app = DisplayApp()
    app.run()