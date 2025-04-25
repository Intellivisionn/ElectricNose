import pygame
import os
import time
import socket
import threading
import math
import json

# Configuration
SOCKET_PORT = 9999
COUNTDOWN_DURATION = 30  # seconds before prediction
VENTILATE_DURATION = 30  # seconds to ventilate

# Colors
BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
YELLOW  = (255, 215,   0)
GREEN   = ( 34, 139,  34)

# Application States
STATE_COUNTDOWN = 'countdown'
STATE_WAIT      = 'wait_for_prediction'
STATE_SHOW      = 'show_prediction'
STATE_VENTILATE = 'ventilate'

class DisplayApp:
    def __init__(self):
        # Initialize state/timers
        self.state = STATE_COUNTDOWN
        self.countdown_start = time.time()
        self.ventilate_start = None
        self.prediction = None
        self.angle = 0
        # Threading
        self.lock = threading.Lock()
        self.socket_thread = threading.Thread(target=self._socket_server, daemon=True)

    def start(self):
        # Framebuffer setup for Raspberry Pi
        os.system('chvt 7')
        os.system('fbset -depth 32 && fbset -depth 16')

        # Initialize Pygame in fullscreen mode
        pygame.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
        h = self.screen.get_height()
        # Fonts based on screen height
        self.font_title = pygame.font.Font(None, int(h * 0.1))
        self.font_main  = pygame.font.Font(None, int(h * 0.2))
        self.font_small = pygame.font.Font(None, int(h * 0.05))
        # Start socket listener
        self.socket_thread.start()

    def _socket_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', SOCKET_PORT))
        s.listen(1)
        while True:
            client, _ = s.accept()
            data = client.recv(4096)
            client.close()
            try:
                payload = json.loads(data.decode())
            except Exception:
                continue
            with self.lock:
                # Expecting {'scent': str, 'confidence': float}
                self.prediction = payload
                # Move to show state immediately
                if self.state in (STATE_WAIT, STATE_COUNTDOWN):
                    self.state = STATE_SHOW
            time.sleep(0.1)

    def run(self):
        self.start()
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    # On any key during show state, move to ventilate
                    if self.state == STATE_SHOW:
                        self.state = STATE_VENTILATE
                        self.ventilate_start = time.time()
                elif event.type == pygame.QUIT:
                    running = False

            now = time.time()
            # State logic
            if self.state == STATE_COUNTDOWN:
                elapsed = now - self.countdown_start
                if elapsed >= COUNTDOWN_DURATION:
                    self.state = STATE_WAIT
                else:
                    self._draw_countdown(COUNTDOWN_DURATION - int(elapsed))

            elif self.state == STATE_WAIT:
                self._draw_wait()

            elif self.state == STATE_SHOW:
                with self.lock:
                    data = self.prediction
                self._draw_prediction(data)

            elif self.state == STATE_VENTILATE:
                elapsed = now - self.ventilate_start
                if elapsed >= VENTILATE_DURATION:
                    # Reset for next run
                    self.state = STATE_COUNTDOWN
                    self.countdown_start = time.time()
                    self.prediction = None
                else:
                    self._draw_ventilate(VENTILATE_DURATION - int(elapsed))

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def _draw_countdown(self, seconds_left):
        self.screen.fill(BLACK)
        text = f"Starting in {seconds_left}s"
        surface = self.font_main.render(text, True, WHITE)
        rect = surface.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(surface, rect)

    def _draw_wait(self):
        self.screen.fill(BLACK)
        surface = self.font_title.render("Waiting for prediction...", True, YELLOW)
        rect = surface.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(surface, rect)

    def _draw_prediction(self, data):
        self.screen.fill(BLACK)
        scent = data.get('scent', 'Unknown')
        conf = data.get('confidence', 0) * 100
        # Title
        title_surf = self.font_title.render("Prediction:", True, GREEN)
        title_rect = title_surf.get_rect(center=(self.screen.get_width()//2, int(self.screen.get_height()*0.2)))
        self.screen.blit(title_surf, title_rect)
        # Scent name
        scent_surf = self.font_main.render(scent, True, WHITE)
        scent_rect = scent_surf.get_rect(center=(self.screen.get_width()//2, int(self.screen.get_height()*0.5)))
        self.screen.blit(scent_surf, scent_rect)
        # Confidence
        conf_text = f"Confidence: {conf:.1f}%"
        conf_surf = self.font_small.render(conf_text, True, WHITE)
        conf_rect = conf_surf.get_rect(center=(self.screen.get_width()//2, int(self.screen.get_height()*0.75)))
        self.screen.blit(conf_surf, conf_rect)

    def _draw_ventilate(self, seconds_left):
        self.screen.fill(BLACK)
        # Text
        ventilate_surf = self.font_title.render("Let the box ventilate", True, YELLOW)
        ventilate_rect = ventilate_surf.get_rect(center=(self.screen.get_width()//2, int(self.screen.get_height()*0.2)))
        self.screen.blit(ventilate_surf, ventilate_rect)
        # Countdown
        count_surf = self.font_main.render(f"{seconds_left}s", True, WHITE)
        count_rect = count_surf.get_rect(center=(self.screen.get_width()//2, int(self.screen.get_height()*0.5)))
        self.screen.blit(count_surf, count_rect)
        # Simple rotating fan animation
        center = (self.screen.get_width()//2, int(self.screen.get_height()*0.85))
        radius = 40
        self.angle = (self.angle + 6) % 360
        for i in range(4):
            ang = math.radians(self.angle + i * 90)
            x = center[0] + radius * math.cos(ang)
            y = center[1] + radius * math.sin(ang)
            pygame.draw.line(self.screen, WHITE, center, (x, y), 6)

if __name__ == '__main__':
    app = DisplayApp()
    app.run()
