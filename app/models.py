from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.timezone import get_current_ist_time


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_current_ist_time, nullable=False)

    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    created_classes = relationship("FitnessClass", back_populates="creator")


class FitnessClass(Base):
    __tablename__ = "fitness_classes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    date_time = Column(DateTime(timezone=True), nullable=False, index=True)  # Always stored in IST
    instructor = Column(String(100), nullable=False)
    total_slots = Column(Integer, nullable=False)
    available_slots = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_ist_time, nullable=False)

    creator = relationship("User", back_populates="created_classes")
    bookings = relationship("Booking", back_populates="fitness_class", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("fitness_classes.id"), nullable=False, index=True)
    client_name = Column(String(100), nullable=False)
    client_email = Column(String(255), nullable=False, index=True)
    booked_at = Column(DateTime(timezone=True), default=get_current_ist_time, nullable=False)

    user = relationship("User", back_populates="bookings")
    fitness_class = relationship("FitnessClass", back_populates="bookings")

    # Prevent a client from booking the same class multiple times
    __table_args__ = (
        UniqueConstraint("class_id", "client_email", name="uq_class_client_booking"),
    )
