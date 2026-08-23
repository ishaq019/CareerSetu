from app.core.security import hash_password, verify_password, create_access_token

def test_password_hashing():
    encoded = hash_password("StrongPass123")
    assert encoded != "StrongPass123"
    assert verify_password("StrongPass123", encoded)
    assert not verify_password("wrong", encoded)

def test_token():
    token = create_access_token(7, "a@example.com")
    assert isinstance(token, str) and len(token) > 20
