"""
ARIA Proxy — database layer
SQLite for now; swap to Postgres/Supabase later with zero code changes.
"""
import sqlite3
import secrets
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "aria.db"


class Database:
    def __init__(self, path: str = None):
        self.path = path or str(DB_PATH)
        self._init()

    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS customers (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key     TEXT    UNIQUE NOT NULL,
                    name            TEXT    NOT NULL,
                    email           TEXT,
                    active          INTEGER DEFAULT 1,
                    plan_limit      INTEGER DEFAULT 500,
                    created_at      REAL    NOT NULL,
                    requests_month  INTEGER DEFAULT 0,
                    tokens_month    INTEGER DEFAULT 0,
                    last_reset      REAL    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS request_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT  NOT NULL,
                    tokens      INTEGER NOT NULL,
                    ts          REAL    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS registrations (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    email           TEXT    NOT NULL,
                    license_key     TEXT    UNIQUE NOT NULL,
                    ip_address      TEXT,
                    user_agent      TEXT,
                    install_date    REAL    NOT NULL,
                    status          TEXT    NOT NULL DEFAULT 'pending',
                    approved_at     REAL,
                    trial_requests  INTEGER DEFAULT 0,
                    trial_limit     INTEGER DEFAULT 10,
                    notes           TEXT
                );
            """)

    # ── Registration management ───────────────────────────────────

    def register(self, email: str, license_key: str,
                 ip_address: str = "", user_agent: str = "") -> dict:
        """Create a new pending registration. Returns the created row."""
        now = time.time()
        with self._conn() as c:
            c.execute(
                "INSERT INTO registrations "
                "(email, license_key, ip_address, user_agent, install_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (email, license_key, ip_address, user_agent, now)
            )
        return self.get_registration(license_key)

    def get_registration(self, license_key: str) -> dict | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM registrations WHERE license_key = ?",
                (license_key,)
            ).fetchone()
        return dict(row) if row else None

    def get_pending(self) -> list:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM registrations WHERE status = 'pending' "
                "ORDER BY install_date ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_registrations(self) -> list:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM registrations "
                "ORDER BY CASE status "
                "  WHEN 'pending'  THEN 0 "
                "  WHEN 'approved' THEN 1 "
                "  ELSE 2 END, install_date DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def approve(self, license_key: str, plan_limit: int = 500) -> bool:
        """Approve a registration and create the customers row. Idempotent."""
        reg = self.get_registration(license_key)
        if not reg:
            return False
        now = time.time()
        with self._conn() as c:
            c.execute(
                "UPDATE registrations SET status='approved', approved_at=? "
                "WHERE license_key=?",
                (now, license_key)
            )
            c.execute(
                "INSERT OR IGNORE INTO customers "
                "(license_key, name, email, plan_limit, created_at, last_reset) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (license_key, reg["email"], reg["email"], plan_limit, now, now)
            )
            # Make sure the customer is active (handles re-approval after reject)
            c.execute(
                "UPDATE customers SET active=1 WHERE license_key=?",
                (license_key,)
            )
        return True

    def reject(self, license_key: str, notes: str = "") -> bool:
        """Reject a registration and deactivate any customer row."""
        if not self.get_registration(license_key):
            return False
        with self._conn() as c:
            c.execute(
                "UPDATE registrations SET status='rejected', notes=? "
                "WHERE license_key=?",
                (notes, license_key)
            )
            c.execute(
                "UPDATE customers SET active=0 WHERE license_key=?",
                (license_key,)
            )
        return True

    def increment_trial(self, license_key: str) -> int:
        """Increment trial_requests counter. Returns new count."""
        with self._conn() as c:
            c.execute(
                "UPDATE registrations SET trial_requests = trial_requests + 1 "
                "WHERE license_key = ?",
                (license_key,)
            )
        reg = self.get_registration(license_key)
        return reg["trial_requests"] if reg else 0

    # ── License key management ────────────────────────────────────

    def create_key(self, name: str, email: str = "", plan_limit: int = 500,
                   key_type: str = "live") -> str:
        """Create a pre-approved customer key (admin-issued, bypasses trial)."""
        key = f"aria_{key_type}_{secrets.token_urlsafe(20)}"
        now = time.time()
        with self._conn() as c:
            c.execute(
                "INSERT INTO customers (license_key, name, email, plan_limit, created_at, last_reset) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (key, name, email, plan_limit, now, now)
            )
        return key

    def get_customer(self, license_key: str) -> dict | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM customers WHERE license_key = ?", (license_key,)
            ).fetchone()
        return dict(row) if row else None

    def set_active(self, license_key: str, active: bool):
        with self._conn() as c:
            c.execute("UPDATE customers SET active = ? WHERE license_key = ?",
                      (1 if active else 0, license_key))

    # ── Usage tracking ────────────────────────────────────────────

    def log_request(self, license_key: str, tokens: int):
        now = time.time()
        customer = self.get_customer(license_key)
        if customer:
            last_month = time.gmtime(customer["last_reset"]).tm_mon
            now_month  = time.gmtime(now).tm_mon
            if now_month != last_month:
                with self._conn() as c:
                    c.execute(
                        "UPDATE customers SET requests_month=0, tokens_month=0, "
                        "last_reset=? WHERE license_key=?",
                        (now, license_key)
                    )
        with self._conn() as c:
            c.execute(
                "UPDATE customers SET requests_month = requests_month + 1, "
                "tokens_month = tokens_month + ? WHERE license_key = ?",
                (tokens, license_key)
            )
            c.execute(
                "INSERT INTO request_log (license_key, tokens, ts) VALUES (?, ?, ?)",
                (license_key, tokens, now)
            )

    def get_all_usage(self) -> list:
        with self._conn() as c:
            rows = c.execute(
                "SELECT name, email, license_key, requests_month, tokens_month, plan_limit, active "
                "FROM customers ORDER BY requests_month DESC"
            ).fetchall()
        return [
            {
                "name":     r["name"],
                "email":    r["email"],
                "key":      r["license_key"][:24] + "...",
                "requests": r["requests_month"],
                "tokens":   r["tokens_month"],
                "limit":    r["plan_limit"],
                "active":   bool(r["active"]),
            }
            for r in rows
        ]
