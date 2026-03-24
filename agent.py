"""
ARIA — Claude API integration + Skill loader
Loads SKILL.md files at runtime — no recompile needed to update behaviours
"""

import os
import json
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from storage import Storage
from paths import get_resource_dir, get_config_path

load_dotenv(get_config_path())

SKILLS_DIR = get_resource_dir() / "skills"


class Agent:
    def __init__(self):
        self.client  = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.storage = Storage()
        self.skills  = self._load_skills()
        self.history = []   # conversation memory (session only)

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
        # Load latest captured data
        latest = self.storage.get_latest()
        data_context = json.dumps(latest, indent=2) if latest else "No data captured yet."

        # Load skill 001
        skill_001 = self.skills.get("schedule-intelligence-reader", "")

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
        self.history.append({"role": "user", "content": question})

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                system=self._build_system_prompt(),
                messages=self.history
            )
            answer = response.content[0].text
            self.history.append({"role": "assistant", "content": answer})

            # Keep history to last 10 exchanges
            if len(self.history) > 20:
                self.history = self.history[-20:]

            return answer

        except Exception as e:
            return f"Error: {str(e)}"

    # ── Clear history ────────────────────────────────────────────
    def reset(self):
        self.history = []
