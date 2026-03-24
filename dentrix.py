"""
ARIA — Dentrix screen reader
No API needed. Screenshots the active Dentrix window and OCR-reads it.
"""

import pyautogui
import pytesseract
import subprocess
import sys
import time
from PIL import Image
from pathlib import Path
from paths import get_resource_dir, get_data_dir

SCREENSHOT_DIR = get_data_dir() / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Point pytesseract at the bundled binary when frozen
if getattr(sys, 'frozen', False):
    import os
    _tess = get_resource_dir() / "tesseract" / "tesseract.exe"
    if _tess.exists():
        pytesseract.pytesseract.tesseract_cmd = str(_tess)

# Dentrix window title fragments to look for
DENTRIX_TITLES = ["Dentrix", "DENTRIX", "Office Manager", "Appointment Book"]


class DentrixReader:

    def is_running(self) -> bool:
        """Check if Dentrix is open."""
        if sys.platform == "darwin":
            result = subprocess.run(
                ["pgrep", "-f", "Dentrix"], capture_output=True, text=True
            )
            return result.returncode == 0
        elif sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Dentrix*"],
                capture_output=True, text=True
            )
            return "Dentrix" in result.stdout
        return False

    def focus_dentrix(self) -> bool:
        """Bring Dentrix window to front."""
        if sys.platform == "darwin":
            subprocess.run(
                ["osascript", "-e",
                 'tell application "Dentrix" to activate'],
                capture_output=True
            )
            time.sleep(0.8)
            return True
        elif sys.platform == "win32":
            import ctypes
            # Windows: find and focus the window
            # Implementation depends on Dentrix version
            pass
        return False

    def screenshot(self, label: str = "capture") -> Path:
        """Take a full screenshot and save it."""
        ts = int(time.time())
        path = SCREENSHOT_DIR / f"{label}_{ts}.png"
        img = pyautogui.screenshot()
        img.save(path)
        return path

    def ocr(self, image_path: Path) -> str:
        """Extract all text from a screenshot."""
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, config="--psm 6")
        return text.strip()

    def read_appointment_book(self) -> dict:
        """
        Navigate to the Dentrix Appointment Book, screenshot, and OCR it.
        Returns raw text + metadata.
        """
        if not self.is_running():
            return {"error": "Dentrix is not running", "text": ""}

        self.focus_dentrix()
        time.sleep(1.0)

        # Screenshot the current screen (assumes Appointment Book is visible)
        path = self.screenshot("appointment_book")
        text = self.ocr(path)

        return {
            "screen": "appointment_book",
            "raw_text": text,
            "screenshot": str(path),
            "timestamp": time.time()
        }

    def read_production_summary(self) -> dict:
        """
        Navigate to Office Manager → Practice Production Summary.
        Dentrix menu path: Office Manager → Reports → Management → Practice Production Summary
        """
        if not self.is_running():
            return {"error": "Dentrix is not running", "text": ""}

        self.focus_dentrix()
        time.sleep(0.8)

        # TODO: automate menu navigation once we know the exact Dentrix version
        # For now: screenshot whatever is visible
        path = self.screenshot("production_summary")
        text = self.ocr(path)

        return {
            "screen": "production_summary",
            "raw_text": text,
            "screenshot": str(path),
            "timestamp": time.time()
        }

    def read_patient_list(self) -> dict:
        """Read patient list / recall screen."""
        if not self.is_running():
            return {"error": "Dentrix is not running", "text": ""}

        self.focus_dentrix()
        time.sleep(0.8)

        path = self.screenshot("patient_list")
        text = self.ocr(path)

        return {
            "screen": "patient_list",
            "raw_text": text,
            "screenshot": str(path),
            "timestamp": time.time()
        }
