from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from app.utils.timezone import normalize_to_ist, get_current_ist_time


# ----------------------------------------------------
# User & Auth Schemas
# ----------------------------------------------------

class UserSignUp(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name", examples=["John Doe"])
    email: EmailStr = Field(..., description="Valid unique email address", examples=["user@example.com"])
    password: str = Field(..., min_length=6, max_length=72, description="Password (6 to 72 characters, max 72 bytes)", examples=["SecurePass123!"])

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        """Validate that password in UTF-8 bytes does not exceed bcrypt's 72-byte limit."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes in length")
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Registered email address", examples=["user@example.com"])
    password: str = Field(..., description="User password", examples=["SecurePass123!"])


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


# ----------------------------------------------------
# Fitness Class Schemas
# ----------------------------------------------------

class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Name of the fitness class", examples=["Yoga Flow"])
    dateTime: datetime = Field(..., description="Class start time in ISO 8601 format (e.g., 2026-06-15T10:00:00Z)", examples=["2026-06-15T10:00:00Z"])
    instructor: str = Field(..., min_length=1, max_length=100, description="Instructor name", examples=["John Doe"])
    availableSlots: int = Field(..., gt=0, description="Number of available seats (must be greater than 0)", examples=[20])

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("dateTime")
    @classmethod
    def validate_and_convert_datetime(cls, v: datetime) -> datetime:
        """Convert input datetime to IST and ensure it is not scheduled in the past."""
        ist_dt = normalize_to_ist(v)
        if ist_dt < get_current_ist_time():
            raise ValueError("Class dateTime cannot be in the past. Must be scheduled for a future time.")
        return ist_dt


class ClassResponse(BaseModel):
    id: int
    name: str
    dateTime: datetime = Field(..., serialization_alias="dateTime")
    instructor: str
    availableSlots: int = Field(..., serialization_alias="availableSlots")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


# ----------------------------------------------------
# Booking Schemas
# ----------------------------------------------------

class BookingCreate(BaseModel):
    class_id: int = Field(..., gt=0, description="ID of the fitness class to book", examples=[1])
    client_name: str = Field(..., min_length=1, max_length=100, description="Name of the client", examples=["Alice"])
    client_email: EmailStr = Field(..., description="Email of the client booking the slot", examples=["alice@example.com"])


class BookingResponse(BaseModel):
    id: int
    class_id: int
    class_name: str
    dateTime: datetime
    instructor: str
    client_name: str
    client_email: str
    booked_at: datetime
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
