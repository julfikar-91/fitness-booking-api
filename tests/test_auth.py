from datetime import timedelta
from app.security import create_access_token


def test_signup_success(client):
    response = client.post("/signup", json={
        "name": "Bruce Wayne",
        "email": "bruce@wayne.com",
        "password": "GothamPassword123!"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bruce Wayne"
    assert data["email"] == "bruce@wayne.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_signup_duplicate_email(client):
    payload = {
        "name": "Clark Kent",
        "email": "clark@dailyplanet.com",
        "password": "KryptonPassword123!"
    }
    resp1 = client.post("/signup", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/signup", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


def test_signup_missing_fields(client):
    # Missing password
    resp = client.post("/signup", json={
        "name": "Diana Prince",
        "email": "diana@themyscira.com"
    })
    assert resp.status_code == 422
    assert "errors" in resp.json()


def test_signup_invalid_email(client):
    resp = client.post("/signup", json={
        "name": "Diana Prince",
        "email": "not-an-email",
        "password": "Password123!"
    })
    assert resp.status_code == 422


def test_signup_short_password(client):
    resp = client.post("/signup", json={
        "name": "Barry Allen",
        "email": "barry@centralcity.com",
        "password": "123"  # Less than 6 characters
    })
    assert resp.status_code == 422


def test_signup_password_too_long_bytes(client):
    """Bcrypt 5.x rejects passwords > 72 bytes. Schema should return 422, not 500."""
    # 80 character password
    long_pw_80 = "A" * 80
    resp = client.post("/signup", json={
        "name": "Long Password User",
        "email": "longpw@test.com",
        "password": long_pw_80
    })
    assert resp.status_code == 422
    assert "72" in str(resp.json())

    # Multi-byte UTF-8 password: 20 emojis * 4 bytes = 80 bytes (exceeds 72 byte limit)
    multi_byte_pw = "🔒" * 20
    resp_multi = client.post("/signup", json={
        "name": "Multi Byte User",
        "email": "multibyte@test.com",
        "password": multi_byte_pw
    })
    assert resp_multi.status_code == 422
    assert "72 bytes" in str(resp_multi.json())


def test_login_success(client):
    # First sign up
    client.post("/signup", json={
        "name": "Tony Stark",
        "email": "tony@stark.com",
        "password": "IronManPassword123!"
    })

    # Then log in
    response = client.post("/login", json={
        "email": "tony@stark.com",
        "password": "IronManPassword123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_invalid_password(client):
    client.post("/signup", json={
        "name": "Steve Rogers",
        "email": "steve@avengers.com",
        "password": "CorrectPassword123!"
    })

    response = client.post("/login", json={
        "email": "steve@avengers.com",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post("/login", json={
        "email": "nobody@nowhere.com",
        "password": "AnyPassword123!"
    })
    assert response.status_code == 401


def test_refresh_token(client):
    client.post("/signup", json={
        "name": "Natasha Romanoff",
        "email": "natasha@shield.gov",
        "password": "BlackWidow123!"
    })

    login_resp = client.post("/login", json={
        "email": "natasha@shield.gov",
        "password": "BlackWidow123!"
    })
    refresh_tok = login_resp.json()["refresh_token"]

    refresh_resp = client.post("/refresh", json={"refresh_token": refresh_tok})
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_expired_access_token(client):
    """An expired token should return 401 Unauthorized."""
    expired_token = create_access_token(
        data={"sub": "1", "email": "expired@example.com"},
        expires_delta=timedelta(minutes=-10)
    )
    response = client.get("/bookings", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_refresh_with_access_token_rejected(client):
    """Sending an access token instead of a refresh token to /refresh should return 401."""
    access_tok = create_access_token(data={"sub": "1", "email": "user@example.com"})
    resp = client.post("/refresh", json={"refresh_token": access_tok})
    assert resp.status_code == 401
    assert "not a refresh token" in resp.json()["detail"].lower()
