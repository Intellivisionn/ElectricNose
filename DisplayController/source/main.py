import pygame
import json
import os
import time
import socket
import threading
import glob
import subprocess

# ======= CONFIGURATION ========
USE_HDMI = False             # Set to True to use HDMI detection, False for always-on PiTFT
USE_SENSOR_CHECK = True      # Set to False to disable the “sensor” service health check
SOCKET_PORT = 9999
OVERRIDE_TIMEOUT = 10        # seconds

# ======= COLORS ===============
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
        self.override_data = None
        self.override_last_update = 0
        self.lock = threading.Lock()
        self.socket_thread = threading.Thread(
            target=self._start_socket_server,
            daemon=True
        )

    def start(self):
        print("Starting display...")

        os.system("chvt 7")
        os.system("fbset -depth 32 && fbset -depth 16")

        if not USE_HDMI:
            os.environ["SDL_FBDEV"] = "/dev/fb0"

        pygame.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)

        self.socket_thread.start()

    def stop(self):
        pygame.quit()
        self.screen = None

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
        text_rect = text_surface.get_rect(
            center=(self.screen.get_width() // 2, y)
        )
        self.screen.blit(text_surface, text_rect)

    def _draw_custom_display(self, payload):
        self.screen.fill(BLACK)

        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()

        title = payload.get("title", "Invalid Payload")
        lines = payload.get("lines", [])

        # 1) Figure out best font size (unchanged)
        max_fs, min_fs = 48, 16
        spacing = 1.4

        def wrap_text(text, font):
            wrp, cur = [], ""
            for w in text.split():
                test = (cur + " " + w).strip()
                if font.size(test)[0] > screen_w - 40:
                    if cur: wrp.append(cur)
                    cur = w
                else:
                    cur = test
            if cur: wrp.append(cur)
            return wrp

        fs = max_fs
        while fs >= min_fs:
            cf = pygame.font.Font(None, fs)
            tf = pygame.font.Font(None, int(fs * 1.3))

            ttl_wr = wrap_text(title, tf)
            cnt_wr = []
            for ln in lines:
                cnt_wr += wrap_text(ln.get("text", ""), cf)

            if (len(ttl_wr) + len(cnt_wr)) * int(fs * spacing) < screen_h - 20:
                break
            fs -= 2

        # 2) Build render queue
        content_font = pygame.font.Font(None, fs)
        title_font   = pygame.font.Font(None, int(fs * 1.3))

        render_queue = []
        for t in wrap_text(title, title_font):
            render_queue.append((t, title_font, YELLOW))
        for ln in lines:
            col = tuple(ln.get("color", WHITE))
            for sub in wrap_text(ln.get("text", ""), content_font):
                render_queue.append((sub, content_font, col))

        # 3) Compute total block height
        total_h = sum(f.get_linesize() for _, f, _ in render_queue)

        # 4) Draw each line, starting at ( (screen_h - total_h)//2 )
        y = (screen_h - total_h) // 2
        x = screen_w // 2

        for txt, fnt, clr in render_queue:
            surf = fnt.render(txt, True, clr)
            rect = surf.get_rect(midtop=(x, y))
            self.screen.blit(surf, rect)
            y += fnt.get_linesize()

        pygame.display.flip()

    def _draw_fallback_display(self):
        self.screen.fill(BLACK)

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Health-check text logic
        if USE_SENSOR_CHECK:
            try:
                status = subprocess.check_output(
                    ["systemctl", "is-active", "sensor"],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
            except Exception:
                status = "inactive"

            if status != "active":
                text = "Sensors Service is offline"
            else:
                text = "Display Client is offline"
        else:
            text = "Display Client is offline"

        # Dynamically choose font size to fit horizontally and vertically
        max_font_size = 48
        min_font_size = 16
        spacing_ratio = 1.2

        font_size = max_font_size
        while font_size >= min_font_size:
            font = pygame.font.Font(None, font_size)
            text_width, text_height = font.size(text)
            if text_width < screen_width - 40 and text_height < screen_height - 40:
                break
            font_size -= 2

        font = pygame.font.Font(None, font_size)
        self._render_text_centered(text, font, YELLOW, screen_height // 2)
        pygame.display.flip()

    def draw(self):
        with self.lock:
            if (
                self.override_data
                and time.time() - self.override_last_update <= OVERRIDE_TIMEOUT
            ):
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
            if USE_HDMI:
                hdmi_connected = HDMIStatusChecker.is_connected()
            else:
                hdmi_connected = True  # Assume PiTFT always available

            if hdmi_connected and not self.display_active:
                print("Display connected, starting...")
                self.display.start()
                self.display_active = True
            elif not hdmi_connected and self.display_active:
                print("Display disconnected, stopping...")
                self.display.stop()
                self.display_active = False

            if self.display_active:
                self.display.draw()
                for event in pygame.event.get():
                    if (
                        event.type == pygame.QUIT
                        or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)
                    ):
                        self.running = False
            else:
                print("No display detected. Waiting...")
                time.sleep(5)
                continue

            time.sleep(0.2)

        pygame.quit()


if __name__ == "__main__":
    app = DisplayApp()
    app.run()