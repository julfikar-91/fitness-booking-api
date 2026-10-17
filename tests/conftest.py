import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long-for-testing")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import timedelta

from app.main import app
from app.database import Base, get_db
from app.models import FitnessClass
from app.utils.timezone import get_current_ist_time

TEST_DB_FILE = "./test_temp.db"
SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        test_engine.dispose()
        Base.metadata.drop_all(bind=test_engine)
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except OSError:
                pass


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency yielding a thread-safe session per request."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register and log in a regular test user, returning Bearer auth header."""
    user_payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "Password123!"
    }
    client.post("/signup", json=user_payload)
    login_resp = client.post("/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_class(db_session):
    """Insert a sample upcoming class in test database."""
    now_ist = get_current_ist_time()
    fitness_class = FitnessClass(
        name="Morning Yoga",
        date_time=now_ist + timedelta(days=2),
        instructor="Sarah Connor",
        total_slots=10,
        available_slots=10
    )
    db_session.add(fitness_class)
    db_session.commit()
    db_session.refresh(fitness_class)
    return fitness_class


@pytest.fixture
def single_slot_class(db_session):
    """Insert an upcoming class with exactly 1 available slot to test overbooking."""
    now_ist = get_current_ist_time()
    fitness_class = FitnessClass(
        name="VIP Exclusive HIIT",
        date_time=now_ist + timedelta(days=3),
        instructor="Arnold Schwarzenegger",
        total_slots=1,
        available_slots=1
    )
    db_session.add(fitness_class)
    db_session.commit()
    db_session.refresh(fitness_class)
    return fitness_class
