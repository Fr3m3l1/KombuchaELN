"""
Kombucha ELN - A NiceGUI interface for elabFTW
"""

import sys
import os

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import ui

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Kombucha ELN', port=8085, storage_secret='kombucha_eln_secret_key')
