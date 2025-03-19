import pygame
import json
import os
import time
import glob

# Path to sensor data JSON file
JSON_FILE = "/home/admin/ElectricNose-SensorReader/sensor_data.json"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (30, 144, 255)
GREEN = (34, 139, 34)
RED = (220, 20, 60)

# Function to check HDMI connection
def is_hdmi_connected():
    """Check if HDMI is connected using DRM sysfs."""
    hdmi_ports = glob.glob("/sys/class/drm/card*-HDMI-*/status")
    for port in hdmi_ports:
        with open(port, "r") as f:
            status = f.read().strip()
            if status == "connected":
                return True
    return False

# Function to load sensor data
def load_sensor_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return None
    return None

# Function to render centered text
def render_text_centered(text, font, color, y, screen):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(screen.get_width() // 2, y))
    screen.blit(text_surface, text_rect)

# Function to display sensor data
def draw_sensor_data(screen, sensor_data, fonts):
    screen.fill(BLACK)  # Clear screen

    if not sensor_data:
        render_text_centered("Error: No sensor data", fonts["title"], RED, screen.get_height() // 3, screen)
        pygame.display.flip()
        return

    if isinstance(sensor_data, list):
        sensor_data = sensor_data[0]  # Extract first object if it's a list
    elif not isinstance(sensor_data, dict):
        render_text_centered("Invalid JSON format!", fonts["title"], RED, screen.get_height() // 3, screen)
        pygame.display.flip()
        return

    # Title (Centered at top)
    render_text_centered("Electric Nose Sensor Data", fonts["title"], BLUE, int(screen.get_height() * 0.08), screen)

    y_offset = int(screen.get_height() * 0.18)  # Start drawing sensor data

    for sensor, readings in sensor_data.items():
        render_text_centered(sensor, fonts["data"], GREEN, y_offset, screen)
        y_offset += int(screen.get_height() * 0.05)  # Spacing between sensors

        for key, value in readings.items():
            text = f"{key}: {value}"
            render_text_centered(text, fonts["small"], WHITE, y_offset, screen)
            y_offset += int(screen.get_height() * 0.04)  # Adjusted dynamically

        y_offset += int(screen.get_height() * 0.02)  # Extra spacing between sensors

    pygame.display.flip()

# Function to initialize Pygame
def start_pygame():
    print("Initializing Pygame...")
    os.system("chvt 7")  # Ensure framebuffer console is active
    os.system("fbset -depth 32 && fbset -depth 16")  # Reset framebuffer depth

    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)

    # Dynamically scale font sizes
    fonts = {
        "title": pygame.font.Font(None, int(screen.get_height() * 0.06)),  # 6% of screen height
        "data": pygame.font.Font(None, int(screen.get_height() * 0.045)),  # 4.5% of screen height
        "small": pygame.font.Font(None, int(screen.get_height() * 0.035)), # 3.5% of screen height
    }

    return screen, fonts

# Main loop
running = True
display_active = False
screen = None
fonts = None

while running:
    hdmi_connected = is_hdmi_connected()

    if hdmi_connected and not display_active:
        print("HDMI connected, starting Pygame...")
        screen, fonts = start_pygame()
        display_active = True

    elif not hdmi_connected and display_active:
        print("HDMI disconnected, stopping Pygame...")
        pygame.quit()
        screen = None
        fonts = None
        display_active = False

    if display_active:
        sensor_data = load_sensor_data()
        draw_sensor_data(screen, sensor_data, fonts)

        # Handle events only when display is active
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

    time.sleep(5)  # Check HDMI status every 5 seconds

pygame.quit()