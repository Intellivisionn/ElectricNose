# display_test.py
import os
import pygame
import sys

# Debug info
print("Python:", sys.version)
print("Pygame:", pygame.version.ver)
print("SDL:", pygame.get_sdl_version())

# Set environment for ILI9341
os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
os.environ['SDL_KMSDRM_DEVICE_INDEX'] = '1'  # Use card1 for ILI9341

try:
    pygame.display.init()
    print("Display initialized")
    screen = pygame.display.set_mode((320, 240))
    print("Screen created")
    screen.fill((255, 0, 0))  # Red
    pygame.display.flip()
    pygame.time.wait(2000)
except Exception as e:
    print("Error:", e)
finally:
    pygame.quit()