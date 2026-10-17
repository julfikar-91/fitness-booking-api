from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from app.database import get_db
from app.models import FitnessClass, Booking, User
from app.schemas import BookingCreate, BookingResponse
from app.dependencies import get_current_user
from app.utils.timezone import (
    get_current_ist_time,
    ensure_ist_aware,
    convert_to_timezone
)
from app.utils.logging import logger

router = APIRouter(tags=["Bookings"])


@router.post(
    "/book",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a slot in a class",
    description="Reserve a slot in an upcoming fitness class. Validates slot availability, prevents overbooking, and prevents duplicate bookings."
)
def book_class(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check if class exists
    fitness_class = db.query(FitnessClass).filter(FitnessClass.id == payload.class_id).first()
    if not fitness_class:
        logger.warning(f"Booking attempt failed: class_id={payload.class_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fitness class with ID {payload.class_id} not found."
        )

    # 2. Check if class is in the past
    current_ist = get_current_ist_time()
    class_ist = ensure_ist_aware(fitness_class.date_time)
    if class_ist < current_ist:
        logger.warning(f"Booking attempt failed: class_id={payload.class_id} is in the past.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a class that has already taken place."
        )

    # 3. Check for existing booking (prevent duplicate bookings for same class by this client email)
    clean_email = payload.client_email.lower().strip()
    existing_booking = db.query(Booking).filter(
        Booking.class_id == payload.class_id,
        Booking.client_email == clean_email
    ).first()

    if existing_booking:
        logger.warning(
            f"Duplicate booking attempt: email={clean_email}, class_id={payload.class_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A booking for this class with this email already exists."
        )

    # 4. Atomic slot deduction to strictly prevent race conditions and overbooking
    rows_updated = db.query(FitnessClass).filter(
        FitnessClass.id == payload.class_id,
        FitnessClass.available_slots > 0
    ).update(
        {FitnessClass.available_slots: FitnessClass.available_slots - 1},
        synchronize_session="fetch"
    )

    if rows_updated == 0:
        logger.warning(f"Booking attempt failed: class_id={payload.class_id} has no available slots.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No slots available for this class. Class is fully booked."
        )

    # 5. Record booking
    booking = Booking(
        user_id=current_user.id,
        class_id=fitness_class.id,
        client_name=payload.client_name.strip(),
        client_email=clean_email,
        booked_at=current_ist
    )

    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(
            f"IntegrityError on booking: race condition detected for class_id={payload.class_id}, email={clean_email}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A booking for this class with this email already exists."
        )
    db.refresh(booking)
    db.refresh(fitness_class)

    logger.info(
        f"Slot booked successfully: booking_id={booking.id}, user_id={current_user.id}, "
        f"class_id={fitness_class.id}, remaining_slots={fitness_class.available_slots}"
    )

    return BookingResponse(
        id=booking.id,
        class_id=fitness_class.id,
        class_name=fitness_class.name,
        dateTime=ensure_ist_aware(fitness_class.date_time),
        instructor=fitness_class.instructor,
        client_name=booking.client_name,
        client_email=booking.client_email,
        booked_at=ensure_ist_aware(booking.booked_at),
        message=f"Successfully booked slot in '{fitness_class.name}'. {fitness_class.available_slots} slots remaining."
    )


@router.get(
    "/bookings",
    response_model=List[BookingResponse],
    summary="View user bookings",
    description="Fetch all fitness class bookings made by the currently authenticated user."
)
def get_user_bookings(
    tz: Optional[str] = Query(None, description="Optional target timezone for class times (e.g., 'UTC', 'America/New_York')"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.booked_at.desc())
        .all()
    )

    results: List[BookingResponse] = []
    for b in bookings:
        c = b.fitness_class
        try:
            class_dt = convert_to_timezone(c.date_time, tz)
            booked_dt = convert_to_timezone(b.booked_at, tz)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        results.append(
            BookingResponse(
                id=b.id,
                class_id=c.id,
                class_name=c.name,
                dateTime=class_dt,
                instructor=c.instructor,
                client_name=b.client_name,
                client_email=b.client_email,
                booked_at=booked_dt
            )
        )

    return results
