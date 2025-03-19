import pygame
import json
import os
import time
import glob

# Path to sensor data JSON file
JSON_FILE = "/home/admin/ElectricNose-SensorReader/sensor_data.json"

# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(False)

# Get screen dimensions dynamically
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h  # Dynamically detect screen size

# Dynamically scale font sizes based on screen resolution
font_title_size = int(HEIGHT * 0.06)  # ~6% of screen height
font_data_size = int(HEIGHT * 0.04)   # ~4% of screen height
font_small_size = int(HEIGHT * 0.03)  # ~3% of screen height

# Initialize fonts with scaled sizes
font_title = pygame.font.Font(None, font_title_size)
font_data = pygame.font.Font(None, font_data_size)
font_small = pygame.font.Font(None, font_small_size)

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

# Function to render text
def render_text(text, font, color, x, y, screen):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

# Function to display sensor data
def draw_sensor_data(screen, sensor_data):
    screen.fill(BLACK)  # Clear screen

    if not sensor_data:
        render_text("Error: No sensor data", font_title, RED, int(WIDTH * 0.05), int(HEIGHT * 0.3), screen)
        pygame.display.flip()
        return

    # Handle JSON structure (list vs dictionary)
    if isinstance(sensor_data, list):
        sensor_data = sensor_data[0]  # Extract first object if it's a list
    elif not isinstance(sensor_data, dict):
        render_text("Invalid JSON format!", font_title, RED, int(WIDTH * 0.05), int(HEIGHT * 0.3), screen)
        pygame.display.flip()
        return

    # Title
    render_text("Electric Nose Sensor Data", font_title, BLUE, int(WIDTH * 0.2), int(HEIGHT * 0.05), screen)

    y_offset = int(HEIGHT * 0.15)  # Adjusted dynamically for better fit

    for sensor, readings in sensor_data.items():
        render_text(sensor, font_data, GREEN, int(WIDTH * 0.05), y_offset, screen)
        y_offset += int(HEIGHT * 0.05)  # Adjusted dynamically

        for key, value in readings.items():
            render_text(f"{key}: {value}", font_small, WHITE, int(WIDTH * 0.07), y_offset, screen)
            y_offset += int(HEIGHT * 0.04)  # Adjusted dynamically

        y_offset += int(HEIGHT * 0.02)  # Extra spacing between sensors

    pygame.display.flip()

# Main loop
running = True
display_active = False  # Track whether the display is on

while running:
    hdmi_connected = is_hdmi_connected()

    if hdmi_connected and not display_active:
        print("HDMI connected, starting pygame display.")
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        display_active = True

    elif not hdmi_connected and display_active:
        print("HDMI disconnected, stopping pygame display.")
        pygame.quit()
        display_active = False

    if display_active:
        sensor_data = load_sensor_data()
        draw_sensor_data(screen, sensor_data)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    time.sleep(1)  # Refresh every 5 seconds

pygame.quit()