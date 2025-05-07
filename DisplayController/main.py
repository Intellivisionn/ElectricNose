import pygame
import json
import os
import time
import socket
import threading
import glob

# ======= CONFIGURATION ========
USE_HDMI = False  # Set to True to use HDMI detection, False for always-on PiTFT
SOCKET_PORT = 9999
OVERRIDE_TIMEOUT = 10  # seconds

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
        self.socket_thread = threading.Thread(target=self._start_socket_server, daemon=True)

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
        text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, y))
        self.screen.blit(text_surface, text_rect)

    def _draw_custom_display(self, payload):
        self.screen.fill(BLACK)

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        title = payload.get("title", "Invalid Payload")
        lines = payload.get("lines", [])

        # === Step 1: Try largest acceptable font first ===
        max_font_size = 48
        min_font_size = 16
        spacing_ratio = 1.4  # vertical spacing multiplier

        # Prepare text content including wrapped lines
        def wrap_text(text, font):
            wrapped = []
            words = text.split()
            current_line = ""

            for word in words:
                test_line = f"{current_line} {word}".strip()
                width, _ = font.size(test_line)
                if width > screen_width - 40:  # margin padding
                    if current_line:
                        wrapped.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                wrapped.append(current_line)
            return wrapped

        # === Step 2: Determine fitting font size ===
        final_font_size = max_font_size
        wrapped_lines = []

        while final_font_size >= min_font_size:
            content_font = pygame.font.Font(None, final_font_size)
            title_font = pygame.font.Font(None, int(final_font_size * 1.3))

            all_lines = wrap_text(title, title_font)
            for line in lines:
                wrapped_lines += wrap_text(line.get("text", ""), content_font)

            total_height = int(final_font_size * spacing_ratio) * (len(all_lines) + 1)
            if total_height < screen_height - 20:  # add top/bottom margin
                break  # font size fits

            # Too tall — try smaller font
            final_font_size -= 2
            wrapped_lines = []

        # === Step 3: Render title + wrapped content ===
        y_offset = 20
        title_lines = wrap_text(title, title_font)
        for line in title_lines:
            self._render_text_centered(line, title_font, YELLOW, y_offset)
            y_offset += int(final_font_size * spacing_ratio)

        for line in lines:
            color = tuple(line.get("color", WHITE))
            for subline in wrap_text(line.get("text", ""), content_font):
                self._render_text_centered(subline, content_font, color, y_offset)
                y_offset += int(final_font_size * spacing_ratio)

        pygame.display.flip()


    def _draw_fallback_display(self):
        self.screen.fill(BLACK)

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        text = "Display Controller Not Initialised"

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

        # Final rendering
        font = pygame.font.Font(None, font_size)
        self._render_text_centered(text, font, YELLOW, screen_height // 2)
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
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
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