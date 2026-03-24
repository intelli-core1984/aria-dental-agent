"""
ARIA Proxy Server
FastAPI app — sits between every ARIA install and Anthropic.
Your Anthropic key never leaves this server.
"""
import os
import json
import secrets
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv
from db import Database
from dashboard import DASHBOARD_HTML

load_dotenv()

app = FastAPI(title="ARIA Proxy", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
db = Database()


# ── Request models ────────────────────────────────────────────────

class AskRequest(BaseModel):
    messages:   list
    system:     Optional[str] = None
    model:      str = "claude-sonnet-4-6"
    max_tokens: int = 512


class RegisterRequest(BaseModel):
    email:       str
    license_key: Optional[str] = None   # None → auto-generate trial key


class AdminActionRequest(BaseModel):
    license_key: str
    notes:       Optional[str] = ""
    plan_limit:  int = 500


# ── Helpers ───────────────────────────────────────────────────────

def _check_admin(key: str):
    if not key or key != os.environ.get("ADMIN_KEY", ""):
        raise HTTPException(403, "Invalid admin key")


def _call_anthropic(body: AskRequest) -> tuple[str, int]:
    """Call Anthropic and return (answer_text, total_tokens)."""
    response = _anthropic.messages.create(
        model=body.model,
        max_tokens=body.max_tokens,
        system=body.system or "You are ARIA, a helpful dental office assistant.",
        messages=body.messages
    )
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return response.content[0].text, tokens


# ── Health ────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ── Registration ─────────────────────────────────────────────────

@app.post("/register")
async def register(body: RegisterRequest, request: Request,
                   user_agent: str = Header(default="")):
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Valid email address required")

    # Validate or generate key
    if body.license_key:
        key = body.license_key.strip()
        if not key.startswith("aria_"):
            raise HTTPException(400, "Key must start with aria_live_ or aria_trial_")
    else:
        key = f"aria_trial_{secrets.token_urlsafe(16)}"

    ip = request.client.host if request.client else "unknown"

    # Return existing registration if already registered
    existing = db.get_registration(key)
    if existing:
        trial_remaining = max(0, existing["trial_limit"] - existing["trial_requests"])
        return {
            "status":          existing["status"],
            "license_key":     key,
            "trial_remaining": trial_remaining if existing["status"] == "pending" else None,
        }

    try:
        reg = db.register(email=email, license_key=key,
                          ip_address=ip, user_agent=user_agent)
    except Exception:
        raise HTTPException(409, "This key is already registered to a different email")

    return {
        "status":          "pending",
        "license_key":     key,
        "trial_remaining": reg["trial_limit"],
    }


# ── Main ask endpoint ─────────────────────────────────────────────

@app.post("/ask")
async def ask(body: AskRequest, x_license_key: str = Header(...)):
    reg = db.get_registration(x_license_key)

    # ── Pending / trial path ──────────────────────────────────────
    if reg and reg["status"] == "pending":
        if reg["trial_requests"] >= reg["trial_limit"]:
            raise HTTPException(
                403,
                f"Trial limit of {reg['trial_limit']} messages reached. "
                "Your registration is pending admin approval — "
                "contact support@intelli-network.com."
            )
        answer, _ = _call_anthropic(body)
        new_count = db.increment_trial(x_license_key)
        remaining = max(0, reg["trial_limit"] - new_count)
        return {
            "answer":             answer,
            "status":             "pending",
            "trial_remaining":    remaining,
            "requests_remaining": None,
        }

    # ── Rejected ──────────────────────────────────────────────────
    if reg and reg["status"] == "rejected":
        raise HTTPException(
            403,
            "Your registration was not approved. "
            "Contact support@intelli-network.com for assistance."
        )

    # ── Approved / pre-issued key path ────────────────────────────
    customer = db.get_customer(x_license_key)
    if not customer:
        raise HTTPException(401, "Invalid license key. Register at your ARIA setup screen.")
    if not customer["active"]:
        raise HTTPException(403, "License inactive — contact support@intelli-network.com")
    if customer["requests_month"] >= customer["plan_limit"]:
        raise HTTPException(
            429,
            f"Monthly limit of {customer['plan_limit']} requests reached. "
            "Contact support to upgrade your plan."
        )

    answer, tokens = _call_anthropic(body)
    db.log_request(x_license_key, tokens)

    return {
        "answer":             answer,
        "status":             "approved",
        "trial_remaining":    None,
        "requests_remaining": customer["plan_limit"] - customer["requests_month"] - 1,
    }


# ── Admin: dashboard ─────────────────────────────────────────────

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(key: str = ""):
    _check_admin(key)
    registrations = db.get_all_registrations()
    html = DASHBOARD_HTML.replace(
        "__REGISTRATIONS_JSON__",
        json.dumps(registrations)
    )
    return HTMLResponse(html)


# ── Admin: registration actions ───────────────────────────────────

@app.post("/admin/registrations/approve")
async def admin_approve(body: AdminActionRequest,
                        x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    if not db.approve(body.license_key, plan_limit=body.plan_limit):
        raise HTTPException(404, "Registration not found")
    return {"status": "approved", "license_key": body.license_key}


@app.post("/admin/registrations/reject")
async def admin_reject(body: AdminActionRequest,
                       x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    if not db.reject(body.license_key, notes=body.notes or ""):
        raise HTTPException(404, "Registration not found")
    return {"status": "rejected", "license_key": body.license_key}


# ── Admin: usage / key management ────────────────────────────────

@app.get("/admin/usage")
async def usage(x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    return {"customers": db.get_all_usage()}


@app.post("/admin/keys")
async def create_key(body: dict, x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    key = db.create_key(
        name=body["name"], email=body.get("email", ""),
        plan_limit=body.get("plan_limit", 500),
        key_type=body.get("type", "live")
    )
    return {"license_key": key, "name": body["name"], "plan_limit": body.get("plan_limit", 500)}


@app.patch("/admin/keys/{license_key}/deactivate")
async def deactivate(license_key: str, x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    db.set_active(license_key, False)
    return {"status": "deactivated"}


@app.patch("/admin/keys/{license_key}/activate")
async def activate(license_key: str, x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    db.set_active(license_key, True)
    return {"status": "activated"}
