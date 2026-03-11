# backend/deps/auth.py
from fastapi import Header, HTTPException, Depends
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # used in header for /auth/v1/user

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in env")

def get_current_user(authorization: str = Header(None)):
    """
    Verify Supabase JWT by calling Supabase auth endpoint:
    GET {SUPABASE_URL}/auth/v1/user with Authorization: Bearer <token> and apikey header
    Returns user dict with at least 'id' and 'email'.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "")

    resp = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = resp.json()
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="Invalid user data from Supabase")
    return user  # has id, email, etc.
