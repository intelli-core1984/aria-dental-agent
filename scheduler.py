"""
ARIA — Background task scheduler
Runs daily data pulls from Dentrix + weekly CEO brief generation
"""

import schedule
import time
import threading
import json
from pathlib import Path
from dentrix import DentrixReader
from storage import Storage


class BackgroundScheduler:
    def __init__(self):
        self.reader  = DentrixReader()
        self.storage = Storage()

    def daily_pull(self):
        """8am daily: pull schedule + production from Dentrix."""
        print("[ARIA] Running daily Dentrix pull...")
        appt = self.reader.read_appointment_book()
        prod = self.reader.read_production_summary()
        self.storage.save("appointment_book", appt)
        self.storage.save("production_summary", prod)
        print("[ARIA] Daily pull complete.")

    def weekly_brief(self):
        """Monday 8am: generate weekly CEO brief (Skill 001)."""
        print("[ARIA] Generating weekly CEO brief...")
        # Trigger agent to run Skill 001 and save output
        from agent import Agent
        agent = Agent()
        brief = agent.ask(
            "Generate the full weekly CEO brief using Skill 001 — "
            "Schedule Intelligence Reader. Use all available data."
        )
        output_path = Path(__file__).parent / "data" / "weekly_brief_latest.md"
        output_path.write_text(brief)
        print(f"[ARIA] Weekly brief saved to {output_path}")

    def start(self):
        """Start the background scheduler in a daemon thread."""
        schedule.every().day.at("08:00").do(self.daily_pull)
        schedule.every().monday.at("08:00").do(self.weekly_brief)

        def run():
            while True:
                schedule.run_pending()
                time.sleep(30)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        print("[ARIA] Background scheduler started.")
