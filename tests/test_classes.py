from datetime import timedelta
from app.utils.timezone import get_current_ist_time


def test_create_class_authenticated(client, auth_headers):
    future_time = (get_current_ist_time() + timedelta(days=10)).replace(microsecond=0).isoformat()
    payload = {
        "name": "Yoga Flow",
        "dateTime": future_time,
        "instructor": "John Doe",
        "availableSlots": 20
    }
    response = client.post("/classes", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Yoga Flow"
    assert data["instructor"] == "John Doe"
    assert data["availableSlots"] == 20
    assert "dateTime" in data
    assert "+05:30" in data["dateTime"]  # Verifies stored/returned in IST (+05:30)


def test_create_class_unauthenticated(client):
    future_time = (get_current_ist_time() + timedelta(days=10)).replace(microsecond=0).isoformat()
    payload = {
        "name": "HIIT Blast",
        "dateTime": future_time,
        "instructor": "John Doe",
        "availableSlots": 15
    }
    response = client.post("/classes", json=payload)
    assert response.status_code == 401


def test_create_class_invalid_slots(client, auth_headers):
    future_time = (get_current_ist_time() + timedelta(days=10)).replace(microsecond=0).isoformat()
    payload = {
        "name": "Spinning",
        "dateTime": future_time,
        "instructor": "Jane Smith",
        "availableSlots": 0  # Invalid, must be > 0
    }
    response = client.post("/classes", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_create_class_missing_fields(client, auth_headers):
    payload = {
        "name": "Spinning",
        "availableSlots": 10
        # Missing dateTime and instructor
    }
    response = client.post("/classes", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_create_past_class_rejected(client, auth_headers):
    """Attempting to schedule a class with a past dateTime must return 422."""
    past_time = "2025-06-15T10:00:00Z"
    payload = {
        "name": "Past Yoga Class",
        "dateTime": past_time,
        "instructor": "Old Master",
        "availableSlots": 10
    }
    response = client.post("/classes", json=payload, headers=auth_headers)
    assert response.status_code == 422
    assert "cannot be in the past" in str(response.json()).lower()


def test_create_class_naive_datetime_treated_as_ist(client, auth_headers):
    """Naive datetime (no timezone offset) is naturally interpreted as studio local time (IST)."""
    future_date = (get_current_ist_time() + timedelta(days=7)).strftime("%Y-%m-%d")
    naive_dt_str = f"{future_date}T10:00:00"  # No 'Z' or offset
    payload = {
        "name": "Local Studio Pilates",
        "dateTime": naive_dt_str,
        "instructor": "Priya Sharma",
        "availableSlots": 15
    }
    response = client.post("/classes", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    # Should be 10:00:00+05:30 (IST)
    assert f"{future_date}T10:00:00+05:30" == data["dateTime"]


def test_get_classes_list(client, sample_class):
    response = client.get("/classes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "id" in item
    assert "name" in item
    assert "dateTime" in item
    assert "instructor" in item
    assert "availableSlots" in item


def test_get_classes_timezone_conversion(client, sample_class):
    # Request classes converted to UTC
    response = client.get("/classes?tz=UTC")
    assert response.status_code == 200
    data = response.json()
    item = data[0]
    # UTC format should end in +00:00 or Z
    assert "+00:00" in item["dateTime"] or "Z" in item["dateTime"]

    # Request classes converted to America/New_York
    response_ny = client.get("/classes?tz=America/New_York")
    assert response_ny.status_code == 200
    item_ny = response_ny.json()[0]
    assert "-04:00" in item_ny["dateTime"] or "-05:00" in item_ny["dateTime"]


def test_get_classes_invalid_timezone(client, sample_class):
    response = client.get("/classes?tz=Invalid/Timezone_Name")
    assert response.status_code == 400
    assert "Unknown timezone identifier" in response.json()["detail"]
