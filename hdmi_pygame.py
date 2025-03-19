import pygame
import json
import os
import time

# Path to the sensor data JSON file
JSON_FILE = "/home/admin/ElectricNose-SensorReader/sensor_data.json"

# Pygame Initialization
pygame.init()
pygame.mouse.set_visible(False)
WIDTH, HEIGHT = 800, 480  # Match your screen size
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Electric Nose Sensor Data")

# Load Fonts
font_title = pygame.font.Font(None, 40)
font_data = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 22)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (30, 144, 255)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
GRAY = (169, 169, 169)

# Function to Load Sensor Data
def load_sensor_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return None
    return None

# Function to Render Text
def render_text(text, font, color, x, y):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

# Function to Draw Sensor Data on Screen
def draw_sensor_data(sensor_data):
    screen.fill(BLACK)  # Clear screen with black background

    if not sensor_data:
        render_text("Error: No sensor data available", font_title, RED, 50, 200)
        pygame.display.flip()
        return

    if isinstance(sensor_data, list):
        sensor_data = sensor_data[0]  # Extract the first element if it's a list
    elif isinstance(sensor_data, dict):
        pass  # It's already a dictionary, so we don't need to do anything
    else:
        sensor_data = {}  # Fallback for unexpected cases


    # Title
    render_text("Electric Nose Sensor Data", font_title, BLUE, 180, 20)

    y_offset = 80  # Start drawing sensor data below the title

    for sensor, readings in sensor_data.items():
        render_text(sensor, font_data, GREEN, 50, y_offset)
        y_offset += 40

        for key, value in readings.items():
            render_text(f"{key}: {value}", font_small, WHITE, 80, y_offset)
            y_offset += 25

        y_offset += 10  # Extra spacing between sensors

    pygame.display.flip()

# Main Loop
running = True
while running:
    sensor_data = load_sensor_data()
    draw_sensor_data(sensor_data)

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    time.sleep(5)  # Refresh every 5 seconds

pygame.quit()
