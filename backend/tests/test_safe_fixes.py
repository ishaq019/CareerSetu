"""Tests for the "safe fixes" sweep.

These lock in the high-signal hardening changes without going broad:
  * ``app.core.config.Settings.validate_for_environment`` — refuse to boot in
    production with a weak / placeholder JWT secret.
  * ``app.modules.documents.latex_resume._url`` — reject URLs that would break
    out of a LaTeX ``\\href{}`` first argument, or that use a non-http(s) /
    non-mailto scheme.
  * The CORS regex in ``app.main`` must be end-anchored so a hostile origin
    like ``syedishaq.me.evil.example`` cannot match.
  * ``app.main``'s ``SQLAlchemyError`` handler returns a clean 500 (routes rely
    on it instead of per-route try/rollback blocks).

The tests do not need a database and run in milliseconds.
"""
from __future__ import annotations


# --- LaTeX URL hardening ---------------------------------------------------


def test_url_accepts_safe_schemes():
    from app.modules.documents.latex_resume import _url

    assert _url("https://github.com/me") == "https://github.com/me"
    assert _url("http://example.com/x") == "http://example.com/x"
    assert _url("mailto:a@b.com") == "mailto:a@b.com"
    # Bare handle (no scheme) is allowed for ``\href{someone}`` linkify.
    assert _url("syedishaq") == "syedishaq"


def test_url_rejects_dangerous_schemes():
    from app.modules.documents.latex_resume import _url

    assert _url("javascript:alert(1)") == ""
    assert _url("JavaScript:alert(1)") == ""  # case-insensitive
    assert _url("data:text/html,<script>") == ""
    assert _url("file:///etc/passwd") == ""
    assert _url("ftp://example.com") == ""


def test_url_rejects_structural_characters():
    """A URL that contains LaTeX-structural characters (curly braces,
    backslashes, control chars) must not be embedded in ``\\href{...}``."""
    from app.modules.documents.latex_resume import _url

    assert _url("https://x.com/{evil}") == ""
    assert _url("https://x.com\\foo") == ""
    assert _url("https://x.com\nfoo") == ""
    assert _url("https://x.com\rfoo") == ""


def test_url_handles_empty_and_ambiguous():
    from app.modules.documents.latex_resume import _url

    assert _url("") == ""
    assert _url("   ") == ""
    assert _url(None) == ""
    # Ambiguous (single colon, no scheme) — refuse rather than guess.
    assert _url("user:pass") == ""
    # Trailing whitespace gets stripped; embedded newlines are rejected.
    assert _url("  https://x.com  ") == "https://x.com"


# --- JWT secret production validation --------------------------------------


def test_validate_for_environment_allows_dev_with_short_secret():
    """In development the default short / placeholder secret is fine — the
    suite (and `npm run dev`) must keep booting without ceremony."""
    from app.core.config import Settings

    s = Settings(environment="development", jwt_secret="short")
    s.validate_for_environment()  # no exception


def test_validate_for_environment_rejects_placeholder_in_production():
    from app.core.config import Settings

    s = Settings(
        environment="production",
        jwt_secret="dev-only-change-this-secret-to-a-32-byte-random-value",
    )
    try:
        s.validate_for_environment()
    except RuntimeError as exc:
        assert "JWT_SECRET" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for placeholder secret in production")


def test_validate_for_environment_rejects_short_secret_in_production():
    from app.core.config import Settings

    s = Settings(environment="production", jwt_secret="only-31-chars-not-enoughxx")
    # Length is 29 — under the 32-char floor.
    try:
        s.validate_for_environment()
    except RuntimeError as exc:
        assert "32 characters" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for short secret in production")


def test_validate_for_environment_accepts_strong_secret_in_production():
    from app.core.config import Settings

    s = Settings(environment="production", jwt_secret="x" * 48)
    s.validate_for_environment()  # no exception


def test_validate_for_environment_accepts_prod_alias():
    from app.core.config import Settings

    s = Settings(environment="prod", jwt_secret="x" * 48)
    s.validate_for_environment()  # no exception


# --- CORS regex end-anchoring ---------------------------------------------


def test_cors_regex_is_end_anchored():
    """The CORS regex must be anchored at both ends so an attacker cannot
    register ``syedishaq.me.evil.example`` and get credentialed responses."""
    import re

    from starlette.middleware.cors import CORSMiddleware

    from app.main import app

    (cors,) = [m for m in app.user_middleware if m.cls is CORSMiddleware]
    rx = re.compile(cors.kwargs["allow_origin_regex"])
    assert rx.match("https://syedishaq.me")
    assert rx.match("https://app.syedishaq.me")
    assert not rx.match("https://syedishaq.me.evil.example")
    assert not rx.match("https://syedishaq.meevil.example")
    assert not rx.match("http://syedishaq.me")  # protocol is fixed to https
    assert not rx.match("https://syedishaq.me/path")  # no path component


# --- Central database-error handler ----------------------------------------


def test_sqlalchemy_error_becomes_clean_500():
    """Routes no longer carry their own try/rollback blocks — the app-level
    handler turns any SQLAlchemyError into a 500 with no driver detail."""
    from fastapi.testclient import TestClient
    from sqlalchemy.exc import OperationalError

    from app.main import app

    @app.get("/_boom_test")
    def _boom():
        raise OperationalError("INSERT INTO secret_table", {}, Exception("pg detail"))

    with TestClient(app, raise_server_exceptions=False) as client:
        res = client.get("/_boom_test")
    assert res.status_code == 500
    assert res.json() == {"detail": "Database error. Please try again."}
    assert "secret_table" not in res.text
