#!/usr/bin/env python3
"""
Create necessary directories and .gitkeep files for the project.
"""

import os

def create_directories():
    """Create necessary directories and .gitkeep files."""
    directories = [
        "uploads",
        "results",
        "temp",
        "static/js",
        "static/css",
        "services",
        "routers",
        "tests",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        gitkeep_file = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, "w") as f:
                f.write("# This file is used to keep the directory in git\n")
    
    print("Directories created successfully.")

if __name__ == "__main__":
    create_directories()
