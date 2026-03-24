"""
ARIA — Automated Reception Intelligence Assistant
Entry point: system tray icon + global hotkey listener
"""

import threading
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard
import sys
import os

from paths import get_config_path
from setup_dialog import run_setup_if_needed
from popup import PopupWindow
from scheduler import BackgroundScheduler

# ── Global state ─────────────────────────────────────────────────
popup_window = None
popup_lock = threading.Lock()

# ── Tray icon ────────────────────────────────────────────────────
def make_tray_icon():
    """Draw a simple green circle as the tray icon."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=(0, 180, 120, 255))
    draw.text((20, 18), "A", fill="white")
    return img

def toggle_popup(icon=None, item=None):
    global popup_window
    with popup_lock:
        if popup_window is None or not popup_window.winfo_exists():
            popup_window = PopupWindow(on_close=lambda: None)
            popup_window.mainloop()
        else:
            popup_window.toggle_visibility()

def quit_app(icon, item):
    icon.stop()
    sys.exit(0)

# ── Hotkey listener ──────────────────────────────────────────────
def on_hotkey():
    threading.Thread(target=toggle_popup, daemon=True).start()

def start_hotkey_listener():
    # Cmd+Shift+A (Mac) or Ctrl+Shift+A (Windows/Linux)
    modifier = keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse("<cmd>+<shift>+a") if sys.platform == "darwin"
        else keyboard.HotKey.parse("<ctrl>+<shift>+a"),
        on_hotkey
    )
    with keyboard.Listener(
        on_press=hotkey.press,
        on_release=hotkey.release
    ) as listener:
        listener.join()

# ── Main ─────────────────────────────────────────────────────────
def main():
    # First-run setup: show API key dialog if not configured
    if not run_setup_if_needed():
        sys.exit(0)

    # Load config from persistent location
    from dotenv import load_dotenv
    load_dotenv(get_config_path())

    # Start background scheduler
    bg = BackgroundScheduler()
    bg.start()

    # Start hotkey listener in background thread
    threading.Thread(target=start_hotkey_listener, daemon=True).start()

    # Build tray menu
    menu = pystray.Menu(
        pystray.MenuItem("Open ARIA", toggle_popup, default=True),
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon(
        "ARIA",
        make_tray_icon(),
        "ARIA — Dental Assistant",
        menu
    )
    icon.run()

if __name__ == "__main__":
    main()
