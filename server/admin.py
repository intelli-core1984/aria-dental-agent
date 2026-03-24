#!/usr/bin/env python3
"""
ARIA Admin CLI — manage license keys and view usage.
Usage:
  python admin.py create  "Office Name" --email office@example.com --limit 500
  python admin.py usage
  python admin.py deactivate aria_live_xxxx
  python admin.py activate   aria_live_xxxx

Set ARIA_SERVER_URL and ARIA_ADMIN_KEY in your environment (or .env).
"""
import sys
import os
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

SERVER = os.environ.get("ARIA_SERVER_URL", "http://localhost:8000")
ADMIN_KEY = os.environ.get("ARIA_ADMIN_KEY", "")
HEADERS = {"x-admin-key": ADMIN_KEY}


def create(name: str, email: str, limit: int, key_type: str):
    r = requests.post(f"{SERVER}/admin/keys", headers=HEADERS, json={
        "name": name, "email": email, "plan_limit": limit, "key_type": key_type
    })
    r.raise_for_status()
    d = r.json()
    print(f"\n✅  License key created")
    print(f"   Name:  {d['name']}")
    print(f"   Limit: {d['plan_limit']} requests/month")
    print(f"\n   Key:   {d['license_key']}\n")
    print("   → Send this key to the customer. They paste it into ARIA on first launch.\n")


def usage():
    r = requests.get(f"{SERVER}/admin/usage", headers=HEADERS)
    r.raise_for_status()
    customers = r.json()["customers"]
    if not customers:
        print("No customers yet.")
        return
    print(f"\n{'NAME':<25} {'REQUESTS':>10} {'LIMIT':>8} {'TOKENS':>10} {'ACTIVE':>8}")
    print("─" * 70)
    for c in customers:
        active = "✅" if c["active"] else "❌"
        print(f"{c['name']:<25} {c['requests']:>10} {c['limit']:>8} {c['tokens']:>10} {active:>8}")
    print()


def set_active(key: str, active: bool):
    action = "activate" if active else "deactivate"
    r = requests.patch(f"{SERVER}/admin/keys/{key}/{action}", headers=HEADERS)
    r.raise_for_status()
    print(f"✅  Key {action}d: {key[:24]}...")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    c = sub.add_parser("create", help="Create a new license key")
    c.add_argument("name")
    c.add_argument("--email", default="")
    c.add_argument("--limit", type=int, default=500)
    c.add_argument("--type", dest="key_type", default="live", choices=["live", "test"])

    sub.add_parser("usage", help="View all customer usage")

    d = sub.add_parser("deactivate", help="Deactivate a license key")
    d.add_argument("key")

    a = sub.add_parser("activate", help="Re-activate a license key")
    a.add_argument("key")

    args = p.parse_args()
    if args.cmd == "create":
        create(args.name, args.email, args.limit, args.key_type)
    elif args.cmd == "usage":
        usage()
    elif args.cmd == "deactivate":
        set_active(args.key, False)
    elif args.cmd == "activate":
        set_active(args.key, True)
    else:
        p.print_help()
