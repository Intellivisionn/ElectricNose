# =============================================================================
#   1. Waits for user to insert a scent and press the select button
#   2. Shows a 5-second loading countdown.
#   3. Loads a prediction JSON from disk and displays:
#        • Scent name
#        • Confidence percentage
#   4. On a second button press, starts a 5-minute ventilation timer
#        showing a MM:SS countdown.
#   5. After ventilation, resets to the initial prompt for the next cycle.
#
# Pygame handles the display; GPIO input reads the physical button.
# Exiting via Ctrl+C (or ESC/closing the window) cleans up and quits.
# =============================================================================
import pygame
import os
import time
import json

# Configuration
LOADING_DURATION = 5    # seconds loading before reading prediction
VENTILATE_DURATION = 300  # seconds to ventilate (5 minutes)
MODEL_PATH = '/home/admin/ElectronicNose-ModelTraining/prediction.json'

# Colors
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
YELLOW  = (255, 215, 0)
GREEN   = (34, 139, 34)

# Application States
STATE_WAIT_BUTTON = 'wait_for_button'
STATE_LOADING     = 'loading'
STATE_SHOW        = 'show_prediction'
STATE_VENTILATE   = 'ventilate'

class DisplayApp:
    def __init__(self):
        # Initialize state/timers
        self.state = STATE_WAIT_BUTTON
        self.loading_start = None
        self.ventilate_start = None
        self.prediction = None

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

    def run(self):
        self.start()
        clock = pygame.time.Clock()
        running = True
        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:  # PiTFT "Select" button
                            if self.state == STATE_WAIT_BUTTON:
                                self.state = STATE_LOADING
                                self.loading_start = time.time()
                            elif self.state == STATE_SHOW:
                                self.state = STATE_VENTILATE
                                self.ventilate_start = time.time()
                        elif event.key == pygame.K_ESCAPE:
                            running = False

                now = time.time()

                if self.state == STATE_WAIT_BUTTON:
                    self._draw_message("Put in a scent and press SELECT")

                elif self.state == STATE_LOADING:
                    elapsed = now - self.loading_start
                    if elapsed >= LOADING_DURATION:
                        # Load prediction file
                        try:
                            with open(MODEL_PATH) as f:
                                self.prediction = json.load(f)
                        except Exception:
                            self.prediction = {'scent': 'Error', 'confidence': 0}
                        self.state = STATE_SHOW
                    else:
                        left = int(LOADING_DURATION - elapsed)
                        self._draw_message(f"Loading... {left}s")

                elif self.state == STATE_SHOW:
                    self._draw_prediction(self.prediction)

                elif self.state == STATE_VENTILATE:
                    elapsed = now - self.ventilate_start
                    if elapsed >= VENTILATE_DURATION:
                        # Reset for next run
                        self.state = STATE_WAIT_BUTTON
                        self.prediction = None
                    else:
                        left = int(VENTILATE_DURATION - elapsed)
                        mins = left // 60
                        secs = left % 60
                        self._draw_message(f"Ventilating... {mins}:{secs:02d}")

                pygame.display.flip()
                clock.tick(30)
        except KeyboardInterrupt:
            # Allow exit on Ctrl+C
            pass
        finally:
            pygame.quit()

    def _draw_message(self, text):
        self.screen.fill(BLACK)
        surf = self.font_main.render(text, True, WHITE)
        rect = surf.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(surf, rect)

    def _draw_prediction(self, data):
        self.screen.fill(BLACK)
        scent = data.get('scent', 'Unknown')
        conf = data.get('confidence', 0) * 100
        # Title
        title_surf = self.font_title.render("Prediction:", True, GREEN)
        title_rect = title_surf.get_rect(center=(
            self.screen.get_width()//2, int(self.screen.get_height()*0.2)
        ))
        self.screen.blit(title_surf, title_rect)
        # Scent name
        scent_surf = self.font_main.render(scent, True, WHITE)
        scent_rect = scent_surf.get_rect(center=(
            self.screen.get_width()//2, int(self.screen.get_height()*0.5)
        ))
        self.screen.blit(scent_surf, scent_rect)
        # Confidence
        conf_text = f"Confidence: {conf:.1f}%"
        conf_surf = self.font_small.render(conf_text, True, WHITE)
        conf_rect = conf_surf.get_rect(center=(
            self.screen.get_width()//2, int(self.screen.get_height()*0.75)
        ))
        self.screen.blit(conf_surf, conf_rect)

if __name__ == '__main__':
    app = DisplayApp()
    app.run()
