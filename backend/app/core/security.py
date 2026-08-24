"""Password hashing (PBKDF2-SHA256) and JWT helpers.

No third-party password library is required: PBKDF2 is part of the standard
library and hashes are stored in a self-describing ``scheme$rounds$salt$digest``
format so the work factor can be raised over time without breaking old hashes.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGORITHM = "HS256"
PBKDF2_ROUNDS = 600_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode + verify a JWT. Raises ``jwt.PyJWTError`` on any problem."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


# --- OAuth state (CSRF protection for the authorization-code flow) -----------
# The ``state`` round-tripped through Google is a short-lived signed JWT. Because
# it is signed with our server secret, an attacker cannot forge or tamper with
# it, which defends the callback against CSRF and mix-up attacks. The embedded
# nonce also lets us bind the request to the eventual response.
OAUTH_STATE_TTL_SECONDS = 600  # 10 minutes


def create_oauth_state(nonce: str, redirect_uri: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "typ": "oauth_state",
        "nonce": nonce,
        "ruri": redirect_uri,
        "iat": now,
        "exp": now + timedelta(seconds=OAUTH_STATE_TTL_SECONDS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_oauth_state(token: str) -> dict:
    """Decode + verify an OAuth state token. Raises ``jwt.PyJWTError`` if the
    signature is invalid, it has expired, or it is not an OAuth state token."""
    data = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    if data.get("typ") != "oauth_state":
        raise jwt.InvalidTokenError("not an oauth_state token")
    return data
