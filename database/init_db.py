from sqlalchemy import inspect

from database.connection import Base, engine
from database import models  # noqa: F401 - imports models before table creation


EXPECTED_TABLES = {
    "users",
    "locations",
    "medical_camps",
    "patients",
    "patient_registrations",
    "tokens",
    "specializations",
    "doctors",
    "doctor_availability",
    "doctor_allocations",
    "consultations",
    "beds",
    "admissions",
    "resources",
    "resource_allocations",
    "staff",
    "staff_allocations",
    "emergency_alerts",
    "alert_notifications",
}


def initialize_database() -> list[str]:
    """Create missing tables and return the current table names."""
    Base.metadata.create_all(bind=engine)
    return sorted(inspect(engine).get_table_names())


if __name__ == "__main__":
    table_names = initialize_database()
    print(f"Database tables created/verified: {len(table_names)}")
    print("Tables:")
    for table_name in table_names:
        print(f"- {table_name}")

    missing_tables = EXPECTED_TABLES.difference(table_names)
    if missing_tables:
        raise RuntimeError(f"Missing expected tables: {sorted(missing_tables)}")
