"""
ARIA — Agent layer
Routes all requests through the ARIA proxy server using a license key.
The Anthropic API key never lives on the customer's machine.
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from storage import Storage
from paths import get_resource_dir, get_config_path

load_dotenv(get_config_path())

SKILLS_DIR  = get_resource_dir() / "skills"
SERVER_URL  = os.getenv("ARIA_SERVER_URL", "https://aria-proxy.railway.app")
LICENSE_KEY = os.getenv("ARIA_LICENSE_KEY", "")


class Agent:
    def __init__(self):
        self.server      = SERVER_URL.rstrip("/")
        self.license_key = LICENSE_KEY
        self.storage     = Storage()
        self.skills      = self._load_skills()
        self.history     = []

    # ── Skill loader ─────────────────────────────────────────────
    def _load_skills(self) -> dict:
        skills = {}
        if not SKILLS_DIR.exists():
            return skills
        for skill_dir in SKILLS_DIR.iterdir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skills[skill_dir.name] = skill_file.read_text()
        return skills

    # ── System prompt ────────────────────────────────────────────
    def _build_system_prompt(self) -> str:
        latest       = self.storage.get_latest()
        data_context = json.dumps(latest, indent=2) if latest else "No data captured yet."
        skill_001    = self.skills.get("schedule-intelligence-reader", "")

        return f"""You are ARIA, the AI office assistant for Image Dental in Calgary.
You run on the front desk computer and help staff answer questions about
the schedule, production, patients, and KPIs.

RULES:
- Be concise. This is a small popup — 2-4 sentences max unless a list is needed.
- Always prioritize schedule health (chair coverage) over financial metrics.
- If you don't have the data to answer, say so clearly and say what data is needed.
- Never make up numbers. Only use data from the context below.
- Speak like a knowledgeable colleague, not a report generator.

ACTIVE SKILL:
{skill_001}

LATEST CAPTURED DATA:
{data_context}
"""

    # ── Ask ──────────────────────────────────────────────────────
    def ask(self, question: str) -> str:
        if not self.license_key:
            return "No license key configured. Please re-run setup."

        self.history.append({"role": "user", "content": question})

        try:
            resp = requests.post(
                f"{self.server}/ask",
                headers={"x-license-key": self.license_key},
                json={
                    "messages":   self.history,
                    "system":     self._build_system_prompt(),
                    "max_tokens": 512,
                },
                timeout=30,
            )

            # Pass server error messages through verbatim — they are user-friendly
            if resp.status_code in (401, 403, 429):
                try:
                    detail = resp.json().get("detail", "")
                except Exception:
                    detail = ""
                return detail or "Access denied. Contact support@intelli-network.com"

            resp.raise_for_status()

            data   = resp.json()
            answer = data.get("answer", "")
            status = data.get("status")
            trial  = data.get("trial_remaining")

            self.history.append({"role": "assistant", "content": answer})
            if len(self.history) > 20:
                self.history = self.history[-20:]

            # Append trial notice when account is pending approval
            if status == "pending" and trial is not None:
                plural = "s" if trial != 1 else ""
                answer += (f"\n\n[Trial: {trial} message{plural} remaining — "
                           "pending admin approval]")

            return answer

        except requests.exceptions.ConnectionError:
            return "Cannot reach ARIA server. Check your internet connection."
        except Exception as e:
            return f"Error: {str(e)}"

    # ── Reset ────────────────────────────────────────────────────
    def reset(self):
        self.history = []
