import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routers import auth, classes, bookings
from app.utils.logging import logger
from app.utils.timezone import get_current_ist_time


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to initialize DB tables on startup."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration, authentication, JWT tokens, and token refresh."
        },
        {
            "name": "Fitness Classes",
            "description": "Create and explore upcoming fitness classes with IST timezone support."
        },
        {
            "name": "Bookings",
            "description": "Reserve slots in fitness classes with atomic overbooking and duplicate prevention."
        },
        {
            "name": "Health",
            "description": "System health and timezone status."
        }
    ]
)

# CORS Middleware (allow_credentials=False for security when using wildcard origins and Bearer tokens)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging & Performance Middleware
@app.middleware("http")
async def log_requests_and_timing(request: Request, call_next):
    start_time = time.perf_counter()
    logger.info(f"Incoming request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception during {request.method} {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."}
        )

    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    logger.info(f"Completed {request.method} {request.url.path} with status {response.status_code} in {process_time:.2f}ms")
    return response


# Validation Error Handler for cleaner missing/invalid field error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field_loc = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        errors.append({
            "field": field_loc or "body",
            "message": err.get("msg"),
            "type": err.get("type")
        })

    logger.warning(f"Validation error on {request.method} {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed. Please check the provided fields.",
            "errors": errors
        }
    )


# Include Routers
app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(bookings.router)


@app.get("/", tags=["Health"], summary="API Root & Health Check")
def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "current_time_ist": get_current_ist_time().isoformat(),
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
