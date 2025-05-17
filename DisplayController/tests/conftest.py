import os
import sys
import pytest

# 1) project root, so we can import display.display_controller, io.io_handler, etc.
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# 2) also add the 'display' and 'io' subfolders so that their internal imports (e.g. `from display_impl import ...`)
#    resolve correctly
display_dir = os.path.join(root, 'display')
io_dir      = os.path.join(root, 'io')

for p in (root, display_dir, io_dir):
    if p not in sys.path:
        sys.path.insert(0, p)
