#!/bin/bash
#
# Tiger Compiler Web UI Launcher
#
# This script launches the Tiger Compiler web interface, which provides
# a browser-based frontend for compiling and analyzing Tiger programs.
#
# Features:
# - Interactive code editor with syntax highlighting
# - Real-time compilation and error reporting
# - Visualization of compilation phases
# - Example Tiger programs
#
# Usage:
#     ./run.sh
#
# The web interface will be available at http://localhost:5000
#
# Requirements:
# - Python 3 with Flask and required dependencies
# - Tiger compiler modules in parent directory
# - Optional: Virtual environment in ../venv
#
# Author: Tiger Compiler Team

# Activate virtual environment if it exists
# This ensures consistent dependencies and avoids conflicts
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
else
    echo "No virtual environment found, using system Python..."
fi

# Run the Flask application
# The web server will start on localhost:5000 by default
echo "Starting Tiger Compiler Web UI..."
echo "Open your browser to http://localhost:5000"
python app.py 