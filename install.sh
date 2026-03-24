#!/bin/bash
# ═══════════════════════════════════════════════
#  ARIA Dental Agent — 1-Click Installer (Mac)
# ═══════════════════════════════════════════════
set -e

REPO="https://github.com/intelli-core1984/aria-dental-agent"
INSTALL_DIR="$HOME/aria-dental-agent"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   ARIA Dental Agent — Installer      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Check Python 3 ────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌  Python 3 not found."
  echo "    Install it from https://www.python.org/downloads/ then re-run this script."
  exit 1
fi
PY_VER=$(python3 -c 'import sys; print(sys.version_info.major, sys.version_info.minor)')
PY_MAJOR=$(echo $PY_VER | cut -d' ' -f1)
PY_MINOR=$(echo $PY_VER | cut -d' ' -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "❌  Python 3.10+ required (found 3.$PY_MINOR). Please upgrade."
  exit 1
fi
echo "✅  Python $(python3 --version) found"

# ── 2. Install Homebrew (if missing) ─────────
if ! command -v brew &>/dev/null; then
  echo "▶  Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
echo "✅  Homebrew ready"

# ── 3. Install Tesseract (OCR engine) ────────
if ! command -v tesseract &>/dev/null; then
  echo "▶  Installing Tesseract OCR..."
  brew install tesseract
fi
echo "✅  Tesseract $(tesseract --version 2>&1 | head -1) ready"

# ── 4. Clone or update repo ──────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "▶  Updating existing install..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "▶  Downloading ARIA..."
  git clone "$REPO" "$INSTALL_DIR"
fi
echo "✅  Files ready at $INSTALL_DIR"

# ── 5. Install Python dependencies ───────────
echo "▶  Installing Python packages..."
cd "$INSTALL_DIR"
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r requirements.txt
echo "✅  Dependencies installed"

# ── 6. Set up .env with API key ──────────────
if [ ! -f "$INSTALL_DIR/.env" ]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  You need an Anthropic API key."
  echo "  Get one free at: https://console.anthropic.com"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  read -p "  Paste your API key here: " API_KEY
  echo "ANTHROPIC_API_KEY=$API_KEY" > "$INSTALL_DIR/.env"
  echo "✅  API key saved to .env"
else
  echo "✅  .env already exists — skipping API key step"
fi

# ── 7. Grant accessibility permissions notice ─
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  IMPORTANT — Mac Permission Required"
echo ""
echo "  ARIA uses a global hotkey (Cmd+Shift+A)."
echo "  macOS will ask to grant Accessibility access"
echo "  the first time it runs."
echo ""
echo "  When prompted:"
echo "  System Settings → Privacy & Security"
echo "    → Accessibility → add Terminal (or ARIA)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 8. Create launcher shortcut ──────────────
LAUNCHER="$HOME/Desktop/Launch ARIA.command"
cat > "$LAUNCHER" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 main.py
EOF
chmod +x "$LAUNCHER"
echo "✅  Launcher created on Desktop: 'Launch ARIA.command'"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   ✅  ARIA is ready to launch!       ║"
echo "║                                      ║"
echo "║   Double-click 'Launch ARIA.command' ║"
echo "║   on your Desktop — or run:          ║"
echo "║   cd ~/aria-dental-agent             ║"
echo "║   python3 main.py                    ║"
echo "║                                      ║"
echo "║   Hotkey: Cmd+Shift+A               ║"
echo "╚══════════════════════════════════════╝"
echo ""
