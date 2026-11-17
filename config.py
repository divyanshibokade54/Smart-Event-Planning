import os


class Settings:
    """Small database configuration object with no extra dependency."""

    database_url = os.getenv("DATABASE_URL", "sqlite:///./medical_camp.db")


settings = Settings()
