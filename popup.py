"""
ARIA — Floating chat popup window
320x480px · dark theme · always-on-top · draggable
"""

import customtkinter as ctk
import threading
from agent import Agent

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

POPUP_W = 320
POPUP_H = 480
BG      = "#0f1419"
SURFACE = "#161d26"
ACCENT  = "#00e5a0"
MUTED   = "#5a7a8a"
TEXT    = "#e8edf2"


class PopupWindow(ctk.CTk):
    def __init__(self, on_close):
        super().__init__()
        self.on_close = on_close
        self.agent = Agent()
        self._drag_x = 0
        self._drag_y = 0

        self._setup_window()
        self._build_ui()

    # ── Window setup ─────────────────────────────────────────────
    def _setup_window(self):
        self.title("")
        self.geometry(f"{POPUP_W}x{POPUP_H}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.overrideredirect(True)          # borderless
        self.configure(fg_color=BG)

        # Position: bottom-right corner
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw - POPUP_W - 24
        y = sh - POPUP_H - 60
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.hide)

    # ── UI ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Title bar (draggable)
        self.title_bar = ctk.CTkFrame(self, fg_color=SURFACE, height=38, corner_radius=0)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.bind("<ButtonPress-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._do_drag)

        name_lbl = ctk.CTkLabel(
            self.title_bar, text="⬡  ARIA  ·  Image Dental",
            font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
            text_color=ACCENT
        )
        name_lbl.pack(side="left", padx=12, pady=8)
        name_lbl.bind("<ButtonPress-1>", self._start_drag)
        name_lbl.bind("<B1-Motion>", self._do_drag)

        close_btn = ctk.CTkButton(
            self.title_bar, text="✕", width=28, height=22,
            fg_color="transparent", hover_color="#2a2a3a",
            text_color=MUTED, font=ctk.CTkFont(size=11),
            command=self.hide
        )
        close_btn.pack(side="right", padx=6)

        # Chat history
        self.chat_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG, corner_radius=0
        )
        self.chat_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Welcome message
        self._add_message("ARIA", "Hi. Ask me anything about the schedule, production, or patients.", is_aria=True)

        # Input bar
        input_bar = ctk.CTkFrame(self, fg_color=SURFACE, height=52, corner_radius=0)
        input_bar.pack(fill="x", side="bottom")
        input_bar.pack_propagate(False)

        self.input_box = ctk.CTkEntry(
            input_bar,
            placeholder_text="Ask a question...",
            fg_color="#1d2733",
            border_color="#263545",
            text_color=TEXT,
            placeholder_text_color=MUTED,
            font=ctk.CTkFont(family="Courier", size=11),
            corner_radius=4,
            height=34
        )
        self.input_box.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=9)
        self.input_box.bind("<Return>", self._on_send)

        send_btn = ctk.CTkButton(
            input_bar, text="→", width=34, height=34,
            fg_color=ACCENT, hover_color="#00ffb3",
            text_color="#000000",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=4,
            command=self._on_send
        )
        send_btn.pack(side="right", padx=(0, 10), pady=9)

    # ── Drag ─────────────────────────────────────────────────────
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ── Chat ─────────────────────────────────────────────────────
    def _add_message(self, sender, text, is_aria=False):
        color = ACCENT if is_aria else TEXT
        sender_lbl = ctk.CTkLabel(
            self.chat_frame,
            text=sender,
            font=ctk.CTkFont(family="Courier", size=9, weight="bold"),
            text_color=color,
            anchor="w"
        )
        sender_lbl.pack(fill="x", padx=14, pady=(10, 2))

        bubble = ctk.CTkLabel(
            self.chat_frame,
            text=text,
            font=ctk.CTkFont(family="Courier", size=10),
            text_color=TEXT if is_aria else MUTED,
            anchor="w",
            justify="left",
            wraplength=270,
            fg_color=SURFACE if is_aria else "transparent",
            corner_radius=6
        )
        bubble.pack(fill="x", padx=12, pady=(0, 4), ipadx=8, ipady=6)

        # Scroll to bottom
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def _on_send(self, event=None):
        question = self.input_box.get().strip()
        if not question:
            return
        self.input_box.delete(0, "end")
        self._add_message("You", question, is_aria=False)
        self._add_message("ARIA", "thinking...", is_aria=True)

        def ask():
            response = self.agent.ask(question)
            # Remove "thinking..." and replace with real answer
            self.after(0, lambda: self._replace_last_aria(response))

        threading.Thread(target=ask, daemon=True).start()

    def _replace_last_aria(self, text):
        # Remove last widget (the "thinking..." bubble and its label)
        children = self.chat_frame.winfo_children()
        if len(children) >= 2:
            children[-1].destroy()
            children[-2].destroy()
        self._add_message("ARIA", text, is_aria=True)

    # ── Show / Hide ──────────────────────────────────────────────
    def toggle_visibility(self):
        if self.winfo_viewable():
            self.hide()
        else:
            self.show()

    def hide(self):
        self.withdraw()

    def show(self):
        self.deiconify()
        self.lift()
        self.input_box.focus()
