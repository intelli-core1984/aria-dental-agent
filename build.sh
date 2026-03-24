#!/bin/bash
# ARIA — Build script
# Packages the agent into a single installable app

set -e

echo "▶ Building ARIA Dental Agent..."

# Install deps
pip install -r requirements.txt

# Build with PyInstaller
pyinstaller \
  --onefile \
  --windowed \
  --name "ARIA" \
  --add-data "skills:skills" \
  --hidden-import "pystray._darwin" \
  --hidden-import "PIL._tkinter_finder" \
  main.py

echo ""
echo "✅ Build complete."
echo "   Mac:     dist/ARIA.app"
echo "   Windows: dist/ARIA.exe"
echo ""
echo "Copy the dist/ output to the dental office computer and double-click to install."
