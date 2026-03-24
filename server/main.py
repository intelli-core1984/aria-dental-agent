"""
ARIA Proxy Server
FastAPI app — sits between every ARIA install and Anthropic.
Your Anthropic key never leaves this server.
"""
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv
from db import Database

load_dotenv()

app = FastAPI(title="ARIA Proxy", version="1.0.0")
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


class CreateKeyRequest(BaseModel):
    name:       str
    email:      str = ""
    plan_limit: int = 500
    key_type:   str = "live"   # "live" | "test"


# ── Health ────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Main ask endpoint (called by every ARIA install) ──────────────

@app.post("/ask")
async def ask(body: AskRequest, x_license_key: str = Header(...)):
    # 1. Validate key
    customer = db.get_customer(x_license_key)
    if not customer:
        raise HTTPException(401, "Invalid license key")
    if not customer["active"]:
        raise HTTPException(403, "License inactive — contact support@intelli-network.com")

    # 2. Enforce monthly limit
    if customer["requests_month"] >= customer["plan_limit"]:
        raise HTTPException(
            429,
            f"Monthly limit of {customer['plan_limit']} requests reached. "
            "Contact support to upgrade."
        )

    # 3. Call Anthropic (your key, never the customer's)
    response = _anthropic.messages.create(
        model=body.model,
        max_tokens=body.max_tokens,
        system=body.system or "You are ARIA, a helpful dental office assistant.",
        messages=body.messages
    )

    # 4. Log usage
    tokens = response.usage.input_tokens + response.usage.output_tokens
    db.log_request(x_license_key, tokens)

    return {
        "answer": response.content[0].text,
        "requests_remaining": customer["plan_limit"] - customer["requests_month"] - 1,
    }


# ── Admin endpoints (protected by ADMIN_KEY) ─────────────────────

def _check_admin(key: str):
    if key != os.environ.get("ADMIN_KEY", ""):
        raise HTTPException(403, "Invalid admin key")


@app.post("/admin/keys")
async def create_key(body: CreateKeyRequest, x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    key = db.create_key(
        name=body.name, email=body.email,
        plan_limit=body.plan_limit, key_type=body.key_type
    )
    return {"license_key": key, "name": body.name, "plan_limit": body.plan_limit}


@app.get("/admin/usage")
async def usage(x_admin_key: str = Header(...)):
    _check_admin(x_admin_key)
    return {"customers": db.get_all_usage()}


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
