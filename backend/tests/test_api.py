"""End-to-end API tests against an in-memory SQLite database (no LLM/Chroma)."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_db_ok(client):
    assert client.get("/health/db").json()["status"] == "ok"


def test_guest_analysis_no_auth(client):
    resume = "Experienced Python developer who built and deployed FastAPI services with PostgreSQL and Docker."
    jd = "Looking for a Python engineer with FastAPI, PostgreSQL and Docker experience to build REST APIs."
    r = client.post("/api/v1/analysis", json={"resume_text": resume, "job_description": jd})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["match_score"] <= 100
    assert body["recommendation"] in {"STRONG_MATCH", "MATCH_WITH_IMPROVEMENTS", "LOW_MATCH"}
    assert body["id"] is None  # not saved for guests


def test_analysis_validation(client):
    r = client.post("/api/v1/analysis", json={"resume_text": "too short", "job_description": "x"})
    assert r.status_code == 422


def _auth_headers(client, email="user@example.com", password="StrongPass123"):
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_signup_login_me_flow(client):
    headers = _auth_headers(client)
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"

    # duplicate signup rejected
    dup = client.post("/api/v1/auth/signup", json={"email": "user@example.com", "password": "StrongPass123"})
    assert dup.status_code == 409

    # login works
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "StrongPass123"})
    assert login.status_code == 200

    # wrong password rejected
    bad = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "WrongPass123"})
    assert bad.status_code == 401


def test_protected_routes_require_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/analysis/history").status_code == 401
    assert client.post("/api/v1/chat", json={"question": "hello there"}).status_code == 401


def test_analysis_save_and_history(client):
    headers = _auth_headers(client)
    resume = "Python developer experienced with FastAPI, PostgreSQL, Docker and REST APIs in production."
    jd = "Hiring a backend engineer skilled in Python, FastAPI, PostgreSQL and Docker."
    r = client.post(
        "/api/v1/analysis",
        json={"resume_text": resume, "job_description": jd, "save": True},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["id"] is not None

    history = client.get("/api/v1/analysis/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1

    record_id = history.json()[0]["id"]
    detail = client.get(f"/api/v1/analysis/history/{record_id}", headers=headers)
    assert detail.status_code == 200
    assert "result" in detail.json()

    assert client.delete(f"/api/v1/analysis/history/{record_id}", headers=headers).status_code == 204
    assert len(client.get("/api/v1/analysis/history", headers=headers).json()) == 0


def test_roadmap_fallback_and_persistence(client):
    headers = _auth_headers(client)
    gen = client.post("/api/v1/roadmap/generate", json={"skills": ["React", "Docker"]}, headers=headers)
    assert gen.status_code == 200
    assert len(gen.json()["items"]) == 2

    saved = client.post("/api/v1/roadmap", json={"items": gen.json()["items"]}, headers=headers)
    assert saved.status_code == 200
    assert len(client.get("/api/v1/roadmap", headers=headers).json()["items"]) == 2


def test_interview_question_fallback(client):
    headers = _auth_headers(client)
    r = client.post("/api/v1/interview/question", json={"difficulty": "basic"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["question"]
