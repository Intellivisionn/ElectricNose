### Setup
In order to get the Pygame running and Raspberry Pi display to work from a python venv, run these commands inside the virtual environment:
```
pip install -r requirements.txt
pip uninstall pygame
sudo apt-get install libsdl2-dev
pip install --no-binary :all: pygame
```