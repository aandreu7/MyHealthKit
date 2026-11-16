#!/usr/bin/env python3
"""Create/migrate the inventory without inserting fictitious medicines."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server.storage import Inventory

if __name__ == '__main__':
    inventory = Inventory()
    inventory.initialize()
    print('Inventory initialized:', inventory.path)
