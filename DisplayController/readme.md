# Setting up KMSDRM for Pygame in Virtual Environment

## 1. Install System Dependencies
`sudo apt-get update`
`sudo apt-get install -y libsdl2-dev libdrm-dev mesa-common-dev`

## 2. Create and Activate Virtual Environment
`python3 -m venv myenv`
`source myenv/bin/activate`

## 3. Install Pygame with Required Build
`pip uninstall pygame`
`pip install --no-binary :all: pygame`

## 4. Add User to Required Groups
`sudo usermod -a -G video,input $USER`

## 5. Enable KMS in /boot/firmware/config.txt
Add these lines to /boot/firmware/config.txt:

dtoverlay=vc4-kms-v3d
gpu_mem=128

## 6. Reboot System
`sudo reboot`

## 7. After Reboot
`source myenv/bin/activate`

## 8. Test KMSDRM
Create a test file (test_kms.py):

import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
pygame.display.init()
print("KMSDRM initialized successfully")
pygame.display.quit()

Run the test:
`python test_kms.py`