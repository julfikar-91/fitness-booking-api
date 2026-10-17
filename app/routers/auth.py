from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import User
from app.schemas import (
    UserSignUp,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest
)
from app.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.config import settings
from app.utils.logging import logger

router = APIRouter(tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new user account with name, unique email, and secure password."
)
def signup(payload: UserSignUp, db: Session = Depends(get_db)):
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        logger.warning(f"Signup attempt with existing email: {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    hashed_pw = get_password_hash(payload.password)
    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=hashed_pw
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(f"IntegrityError on signup: email={payload.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )
    db.refresh(new_user)

    logger.info(f"New user registered successfully: id={new_user.id}, email={new_user.email}")
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticates credentials and returns JWT access and refresh tokens."
)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})

    logger.info(f"User logged in successfully: id={user.id}, email={user.email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
    description="Issue a new access token using a valid refresh token."
)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        token_data = decode_token(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token_data.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with refresh token not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
