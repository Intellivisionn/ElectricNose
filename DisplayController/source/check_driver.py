import os
import pygame

drivers = [
    "fbcon",
    "rpi",
    "directfb",
    "kmsdrm",
    "drm",
    "x11",
    "wayland",
    "dummy"
]

print("Probing SDL video drivers…")
for drv in drivers:
    os.environ["SDL_VIDEODRIVER"] = drv
    try:
        # re‐init the display subsystem fresh each time
        pygame.display.quit()
        pygame.display.init()
        print(f"✅  {drv}")
        pygame.display.quit()
    except pygame.error:
        print(f"❌  {drv}")
