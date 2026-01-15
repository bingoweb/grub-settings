#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# Ensure the current directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grub_settings_pkg.main import main

if __name__ == "__main__":
    main()
