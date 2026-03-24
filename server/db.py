"""
ARIA Proxy — database layer
SQLite for now; swap to Postgres/Supabase later with zero code changes.
"""
import sqlite3
import secrets
import time
import calendar
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
            """)

    # ── License key management ────────────────────────────────────

    def create_key(self, name: str, email: str = "", plan_limit: int = 500,
                   key_type: str = "live") -> str:
        """Create a new customer + license key. Returns the key."""
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
        """Increment usage counters and write to log."""
        now = time.time()
        # Auto-reset counters at start of new calendar month
        customer = self.get_customer(license_key)
        last = customer["last_reset"]
        last_month = time.gmtime(last).tm_mon
        now_month  = time.gmtime(now).tm_mon
        if now_month != last_month:
            with self._conn() as c:
                c.execute(
                    "UPDATE customers SET requests_month=0, tokens_month=0, last_reset=? WHERE license_key=?",
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
