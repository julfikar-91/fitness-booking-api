"""
Seed script to populate initial sample users, classes, and bookings for the Fitness Booking API.
Run via: python seed.py
"""
import sys
from datetime import timedelta
from app.database import SessionLocal, engine, Base
from app.models import User, FitnessClass, Booking
from app.security import get_password_hash
from app.utils.timezone import get_current_ist_time
from app.utils.logging import logger


def seed_database():
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_user = db.query(User).filter(User.email == "john@fitness.com").first()
        if existing_user:
            logger.info("Database appears to be already seeded. Skipping seed.")
            print("\nDatabase is already seeded with initial data.")
            print("Credentials:")
            print("  Instructor : john@fitness.com / Password123!")
            print("  Client 1   : alice@example.com / Password123!")
            print("  Client 2   : bob@example.com / Password123!")
            return

        logger.info("Seeding initial users...")
        instructor = User(
            name="John Doe",
            email="john@fitness.com",
            hashed_password=get_password_hash("Password123!")
        )
        alice = User(
            name="Alice Walker",
            email="alice@example.com",
            hashed_password=get_password_hash("Password123!")
        )
        bob = User(
            name="Bob Smith",
            email="bob@example.com",
            hashed_password=get_password_hash("Password123!")
        )

        db.add_all([instructor, alice, bob])
        db.commit()
        db.refresh(instructor)
        db.refresh(alice)
        db.refresh(bob)

        logger.info("Seeding upcoming fitness classes (all stored in IST)...")
        now_ist = get_current_ist_time()

        classes = [
            FitnessClass(
                name="Yoga Flow & Mindfulness",
                date_time=now_ist + timedelta(days=1, hours=2),
                instructor="John Doe",
                total_slots=20,
                available_slots=19,  # 1 booked by Alice below
                created_by=instructor.id
            ),
            FitnessClass(
                name="High-Intensity Interval Training (HIIT)",
                date_time=now_ist + timedelta(days=2, hours=3),
                instructor="Jane Smith",
                total_slots=15,
                available_slots=14,  # 1 booked by Bob below
                created_by=instructor.id
            ),
            FitnessClass(
                name="Zumba Dance Workout",
                date_time=now_ist + timedelta(days=3, hours=1),
                instructor="Carlos Gomez",
                total_slots=25,
                available_slots=25,
                created_by=instructor.id
            ),
            FitnessClass(
                name="Pilates Core Strength",
                date_time=now_ist + timedelta(days=4, hours=4),
                instructor="Emily Chen",
                total_slots=10,
                available_slots=10,
                created_by=instructor.id
            ),
            FitnessClass(
                name="Exclusive Spin Workshop (Limited 1 Slot)",
                date_time=now_ist + timedelta(days=5, hours=5),
                instructor="Mike Ross",
                total_slots=1,
                available_slots=1,  # Great for testing overbooking race conditions
                created_by=instructor.id
            ),
            FitnessClass(
                name="Power Lifting Bootcamp (Fully Booked)",
                date_time=now_ist + timedelta(days=6, hours=2),
                instructor="Arnold Schwarzenegger",
                total_slots=10,
                available_slots=0,  # Fully booked class (0 slots) to test overbooking rejection
                created_by=instructor.id
            )
        ]

        db.add_all(classes)
        db.commit()
        for c in classes:
            db.refresh(c)

        logger.info("Seeding initial bookings...")
        booking_1 = Booking(
            user_id=alice.id,
            class_id=classes[0].id,
            client_name="Alice Walker",
            client_email="alice@example.com",
            booked_at=now_ist
        )
        booking_2 = Booking(
            user_id=bob.id,
            class_id=classes[1].id,
            client_name="Bob Smith",
            client_email="bob@example.com",
            booked_at=now_ist
        )

        db.add_all([booking_1, booking_2])
        db.commit()

        print("\n" + "="*60)
        print(" SUCCESS: Database successfully seeded with sample data!")
        print("="*60)
        print("\n[Sample Users & Credentials]")
        print("  1. Instructor : john@fitness.com  | Password: Password123!")
        print("  2. Client 1   : alice@example.com | Password: Password123!")
        print("  3. Client 2   : bob@example.com   | Password: Password123!")
        print("\n[Sample Classes Seeded]")
        for c in classes:
            print(f"  • ID {c.id}: {c.name} | Instructor: {c.instructor} | Slots: {c.available_slots}/{c.total_slots} | Time (IST): {c.date_time.strftime('%Y-%m-%d %H:%M %Z')}")
        print("="*60 + "\n")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
