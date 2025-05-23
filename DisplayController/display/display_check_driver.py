import os
import pygame

print("SDL Library Path:", os.environ.get('LD_LIBRARY_PATH'))
print("Current SDL_VIDEODRIVER:", os.environ.get('SDL_VIDEODRIVER'))
print("FB Device exists:", os.path.exists('/dev/fb0'))
print("FB Device permissions:", os.popen('ls -l /dev/fb0').read().strip())

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
