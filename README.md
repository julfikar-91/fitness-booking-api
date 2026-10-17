# 🏋️‍♂️ Fitness Studio Booking API

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)


A robust RESTful Booking API for a fictional fitness studio built with **Python 3**, **FastAPI**, **SQLAlchemy**, and **Pydantic v2**.

The studio offers fitness classes (Yoga, Zumba, HIIT, Pilates, etc.). Authenticated users can explore upcoming classes, schedule new classes, reserve slots with atomic overbooking protection, and view their personalized booking history.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Architecture](#-project-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
  - [Environment Variables](#environment-variables)
- [Database Seeding](#-database-seeding)
- [Running the Application](#-running-the-application)
- [Interactive API Documentation](#-interactive-api-documentation)
- [API Reference & Usage](#-api-reference--usage)
  - [Health Check](#health-check)
  - [Authentication](#authentication)
  - [Fitness Classes](#fitness-classes)
  - [Bookings](#bookings)
- [Timezone Management (IST)](#-timezone-management-ist)
- [Design Decisions & Limitations](#-design-decisions--limitations)
- [Running Tests](#-running-tests)
- [Postman Collection](#-postman-collection)
- [Error Handling](#-error-handling)

---

## 🧠 Overview

In this system:
1. **User Authentication**: Secure JWT (JSON Web Token) auth with password hashing (`bcrypt`), access tokens, and refresh tokens. Passwords are strictly validated against bcrypt's 72-byte limit to prevent runtime crashes.
2. **Class Scheduling**: Fitness classes can be scheduled with custom capacities and start times. All class times are normalized and stored in **Indian Standard Time (IST, UTC+05:30)**. Scheduling classes in the past is rejected.
3. **Atomic Slot Reservation**: Protects against race conditions and overbooking using atomic SQL decrement conditions (`available_slots > 0`).
4. **Duplicate Prevention**: Prevents duplicate bookings for the same class per attendee email.
5. **Timezone Conversion**: Allows clients globally to query schedules in their preferred timezone (e.g., `UTC`, `America/New_York`) on demand.

---

## ✨ Key Features

- **JWT Authentication & Token Lifecycle**: Access tokens (short-lived) + Refresh tokens (long-lived) with secure direct `bcrypt` hashing.
- **Atomic Booking & Overbooking Prevention**: Prevents overbooking even under high-concurrency conditions using atomic SQL decrement queries. Returns `409 Conflict` on slot exhaustion.
- **Concurrent Race-Condition Test Suite**: Verified via multi-threaded tests simulating simultaneous booking requests competing for limited seats.
- **Comprehensive IST Timezone Management**:
  - Automatically parses incoming ISO 8601 timestamps.
  - Interprets naive datetimes naturally as local studio time (**IST**, `Asia/Kolkata`).
  - Normalizes and stores all class schedules in **Indian Standard Time (IST, UTC+05:30)**.
  - Supports dynamic query-time conversions (e.g. `?tz=UTC`, `?tz=America/New_York`).
- **Structured Request Logging & Performance Metrics**: Middleware automatically logs requests and records total execution time in the `X-Process-Time-Ms` response header.
- **Automated Validation**: Pydantic v2 schemas with human-readable error messages for missing or invalid parameters.
- **Interactive OpenAPI & Swagger UI**: Auto-generated documentation and sandbox available at `/docs` and `/redoc`.
- **Database Seeder**: Pre-configured mock data for quick manual or automated testing, including a fully-booked class.
- **Comprehensive Pytest Suite**: 31 automated unit, integration, and multi-threaded concurrency tests.

---

## 🛠️ Tech Stack

| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ (Tested on Python 3.13) |
| **Framework** | FastAPI |
| **ASGI Server** | Uvicorn |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | SQLite (File-based database for simplicity; easily swappable with PostgreSQL) |
| **Validation** | Pydantic v2 & Pydantic-Settings |
| **Authentication** | PyJWT, Bcrypt (direct) |
| **Testing** | Pytest, FastAPI TestClient, HTTPX |
| **Timezone** | Python standard library `zoneinfo` (`Asia/Kolkata`) |

---

## 📁 Project Architecture

```text
fitness-booking-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application, middleware, lifecycle, exception handlers
│   ├── config.py            # Pydantic BaseSettings configuration
│   ├── database.py          # SQLAlchemy engine, session maker, DB dependency
│   ├── models.py            # Database models (User, FitnessClass, Booking)
│   ├── schemas.py           # Pydantic request/response schemas with validation
│   ├── security.py          # Bcrypt hashing and JWT generation/verification
│   ├── dependencies.py      # Auth dependency (get_current_user)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # /signup, /login, /refresh
│   │   ├── classes.py       # POST /classes, GET /classes
│   │   └── bookings.py      # POST /book, GET /bookings
│   └── utils/
│       ├── __init__.py
│       ├── timezone.py      # IST normalization & dynamic timezone conversion
│       └── logging.py       # Structured application logger
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # In-memory SQLite fixtures and test clients
│   ├── test_auth.py         # Authentication & token tests
│   ├── test_classes.py      # Class creation, filtering & timezone tests
│   └── test_bookings.py     # Booking flow, duplicate check, isolation & concurrency tests
├── seed.py                  # Seed script for initial sample data
├── requirements.txt         # Pinned exact project dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Ignored files (venv, DB, cache)
├── postman_collection.json  # Importable Postman collection
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10** or higher installed on your system.
- **Git** installed on your system.

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/julfikar-91/fitness-booking-api.git
   cd fitness-booking-api
   ```

2. **Create and activate a virtual environment:**
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install the pinned dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Generate a secure 256-bit secret key:
```bash
openssl rand -hex 32
```

Create a `.env` file from the provided `.env.example`:
- **Linux / macOS:**
  ```bash
  cp .env.example .env
  ```
- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```

Update your `.env` file with your generated secret:
```env
PROJECT_NAME="Fitness Studio Booking API"
VERSION="1.0.0"
DATABASE_URL="sqlite:///./fitness_booking.db"
SECRET_KEY="<paste-your-generated-openssl-key-here>"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
APP_TIMEZONE="Asia/Kolkata"
```

> [!NOTE]
> The application will refuse to start if `SECRET_KEY` is not provided in your environment or `.env` file.

---

## 🌱 Database Seeding

Populate the database with initial users, upcoming fitness classes, and test bookings:

```bash
python seed.py
```

### Pre-configured Sample Accounts:
- **Instructor Account:**
  - Email: `john@fitness.com`
  - Password: `Password123!`
- **Client 1 Account:**
  - Email: `alice@example.com`
  - Password: `Password123!`
- **Client 2 Account:**
  - Email: `bob@example.com`
  - Password: `Password123!`

---

## 🏃 Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The server will be available at: **`http://127.0.0.1:8000`**

---

## 📖 Interactive API Documentation

FastAPI provides interactive API documentation with one-click test execution:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  *(Click "Authorize" and enter your Bearer token to test protected endpoints)*
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Reference & Usage

### Health Check

#### 1. Root & Health Check (`GET /`)
Status check displaying server state, version, current IST server time, and list of available endpoints.

**cURL Request:**
```bash
curl -X GET "http://127.0.0.1:8000/"
```

**Actual Response (`200 OK`):**
```json
{
  "status": "online",
  "app": "Fitness Studio Booking API",
  "version": "1.0.0",
  "current_time_ist": "2026-10-17T12:34:30.792859+05:30",
  "docs_url": "/docs",
  "endpoints": {
    "signup": "POST /signup",
    "login": "POST /login",
    "refresh_token": "POST /refresh",
    "create_class": "POST /classes (Auth required)",
    "list_classes": "GET /classes",
    "book_class": "POST /book (Auth required)",
    "user_bookings": "GET /bookings (Auth required)"
  }
}
```

---

### Authentication

#### 2. Sign Up (`POST /signup`)
Register a new user account. Password must be between 6 and 72 bytes.

**cURL Request:**
```bash
curl -X POST "http://127.0.0.1:8000/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "password": "SecurePassword123!"
  }'
```

**Actual Response (`201 Created`):**
```json
{
  "id": 4,
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "created_at": "2026-10-17T12:34:31.083254"
}
```

**Duplicate Email Response (`409 Conflict`):**
```json
{
  "detail": "An account with this email address already exists."
}
```

---

#### 3. Log In (`POST /login`)
Authenticate and receive JWT access & refresh tokens.

**cURL Request:**
```bash
curl -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "Password123!"
  }'
```

**Actual Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

#### 4. Refresh Token (`POST /refresh`)
Generate a new access token using a valid refresh token.

**cURL Request:**
```bash
curl -X POST "http://127.0.0.1:8000/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<YOUR_REFRESH_TOKEN>"
  }'
```

**Actual Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### Fitness Classes

#### 5. Create Class (`POST /classes`)
Schedule a new fitness class. **Requires Bearer authentication**. Class start time must be in the future.

**cURL Request:**
```bash
curl -X POST "http://127.0.0.1:8000/classes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{
    "name": "Evening Pilates",
    "dateTime": "2026-11-01T18:00:00+05:30",
    "instructor": "Sarah Connor",
    "availableSlots": 15
  }'
```

**Actual Response (`201 Created`):**
```json
{
  "id": 7,
  "name": "Evening Pilates",
  "dateTime": "2026-11-01T18:00:00+05:30",
  "instructor": "Sarah Connor",
  "availableSlots": 15
}
```

*(Note: Explicit UTC timestamps such as `2026-11-01T12:30:00Z` are automatically normalized into IST `2026-11-01T18:00:00+05:30`)*

---

#### 6. List Upcoming Classes (`GET /classes`)
Retrieve all upcoming fitness classes. Supports optional timezone conversion query parameter (`tz`).

**cURL Request (Default - IST):**
```bash
curl -X GET "http://127.0.0.1:8000/classes"
```

**Actual Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "name": "Yoga Flow & Mindfulness",
    "dateTime": "2026-10-18T14:32:12.174607+05:30",
    "instructor": "John Doe",
    "availableSlots": 19
  },
  {
    "id": 2,
    "name": "High-Intensity Interval Training (HIIT)",
    "dateTime": "2026-10-19T15:32:12.174607+05:30",
    "instructor": "Jane Smith",
    "availableSlots": 14
  }
]
```

**cURL Request (Converted to UTC):**
```bash
curl -X GET "http://127.0.0.1:8000/classes?tz=UTC"
```

**Actual Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "name": "Yoga Flow & Mindfulness",
    "dateTime": "2026-10-18T09:02:12.174607Z",
    "instructor": "John Doe",
    "availableSlots": 19
  }
]
```

---

### Bookings

#### 7. Book a Slot (`POST /book`)
Book an available slot in an upcoming class. **Requires Bearer authentication**.

**Validations handled:**
- Verifies class exists and is scheduled in the future.
- Prevents duplicate booking by the same attendee email for the same class.
- Atomically decrements `available_slots`.
- Prevents overbooking when `available_slots <= 0`.

**cURL Request:**
```bash
curl -X POST "http://127.0.0.1:8000/book" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{
    "class_id": 3,
    "client_name": "Alice Walker",
    "client_email": "alice@example.com"
  }'
```

**Actual Response (`201 Created`):**
```json
{
  "id": 3,
  "class_id": 3,
  "class_name": "Zumba Dance Workout",
  "dateTime": "2026-10-20T13:32:12.174607+05:30",
  "instructor": "Carlos Gomez",
  "client_name": "Alice Walker",
  "client_email": "alice@example.com",
  "booked_at": "2026-10-17T12:34:31.419393+05:30",
  "message": "Successfully booked slot in 'Zumba Dance Workout'. 24 slots remaining."
}
```

**Duplicate Booking Response (`409 Conflict`):**
```json
{
  "detail": "A booking for this class with this email already exists."
}
```

**Overbooking Response (`409 Conflict`):**
```json
{
  "detail": "No slots available for this class. Class is fully booked."
}
```

---

#### 8. View User Bookings (`GET /bookings`)
View all fitness classes booked by the currently authenticated user. Supports optional `?tz=` conversion parameter. **Requires Bearer authentication**.

**cURL Request (Default - IST):**
```bash
curl -X GET "http://127.0.0.1:8000/bookings" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

**Actual Response (`200 OK`):**
```json
[
  {
    "id": 3,
    "class_id": 3,
    "class_name": "Zumba Dance Workout",
    "dateTime": "2026-10-20T13:32:12.174607+05:30",
    "instructor": "Carlos Gomez",
    "client_name": "Alice Walker",
    "client_email": "alice@example.com",
    "booked_at": "2026-10-17T12:34:31.419393+05:30",
    "message": null
  },
  {
    "id": 1,
    "class_id": 1,
    "class_name": "Yoga Flow & Mindfulness",
    "dateTime": "2026-10-18T14:32:12.174607+05:30",
    "instructor": "John Doe",
    "client_name": "Alice Walker",
    "client_email": "alice@example.com",
    "booked_at": "2026-10-17T12:32:12.174607+05:30",
    "message": null
  }
]
```

**cURL Request (Converted to UTC):**
```bash
curl -X GET "http://127.0.0.1:8000/bookings?tz=UTC" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

**Actual Response (`200 OK`):**
```json
[
  {
    "id": 3,
    "class_id": 3,
    "class_name": "Zumba Dance Workout",
    "dateTime": "2026-10-20T08:02:12.174607Z",
    "instructor": "Carlos Gomez",
    "client_name": "Alice Walker",
    "client_email": "alice@example.com",
    "booked_at": "2026-10-17T07:04:31.419393Z",
    "message": null
  }
]
```

---

## 🌐 Timezone Management (IST)

- **Central Storage in IST**: All fitness class times and booking timestamps are normalized and stored in **Indian Standard Time (`Asia/Kolkata`, UTC+05:30)**.
- **Naive Datetime Interpretation**: Because the studio physically operates in India, naive timestamps without an explicit offset (e.g. `2026-11-01T18:00:00`) are treated as local studio time (`18:00 IST`), rather than assuming UTC and shifting the hour.
- **Aware Datetime Normalization**: Timestamps provided with explicit offsets or UTC designations (e.g. `2026-11-01T12:30:00Z`) are accurately converted to IST.
- **Past Class Rejection**: The API rejects scheduling classes in the past (`422 Unprocessable Content`).
- **Dynamic Conversion**: Both `GET /classes` and `GET /bookings` accept a `?tz=<TIMEZONE>` query parameter (e.g. `UTC`, `America/New_York`, `Asia/Tokyo`) using Python standard library `zoneinfo`.

---

## 💡 Design Decisions & Limitations

1. **Database Selection (SQLite vs. PostgreSQL)**:
   - *Decision*: SQLite is used for this assignment because it requires zero external setup, runs reliably in any environment, and simplifies evaluation.
   - *Limitation*: SQLite uses file-level locking for write operations. In a high-traffic production system with horizontal scaling across multiple application instances, PostgreSQL with row-level locking (`SELECT ... FOR UPDATE`) or Redis-based distributed locks would be required.

2. **Concurrency & Overbooking Prevention**:
   - *Decision*: Slot reservation is performed via an atomic database decrement:
     ```sql
     UPDATE fitness_classes 
     SET available_slots = available_slots - 1 
     WHERE id = :class_id AND available_slots > 0;
     ```
     If `rows_updated == 0`, the slot is already taken, and the API returns `409 Conflict`. A dedicated multi-threaded test (`ThreadPoolExecutor` with 10 concurrent threads) validates that no race condition can ever decrement slots below 0.

3. **HTTP 409 Conflict vs. 400 Bad Request**:
   - *Decision*: Resource state conflicts (overbooking when slots are exhausted, duplicate booking attempts, and duplicate email registrations) return `409 Conflict`, which is the standard RESTful status code for conflicts with the current state of a resource. HTTP `400` is reserved for bad request logic (such as trying to book a past class), while `422` is reserved for schema validation errors.

4. **Booking Model & Duplicate Prevention**:
   - *Decision*: Attendance uniqueness is enforced per `(class_id, client_email)` at both the application level and via a database `UniqueConstraint`. This design allows an authenticated user to book a slot for themselves and also book additional slots for friends or family members using their respective emails, while strictly preventing the same attendee email from occupying multiple seats in the same class session.

5. **Token Architecture & Refresh Token Rotation**:
   - *Limitation*: The application currently issues long-lived refresh tokens that can be reused until their expiration. Full refresh token rotation (invalidating the used refresh token and issuing a one-time single-use replacement upon each refresh) is acknowledged as a production enhancement not included in this iteration.

6. **Password Security (Bcrypt 72-Byte Boundary)**:
   - *Decision*: Bcrypt 5.x raises a runtime exception when hashing strings exceeding 72 bytes. The Pydantic signup schema enforces both character length (`max_length=72`) and exact UTF-8 byte length (`len(v.encode('utf-8')) <= 72`), preventing server crashes (`500`) and returning clean `422 Unprocessable Content` responses.

---

## 🧪 Running Tests

The test suite runs against an isolated in-memory SQLite database (`sqlite:///:memory:`) using request-scoped sessions:

```bash
pytest -v
```

### Test Coverage Summary (31 Tests):
- **Authentication (12 tests)**: Sign up, duplicate email rejection (`409`), missing fields (`422`), invalid email (`422`), short password (`422`), password >72 bytes / multi-byte UTF-8 (`422`), login success, invalid password (`401`), non-existent user (`401`), refresh token success, expired access token rejection (`401`), access token used as refresh token rejection (`401`).
- **Fitness Classes (9 tests)**: Authenticated creation (`201`), unauthenticated rejection (`401`), invalid slots count (`422`), missing fields (`422`), past class scheduling rejection (`422`), naive datetime treated as IST, upcoming classes listing, timezone conversion (`?tz=UTC`, `?tz=America/New_York`), invalid timezone parameter (`400`).
- **Bookings (10 tests)**: Successful booking (`201`), unauthenticated rejection (`401`), non-existent class (`404`), duplicate booking prevention (`409`), booking for friend with different email (`201`), overbooking prevention (`409`), past class booking rejection (`400`), user bookings listing, user booking isolation (User B cannot see User A's bookings), and multi-threaded concurrent booking race condition test.

---

## 📮 Postman Collection

A complete Postman collection is included in the root directory: [`postman_collection.json`](./postman_collection.json).

### How to use:
1. Open Postman.
2. Click **Import** in the upper left corner.
3. Select or drag-and-drop `postman_collection.json`.
4. Run the **Log In User** request — it automatically stores `accessToken` and `refreshToken` into the collection variables.
5. Execute any protected requests (`POST /classes`, `POST /book`, `GET /bookings`) with zero manual token copying!

---

## ⚠️ Error Handling

| Status Code | Description | Typical Scenario |
| :--- | :--- | :--- |
| `200 OK` | Request succeeded | Fetching classes, logging in, token refresh, viewing bookings |
| `201 Created` | Resource created | User registered, class created, booking confirmed |
| `400 Bad Request` | Client logic error | Booking a class that already took place, invalid timezone parameter |
| `401 Unauthorized` | Authentication failed | Missing/expired Bearer token, invalid login credentials, wrong token type |
| `404 Not Found` | Resource not found | Requesting non-existent `class_id` |
| `409 Conflict` | Resource state conflict | Overbooking (0 slots available), duplicate booking, duplicate email on signup |
| `422 Unprocessable Content` | Request validation failure | Missing fields, invalid email format, password > 72 bytes, scheduling class in past |
| `500 Internal Error` | Unexpected server error | Uncaught exceptions with safe masking |

## API Reference

#### Get all items

```http
  GET /api/items
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. Your API key |

#### Get item

```http
  GET /api/items/${id}
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `string` | **Required**. Id of item to fetch |

#### add(num1, num2)

Takes two numbers and returns the sum.

