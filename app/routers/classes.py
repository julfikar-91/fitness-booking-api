from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import FitnessClass, User
from app.schemas import ClassCreate, ClassResponse
from app.dependencies import get_current_user
from app.utils.timezone import (
    get_current_ist_time,
    normalize_to_ist,
    ensure_ist_aware,
    convert_to_timezone
)
from app.utils.logging import logger

router = APIRouter(tags=["Fitness Classes"])


@router.post(
    "/classes",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fitness class",
    description="Creates a new class schedule. Class time is converted and stored in IST. Requires authentication."
)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure dateTime is normalized to IST
    ist_datetime = normalize_to_ist(payload.dateTime)

    new_class = FitnessClass(
        name=payload.name.strip(),
        date_time=ist_datetime,
        instructor=payload.instructor.strip(),
        total_slots=payload.availableSlots,
        available_slots=payload.availableSlots,
        created_by=current_user.id
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    logger.info(
        f"Fitness class created: id={new_class.id}, name='{new_class.name}', "
        f"dateTime={new_class.date_time} (IST), slots={new_class.available_slots}, by_user={current_user.id}"
    )

    return ClassResponse(
        id=new_class.id,
        name=new_class.name,
        dateTime=ensure_ist_aware(new_class.date_time),
        instructor=new_class.instructor,
        availableSlots=new_class.available_slots
    )


@router.get(
    "/classes",
    response_model=List[ClassResponse],
    summary="Fetch all upcoming fitness classes",
    description="Fetches upcoming fitness classes. Supports optional timezone conversion query parameter (e.g. ?tz=UTC)."
)
def get_classes(
    upcoming_only: bool = Query(True, description="Filter only classes scheduled for the future"),
    tz: Optional[str] = Query(None, description="Optional target timezone (e.g., 'UTC', 'America/New_York', 'Asia/Kolkata')"),
    db: Session = Depends(get_db)
):
    query = db.query(FitnessClass)

    if upcoming_only:
        current_ist = get_current_ist_time()
        query = query.filter(FitnessClass.date_time >= current_ist)

    # Order by nearest class first
    classes = query.order_by(FitnessClass.date_time.asc()).all()

    response_list: List[ClassResponse] = []
    for c in classes:
        # Convert timezone if requested
        try:
            target_dt = convert_to_timezone(c.date_time, tz)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        response_list.append(
            ClassResponse(
                id=c.id,
                name=c.name,
                dateTime=target_dt,
                instructor=c.instructor,
                availableSlots=c.available_slots
            )
        )

    return response_list
