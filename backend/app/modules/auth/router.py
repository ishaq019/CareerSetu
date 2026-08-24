"""Authentication: email/password sign-up & login, JWT-protected identity,
and the Google OAuth 2.0 authorization-code flow."""
from __future__ import annotations

import logging
import secrets
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_oauth_state,
    decode_access_token,
    decode_oauth_state,
    hash_password,
    verify_password,
)
from app.db import get_db
from app.models import User

router = APIRouter()
bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger("careersetu.auth")

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    is_admin: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _user_out(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "is_admin": settings.is_admin_email(user.email),
    }


def _issue(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id, user.email),
        "token_type": "bearer",
        "user": _user_out(user),
    }


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
    return _issue(user)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required.")
    try:
        data = decode_access_token(credentials.credentials)
        user_id = int(data["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists.")
    return user


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the authenticated user if a valid token is present, else ``None``.

    Used by endpoints (e.g. guest analysis) that work anonymously but persist
    extra data when the caller happens to be signed in.
    """
    if not credentials:
        return None
    try:
        data = decode_access_token(credentials.credentials)
        return db.get(User, int(data["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return _user_out(user)


def _callback_url(request: Request) -> str:
    """The redirect URI Google will call back. Uses the explicitly configured
    value when present (recommended for production so it matches the Google
    console exactly), otherwise derives it from the incoming request."""
    if settings.google_redirect_uri:
        return settings.google_redirect_uri
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/v1/auth/google/callback"


def _frontend_redirect(fragment: str) -> RedirectResponse:
    # Deliver the result in the URL fragment so the token never lands in server
    # access logs or the Referer header.
    return RedirectResponse(
        url=f"{settings.frontend_url.rstrip('/')}/login#{fragment}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/google")
def google_login(request: Request):
    """Start the Google OAuth flow: redirect the browser to Google's consent
    screen with a signed, short-lived ``state`` for CSRF protection."""
    if not settings.google_oauth_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    redirect_uri = _callback_url(request)
    nonce = secrets.token_urlsafe(24)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": create_oauth_state(nonce, redirect_uri),
        "access_type": "online",
        "prompt": "select_account",
        "include_granted_scopes": "true",
    }
    return RedirectResponse(
        url=f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Handle Google's redirect: validate state, exchange the code server-side,
    fetch the verified profile, upsert the user and hand a JWT to the SPA."""
    if error:
        return _frontend_redirect(f"error={error}")
    if not code or not state:
        return _frontend_redirect("error=missing_code")
    if not settings.google_oauth_configured:
        return _frontend_redirect("error=oauth_not_configured")

    # 1) Validate the signed state (CSRF / tamper protection). The redirect URI
    #    used to obtain the code must match the one bound into the state.
    try:
        state_data = decode_oauth_state(state)
    except jwt.PyJWTError:
        return _frontend_redirect("error=invalid_state")
    redirect_uri = state_data.get("ruri") or _callback_url(request)

    # 2) Exchange the authorization code for tokens. This is a server-to-server
    #    call over TLS authenticated with the client secret, so the response is
    #    trusted without needing to verify the id_token signature ourselves.
    try:
        with httpx.Client(timeout=15.0) as client:
            token_res = client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            token_res.raise_for_status()
            access_token = token_res.json().get("access_token")
            if not access_token:
                return _frontend_redirect("error=token_exchange_failed")

            info_res = client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            info_res.raise_for_status()
            info = info_res.json()
    except httpx.HTTPError:
        return _frontend_redirect("error=google_unreachable")

    email = (info.get("email") or "").lower().strip()
    google_sub = info.get("sub")
    if not email or not google_sub or info.get("email_verified") not in (True, "true"):
        return _frontend_redirect("error=email_unverified")

    # 3) Upsert: match on the stable Google subject first, then by email so an
    #    existing password account is linked rather than duplicated.
    try:
        user = db.query(User).filter(User.google_sub == google_sub).first()
        if user is None:
            user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(email=email, auth_provider="google")
            db.add(user)
        user.google_sub = google_sub
        if not user.auth_provider:
            user.auth_provider = "google"
        user.full_name = info.get("name") or user.full_name
        user.avatar_url = info.get("picture") or user.avatar_url
        db.commit()
        db.refresh(user)
    except SQLAlchemyError:
        # Most commonly a missing OAuth column because migration 0002_oauth has
        # not been applied. Roll back and surface a clean error to the SPA
        # instead of a bare 500 / stack trace.
        db.rollback()
        logger.exception("Google OAuth user upsert failed")
        return _frontend_redirect("error=account_persist_failed")

    # 4) Issue our own session JWT and hand it to the SPA via the URL fragment.
    return _frontend_redirect(f"token={create_access_token(user.id, user.email)}")
