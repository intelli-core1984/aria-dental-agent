"""
ARIA — First-run setup dialog.
Shown when no API key is found. No terminal required.
"""
import customtkinter as ctk
from paths import get_config_path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG      = "#0f1419"
SURFACE = "#161d26"
ACCENT  = "#00e5a0"
TEXT    = "#e8edf2"
MUTED   = "#5a7a8a"


class SetupDialog(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.result = None
        self._build_ui()

    def _build_ui(self):
        self.title("ARIA — First Time Setup")
        self.geometry("420x320")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 420) // 2
        y = (sh - 320) // 2
        self.geometry(f"+{x}+{y}")

        # Header
        ctk.CTkLabel(
            self, text="⬡  ARIA", fg_color=SURFACE,
            font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            text_color=ACCENT, height=52, corner_radius=0
        ).pack(fill="x")

        ctk.CTkLabel(
            self, text="Dental Office AI Assistant",
            font=ctk.CTkFont(size=11), text_color=MUTED
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            self,
            text="Enter your ARIA license key to get started.\n"
                 "Contact support@intelli-network.com if you need one.",
            font=ctk.CTkFont(size=10), text_color=MUTED,
            justify="center"
        ).pack(pady=(0, 16))

        # License key entry
        self.key_entry = ctk.CTkEntry(
            self, placeholder_text="aria_live_...",
            fg_color="#1d2733", border_color="#263545",
            text_color=TEXT, placeholder_text_color=MUTED,
            font=ctk.CTkFont(family="Courier", size=11),
            height=38, width=340, show="*"
        )
        self.key_entry.pack(pady=(0, 6))

        # Toggle show/hide
        self.show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Show key", variable=self.show_var,
            text_color=MUTED, font=ctk.CTkFont(size=10),
            fg_color=ACCENT, hover_color="#00ffb3",
            command=self._toggle_show
        ).pack(pady=(0, 20))

        # Save button
        ctk.CTkButton(
            self, text="Save & Launch ARIA",
            fg_color=ACCENT, hover_color="#00ffb3",
            text_color="#000000",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40, width=200,
            command=self._save
        ).pack()

        self.status_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=10), text_color="#e05050"
        )
        self.status_lbl.pack(pady=(8, 0))

    def _toggle_show(self):
        self.key_entry.configure(show="" if self.show_var.get() else "*")

    def _save(self):
        key = self.key_entry.get().strip()
        if not key.startswith("aria_"):
            self.status_lbl.configure(text="⚠  Key should start with aria_live_ or aria_test_")
            return
        config_path = get_config_path()
        config_path.write_text(f"ARIA_LICENSE_KEY={key}\n")
        self.result = key
        self.destroy()

    def run(self) -> bool:
        """Returns True if setup completed, False if user closed the window."""
        self.mainloop()
        return self.result is not None


def run_setup_if_needed() -> bool:
    """Show setup dialog if no license key is configured. Returns True if ready."""
    from dotenv import dotenv_values
    config_path = get_config_path()
    if config_path.exists():
        vals = dotenv_values(config_path)
        if vals.get("ARIA_LICENSE_KEY", "").startswith("aria_"):
            return True
    dialog = SetupDialog()
    return dialog.run()
