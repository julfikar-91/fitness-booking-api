from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from app.models import FitnessClass
from app.utils.timezone import get_current_ist_time


def test_book_class_success(client, auth_headers, sample_class):
    initial_slots = sample_class.available_slots
    payload = {
        "class_id": sample_class.id,
        "client_name": "Alice In Wonderland",
        "client_email": "alice@wonderland.com"
    }
    response = client.post("/book", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["class_id"] == sample_class.id
    assert data["client_name"] == "Alice In Wonderland"
    assert data["client_email"] == "alice@wonderland.com"
    assert "dateTime" in data
    assert "instructor" in data

    # Verify slot was deducted
    classes_resp = client.get("/classes")
    updated_class = next(c for c in classes_resp.json() if c["id"] == sample_class.id)
    assert updated_class["availableSlots"] == initial_slots - 1


def test_book_class_unauthenticated(client, sample_class):
    payload = {
        "class_id": sample_class.id,
        "client_name": "Bob",
        "client_email": "bob@example.com"
    }
    response = client.post("/book", json=payload)
    assert response.status_code == 401


def test_book_nonexistent_class(client, auth_headers):
    payload = {
        "class_id": 999999,
        "client_name": "Charlie",
        "client_email": "charlie@example.com"
    }
    response = client.post("/book", json=payload, headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_prevent_duplicate_booking(client, auth_headers, sample_class):
    payload = {
        "class_id": sample_class.id,
        "client_name": "Duplicate Tester",
        "client_email": "dup@example.com"
    }
    # First booking should succeed
    resp1 = client.post("/book", json=payload, headers=auth_headers)
    assert resp1.status_code == 201

    # Second booking by same client/email for same class should fail with 409 Conflict
    resp2 = client.post("/book", json=payload, headers=auth_headers)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


def test_booking_for_friend_allowed(client, auth_headers, sample_class):
    """An authenticated user can book a seat for themselves and another for a friend with a different email."""
    resp1 = client.post("/book", json={
        "class_id": sample_class.id,
        "client_name": "Primary User",
        "client_email": "primary@example.com"
    }, headers=auth_headers)
    assert resp1.status_code == 201

    resp2 = client.post("/book", json={
        "class_id": sample_class.id,
        "client_name": "Friend User",
        "client_email": "friend@example.com"
    }, headers=auth_headers)
    assert resp2.status_code == 201


def test_prevent_overbooking(client, single_slot_class):
    # Register User A
    client.post("/signup", json={"name": "User A", "email": "usera@test.com", "password": "Password123!"})
    login_a = client.post("/login", json={"email": "usera@test.com", "password": "Password123!"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    client.post("/signup", json={"name": "User B", "email": "userb@test.com", "password": "Password123!"})
    login_b = client.post("/login", json={"email": "userb@test.com", "password": "Password123!"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A books the 1 available slot -> Should succeed
    resp_a = client.post("/book", json={
        "class_id": single_slot_class.id,
        "client_name": "User A",
        "client_email": "usera@test.com"
    }, headers=headers_a)
    assert resp_a.status_code == 201

    # User B attempts to book the same class which now has 0 slots -> Must fail with 409 Conflict
    resp_b = client.post("/book", json={
        "class_id": single_slot_class.id,
        "client_name": "User B",
        "client_email": "userb@test.com"
    }, headers=headers_b)
    assert resp_b.status_code == 409
    assert "No slots available" in resp_b.json()["detail"]


def test_book_past_class_rejected(client, auth_headers, db_session):
    """Booking a class whose scheduled time has passed must be rejected with 400."""
    now_ist = get_current_ist_time()
    past_class = FitnessClass(
        name="Yesterday Yoga",
        date_time=now_ist - timedelta(days=1),
        instructor="Past Instructor",
        total_slots=10,
        available_slots=10
    )
    db_session.add(past_class)
    db_session.commit()
    db_session.refresh(past_class)

    resp = client.post("/book", json={
        "class_id": past_class.id,
        "client_name": "Late Bird",
        "client_email": "latebird@example.com"
    }, headers=auth_headers)
    assert resp.status_code == 400
    assert "already taken place" in resp.json()["detail"].lower()


def test_get_user_bookings(client, auth_headers, sample_class):
    # Book a slot first
    client.post("/book", json={
        "class_id": sample_class.id,
        "client_name": "Alice In Wonderland",
        "client_email": "alice@wonderland.com"
    }, headers=auth_headers)

    # Fetch user bookings
    response = client.get("/bookings", headers=auth_headers)
    assert response.status_code == 200
    bookings = response.json()
    assert isinstance(bookings, list)
    assert len(bookings) == 1
    b = bookings[0]
    assert b["class_id"] == sample_class.id
    assert b["class_name"] == sample_class.name
    assert b["instructor"] == sample_class.instructor
    assert b["client_name"] == "Alice In Wonderland"


def test_user_booking_isolation(client, sample_class):
    """User B should not see bookings made by User A."""
    # User A signs up, logs in, and books
    client.post("/signup", json={"name": "User A", "email": "isolation_a@test.com", "password": "Password123!"})
    login_a = client.post("/login", json={"email": "isolation_a@test.com", "password": "Password123!"})
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    client.post("/book", json={
        "class_id": sample_class.id,
        "client_name": "User A Attendee",
        "client_email": "attendee_a@test.com"
    }, headers=headers_a)

    # User B signs up and logs in
    client.post("/signup", json={"name": "User B", "email": "isolation_b@test.com", "password": "Password123!"})
    login_b = client.post("/login", json={"email": "isolation_b@test.com", "password": "Password123!"})
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # User B fetches their bookings -> must be empty
    resp_b = client.get("/bookings", headers=headers_b)
    assert resp_b.status_code == 200
    assert resp_b.json() == []


def test_concurrent_booking_race_condition(client, db_session):
    """
    High-concurrency test simulating 10 concurrent threads attempting to book a class
    with only 2 available slots. Strictly verifies atomic slot deduction: exactly 2
    must succeed (201) and 8 must be rejected (409 Conflict), leaving 0 remaining slots.
    """
    now_ist = get_current_ist_time()
    limited_class = FitnessClass(
        name="Ultra Limited HIIT",
        date_time=now_ist + timedelta(days=4),
        instructor="The Terminator",
        total_slots=2,
        available_slots=2
    )
    db_session.add(limited_class)
    db_session.commit()
    db_session.refresh(limited_class)

    # Pre-create 10 users and auth tokens
    user_headers = []
    for i in range(10):
        email = f"racer_{i}@speed.com"
        client.post("/signup", json={"name": f"Racer {i}", "email": email, "password": "Password123!"})
        login_resp = client.post("/login", json={"email": email, "password": "Password123!"})
        token = login_resp.json()["access_token"]
        user_headers.append(({"Authorization": f"Bearer {token}"}, email))

    target_class_id = limited_class.id

    def attempt_booking(args):
        hdr, client_email = args
        return client.post("/book", json={
            "class_id": target_class_id,
            "client_name": f"Client {client_email}",
            "client_email": client_email
        }, headers=hdr)

    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(attempt_booking, user_headers))

    successes = [r for r in responses if r.status_code == 201]
    conflicts = [r for r in responses if r.status_code == 409]

    assert len(successes) == 2, f"Expected exactly 2 successes, got {len(successes)}"
    assert len(conflicts) == 8, f"Expected exactly 8 409 Conflicts, got {len(conflicts)}"

    # Check database state: available slots must be exactly 0
    db_session.refresh(limited_class)
    assert limited_class.available_slots == 0
