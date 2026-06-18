#!/bin/bash
# Install script for News Post Generator Desktop App

echo "========================================"
echo "News Post Generator - Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python from https://www.python.org"
    exit 1
fi

echo "Installing dependencies..."
pip3 install -r requirements-desktop.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Create a .env file with your API keys:"
echo "   NEWS_API_KEY=your_key_here"
echo "   GEMINI_API_KEY=your_key_here"
echo ""
echo "2. Run the app:"
echo "   python3 desktop_app.py"
echo ""
