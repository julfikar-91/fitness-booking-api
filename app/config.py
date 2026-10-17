from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fitness Studio Booking API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "A RESTful Booking API for a fictional fitness studio. "
        "Allows users to register, log in, view/create upcoming classes, "
        "and securely book classes with overbooking prevention and IST timezone management."
    )
    
    # Database
    DATABASE_URL: str = "sqlite:///./fitness_booking.db"
    
    # Security & JWT (Must be provided via environment or .env)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Timezone
    APP_TIMEZONE: str = "Asia/Kolkata"  # IST (UTC+05:30)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
