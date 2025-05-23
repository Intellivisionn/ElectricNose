import os
import sys

import glob
import subprocess
import time
import pygame
from abc import ABC, abstractmethod

# allow importing DisplayController.aspects
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))
from DisplayController.aspects.aop_decorators import log_call

class IDisplay(ABC):
    @abstractmethod
    def start(self): ...
    @abstractmethod
    def stop(self): ...
    @abstractmethod
    def draw(self, data: dict | None): ...
    @abstractmethod
    def check_connection(self) -> bool:  # ← new
        """
        Returns True if this display is currently present/usable.
        """
        pass

class HDMIStatusChecker:
    @staticmethod
    def is_connected() -> bool:
        ports = glob.glob("/sys/class/drm/card*-HDMI-*/status")
        for p in ports:
            try:
                if open(p).read().strip() == "connected":
                    return True
            except OSError:
                continue
        return False

class SensorServiceMonitor:
    def is_sensor_active(self) -> bool:
        try:
            st = subprocess.check_output(
                ["systemctl", "is-active", "sensor"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            st = "inactive"
        return st == "active"

class BasePygameDisplay(IDisplay):
    def __init__(self):
        self.screen = None
        self._monitor = SensorServiceMonitor()

    @log_call
    def start(self):
        # 1) silence ALSA
        os.environ["SDL_AUDIODRIVER"] = "dummy"

        # 2) switch to console 7 and set framebuffer depth
        print("Starting display...")
        try:
            os.system("chvt 7")
            os.system("fbset -depth 32 && fbset -depth 16")
        except Exception:
            pass

        # 3) Try KMS/DRM first for ILI9341
        pygame.display.quit()
        drivers_to_try = [
            {
                "driver": "kmsdrm",
                "env": {
                    "SDL_VIDEODRIVER": "kmsdrm",
                    "SDL_KMSDRM_DEVICE_INDEX": "1"
                }
            },
            {
                "driver": "fbcon",
                "env": {
                    "SDL_VIDEODRIVER": "fbcon",
                    "SDL_FBDEV": "/dev/fb0"
                }
            },
            {
                "driver": "directfb",
                "env": {
                    "SDL_VIDEODRIVER": "directfb"
                }
            },
            {
                "driver": "x11",
                "env": {
                    "SDL_VIDEODRIVER": "x11"
                }
            }
        ]

        for driver in drivers_to_try:
            # Clear previous environment variables
            for key in ["SDL_VIDEODRIVER", "SDL_KMSDRM_DEVICE_INDEX", "SDL_FBDEV"]:
                os.environ.pop(key, None)
            
            # Set new environment variables
            for key, value in driver["env"].items():
                os.environ[key] = value

            try:
                pygame.display.init()
                print(f"Successfully initialized {driver['driver']}")
                break
            except pygame.error as e:
                print(f"Failed to initialize {driver['driver']}: {e}")
        else:
            raise RuntimeError("No SDL video driver initialized successfully")

        # 4) now finish pygame init and open fullscreen
        pygame.init()                # init remaining modules (after display)
        pygame.mouse.set_visible(False)
        
        # Get the current display info
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            width, height = info.current_w, info.current_h
        else:
            width, height = 320, 240  # Default for ILI9341
            
        try:
            self.screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        except pygame.error:
            # Fallback to windowed mode if fullscreen fails
            self.screen = pygame.display.set_mode((width, height))

    @log_call
    def stop(self):
        pygame.quit()
        self.screen = None

    def draw(self, data: dict | None):
        if data:
            self._draw_custom(data)
        else:
            self._draw_fallback()

    def _wrap_text(self, text, font, maxw):
        wrp, cur = [], ""
        for w in text.split():
            test = (cur + " " + w).strip()
            if font.size(test)[0] > maxw - 40:
                if cur:
                    wrp.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            wrp.append(cur)
        return wrp

    def _render_center(self, surf, y):
        rect = surf.get_rect(center=(self.screen.get_width() // 2, y))
        self.screen.blit(surf, rect)

    @log_call
    def _draw_custom(self, payload):
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        YELLOW = (255, 215, 0)
        self.screen.fill(BLACK)

        sw, sh = self.screen.get_size()
        title = payload.get("title", "Invalid Payload")
        lines = payload.get("lines", [])

        max_fs, min_fs = 48, 16
        spacing = 1.4
        fs = max_fs
        while fs >= min_fs:
            cf = pygame.font.Font(None, fs)
            tf = pygame.font.Font(None, int(fs * 1.3))

            ttl_wr = self._wrap_text(title, tf, sw)
            cnt_wr = []
            for ln in lines:
                cnt_wr += self._wrap_text(ln.get("text", ""), cf, sw)

            if (len(ttl_wr) + len(cnt_wr)) * int(fs * spacing) < sh - 20:
                break
            fs -= 2

        content_font = pygame.font.Font(None, fs)
        title_font   = pygame.font.Font(None, int(fs * 1.3))

        render_queue = []
        for t in self._wrap_text(title, title_font, sw):
            render_queue.append((t, title_font, YELLOW))
        for ln in lines:
            col = tuple(ln.get("color", WHITE))
            for sub in self._wrap_text(ln.get("text", ""), content_font, sw):
                render_queue.append((sub, content_font, col))

        total_h = sum(f.get_linesize() for _, f, _ in render_queue)
        y = (sh - total_h) // 2
        x = sw // 2

        for txt, fnt, clr in render_queue:
            surf = fnt.render(txt, True, clr)
            rect = surf.get_rect(midtop=(x, y))
            self.screen.blit(surf, rect)
            y += fnt.get_linesize()

        pygame.display.flip()

    @log_call
    def _draw_fallback(self):
        BLACK = (0, 0, 0)
        YELLOW = (255, 215, 0)
        self.screen.fill(BLACK)

        sw, sh = self.screen.get_size()
        if not self._monitor.is_sensor_active():
            text = "Sensors Service is offline"
        else:
            text = "IOHandler is offline"

        max_fs, min_fs = 48, 16
        fs = max_fs
        while fs >= min_fs:
            font = pygame.font.Font(None, fs)
            tw, th = font.size(text)
            if tw < sw - 40 and th < sh - 40:
                break
            fs -= 2

        font = pygame.font.Font(None, fs)
        surf = font.render(text, True, YELLOW)
        self._render_center(surf, sh // 2)
        pygame.display.flip()

    @log_call
    def check_connection(self) -> bool:
        # If Pygame display is initialized and the window object exists,
        # assume the framebuffer is live.
        return bool(self.screen and pygame.display.get_init())


class PiTFTDisplay(BasePygameDisplay):
    def __init__(self):
        super().__init__()
        self.fb_device = "/dev/fb0"

    @log_call
    def start(self):
        os.environ["SDL_FBDEV"] = self.fb_device
        super().start()
    
    @log_call
    def check_connection(self) -> bool:
        # Also ensure the framebuffer device still exists on disk
        return os.path.exists(self.fb_device) and super().check_connection()

class HDMIDisplay(BasePygameDisplay):
    @log_call
    def start(self):
        super().start()

    @log_call
    def check_connection(self) -> bool:
        # Use HDMIStatusChecker to see if the cable is still plugged in
        return HDMIStatusChecker.is_connected() and super().check_connection()