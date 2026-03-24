"""
ARIA — First-run setup / registration dialog.
Collects email + optional pre-issued key, registers with the proxy server,
saves the license key locally. No Anthropic key ever touches this machine.
"""
import os
import customtkinter as ctk
from paths import get_config_path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG      = "#0f1419"
SURFACE = "#161d26"
ACCENT  = "#00e5a0"
TEXT    = "#e8edf2"
MUTED   = "#5a7a8a"
WARN    = "#f0a500"
ERR     = "#e05050"

SERVER_URL = os.getenv("ARIA_SERVER_URL", "https://aria-proxy.railway.app")


class SetupDialog(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.result = None
        self._build_ui()

    def _build_ui(self):
        self.title("ARIA — Setup")
        self.geometry("420x460")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-420)//2}+{(sh-460)//2}")

        # Header
        ctk.CTkLabel(
            self, text="⬡  ARIA", fg_color=SURFACE,
            font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            text_color=ACCENT, height=52, corner_radius=0
        ).pack(fill="x")

        ctk.CTkLabel(
            self, text="Dental Office AI Assistant",
            font=ctk.CTkFont(size=11), text_color=MUTED
        ).pack(pady=(14, 2))

        ctk.CTkLabel(
            self,
            text="Enter your email to register.\n"
                 "Paste a license key if you have one, or leave it blank\n"
                 "for a free 10-message trial.",
            font=ctk.CTkFont(size=10), text_color=MUTED, justify="center"
        ).pack(pady=(0, 18))

        # Email
        ctk.CTkLabel(self, text="Email address",
                     font=ctk.CTkFont(size=10), text_color=MUTED,
                     anchor="w").pack(padx=40, fill="x")
        self.email_entry = ctk.CTkEntry(
            self, placeholder_text="office@example.com",
            fg_color="#1d2733", border_color="#263545",
            text_color=TEXT, placeholder_text_color=MUTED,
            font=ctk.CTkFont(family="Courier", size=11),
            height=36, width=340
        )
        self.email_entry.pack(pady=(4, 14))

        # License key (optional)
        ctk.CTkLabel(self, text="License key  (optional — leave blank for trial)",
                     font=ctk.CTkFont(size=10), text_color=MUTED,
                     anchor="w").pack(padx=40, fill="x")
        self.key_entry = ctk.CTkEntry(
            self, placeholder_text="aria_live_...  or  aria_trial_...",
            fg_color="#1d2733", border_color="#263545",
            text_color=TEXT, placeholder_text_color=MUTED,
            font=ctk.CTkFont(family="Courier", size=11),
            height=36, width=340, show="*"
        )
        self.key_entry.pack(pady=(4, 4))

        self.show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Show key", variable=self.show_var,
            text_color=MUTED, font=ctk.CTkFont(size=10),
            fg_color=ACCENT, hover_color="#00ffb3",
            command=lambda: self.key_entry.configure(
                show="" if self.show_var.get() else "*")
        ).pack(pady=(0, 18))

        # Register button
        self.btn = ctk.CTkButton(
            self, text="Register & Launch ARIA",
            fg_color=ACCENT, hover_color="#00ffb3",
            text_color="#000000",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40, width=220,
            command=self._register
        )
        self.btn.pack()

        # Status label
        self.status_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=10),
            text_color=ERR, wraplength=340, justify="center"
        )
        self.status_lbl.pack(pady=(10, 0))

    # ── Registration ─────────────────────────────────────────────

    def _register(self):
        import requests as req
        from dotenv import dotenv_values

        email = self.email_entry.get().strip()
        key   = self.key_entry.get().strip()

        if not email or "@" not in email:
            self.status_lbl.configure(
                text="Please enter a valid email address.", text_color=ERR)
            return
        if key and not key.startswith("aria_"):
            self.status_lbl.configure(
                text="Key must start with aria_live_ or aria_trial_", text_color=ERR)
            return

        self.btn.configure(state="disabled")
        self.status_lbl.configure(text="Connecting to ARIA server...", text_color=MUTED)
        self.update()

        server = os.getenv("ARIA_SERVER_URL", SERVER_URL)

        try:
            resp = req.post(
                f"{server}/register",
                json={"email": email, "license_key": key or None},
                timeout=15
            )
            data = resp.json()
        except Exception as e:
            self.status_lbl.configure(
                text=f"Cannot reach server: {e}", text_color=ERR)
            self.btn.configure(state="normal")
            return

        if resp.status_code not in (200, 201):
            self.status_lbl.configure(
                text=data.get("detail", "Registration failed."), text_color=ERR)
            self.btn.configure(state="normal")
            return

        # Save to .env
        received_key = data["license_key"]
        config_path  = get_config_path()
        existing     = dict(dotenv_values(config_path)) if config_path.exists() else {}
        existing["ARIA_LICENSE_KEY"] = received_key
        existing["ARIA_EMAIL"]       = email
        existing["ARIA_SERVER_URL"]  = server
        config_path.write_text(
            "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n"
        )

        status          = data.get("status", "pending")
        trial_remaining = data.get("trial_remaining")

        if status == "approved":
            self.status_lbl.configure(
                text="Approved! Launching ARIA...", text_color=ACCENT)
        else:
            msg = (f"Registered! You have {trial_remaining} trial messages.\n"
                   "Admin approval is pending — you'll get full access once approved.")
            self.status_lbl.configure(text=msg, text_color=WARN)

        self.result = received_key
        self.after(1800, self.destroy)

    def run(self) -> bool:
        self.mainloop()
        return self.result is not None


def run_setup_if_needed() -> bool:
    """Show setup dialog if not yet registered. Returns True if ready to launch."""
    from dotenv import dotenv_values
    config_path = get_config_path()
    if config_path.exists():
        vals = dotenv_values(config_path)
        if vals.get("ARIA_LICENSE_KEY", "").startswith("aria_"):
            return True
    dialog = SetupDialog()
    return dialog.run()
