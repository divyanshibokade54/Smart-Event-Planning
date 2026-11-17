from database.connection import Base, engine
from database import models  # noqa: F401 - imports models before table creation


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print("Database tables created successfully.")
