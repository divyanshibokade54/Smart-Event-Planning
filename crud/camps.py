"""CRUD operations for locations and medical camps."""

from datetime import date, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crud._utils import remove, save
from database.models import (
    CampStatus,
    Location,
    MedicalCamp,
    PatientRegistration,
    PatientType,
    RegistrationStatus,
    Token,
)


def create_location(db: Session, name: str, address: str, city: str | None = None) -> Location:
    """Create a location."""
    return save(db, Location(name=name, address=address, city=city), "Location could not be created")


def get_location_by_id(db: Session, location_id: int) -> Location | None:
    """Return one location by ID."""
    return db.get(Location, location_id)


def get_all_locations(db: Session, city: str | None = None, limit: int = 100, offset: int = 0) -> list[Location]:
    """Return locations with an optional city filter."""
    statement = select(Location).order_by(Location.name).limit(limit).offset(offset)
    if city:
        statement = statement.where(Location.city == city)
    return list(db.scalars(statement).all())


def update_location(db: Session, location_id: int, **changes: object) -> Location:
    """Update a location."""
    location = db.get(Location, location_id)
    if location is None:
        raise ValueError("Location not found")
    for field, value in changes.items():
        if hasattr(location, field):
            setattr(location, field, value)
    return save(db, location, "Location could not be updated")


def delete_location(db: Session, location_id: int) -> None:
    """Delete a location that is not used by a camp."""
    location = db.get(Location, location_id)
    if location is None:
        raise ValueError("Location not found")
    remove(db, location, "Location cannot be deleted while camps use it")


def create_camp(
    db: Session,
    name: str,
    camp_date: date,
    location_id: int,
    description: str | None = None,
    start_time: time | None = None,
    end_time: time | None = None,
    capacity: int = 100,
    status: CampStatus = CampStatus.PLANNED,
    created_by: int | None = None,
) -> MedicalCamp:
    """Create a camp after validating its location and capacity."""
    if capacity <= 0:
        raise ValueError("Camp capacity must be greater than zero")
    if db.get(Location, location_id) is None:
        raise ValueError("Location not found")
    camp = MedicalCamp(
        name=name,
        camp_date=camp_date,
        location_id=location_id,
        description=description,
        start_time=start_time,
        end_time=end_time,
        capacity=capacity,
        status=status,
        created_by=created_by,
    )
    return save(db, camp, "Camp could not be created")


def get_camp_by_id(db: Session, camp_id: int) -> MedicalCamp | None:
    """Return one camp by ID."""
    return db.get(MedicalCamp, camp_id)


def get_all_camps(
    db: Session,
    status: CampStatus | None = None,
    location_id: int | None = None,
    camp_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[MedicalCamp]:
    """Return camps with optional filters and pagination."""
    statement = select(MedicalCamp).order_by(MedicalCamp.camp_date).limit(limit).offset(offset)
    if status is not None:
        statement = statement.where(MedicalCamp.status == status)
    if location_id is not None:
        statement = statement.where(MedicalCamp.location_id == location_id)
    if camp_date is not None:
        statement = statement.where(MedicalCamp.camp_date == camp_date)
    return list(db.scalars(statement).all())


def update_camp(db: Session, camp_id: int, **changes: object) -> MedicalCamp:
    """Update a camp and keep capacity above active registrations."""
    camp = db.get(MedicalCamp, camp_id)
    if camp is None:
        raise ValueError("Camp not found")
    if "capacity" in changes:
        capacity = int(changes["capacity"])
        if capacity <= 0:
            raise ValueError("Camp capacity must be greater than zero")
        current_count = db.scalar(
            select(func.count(PatientRegistration.id)).where(
                PatientRegistration.camp_id == camp_id,
                PatientRegistration.status != RegistrationStatus.CANCELLED,
            )
        ) or 0
        if capacity < current_count:
            raise ValueError("Camp capacity cannot be below current registrations")
    for field, value in changes.items():
        if hasattr(camp, field):
            setattr(camp, field, value)
    return save(db, camp, "Camp could not be updated")


def delete_camp(db: Session, camp_id: int) -> None:
    """Delete a camp and its dependent records."""
    camp = db.get(MedicalCamp, camp_id)
    if camp is None:
        raise ValueError("Camp not found")
    remove(db, camp, "Camp could not be deleted")


def get_camp_summary(db: Session, camp_id: int) -> dict[str, int]:
    """Return registration and token counts for a camp."""
    if db.get(MedicalCamp, camp_id) is None:
        raise ValueError("Camp not found")
    base_filter = (
        PatientRegistration.camp_id == camp_id,
        PatientRegistration.status != RegistrationStatus.CANCELLED,
    )
    registrations = db.scalar(select(func.count(PatientRegistration.id)).where(*base_filter)) or 0
    outpatient = db.scalar(
        select(func.count(PatientRegistration.id)).where(
            *base_filter,
            PatientRegistration.patient_type == PatientType.OUTPATIENT,
        )
    ) or 0
    inpatient = db.scalar(
        select(func.count(PatientRegistration.id)).where(
            *base_filter,
            PatientRegistration.patient_type == PatientType.INPATIENT,
        )
    ) or 0
    tokens = db.scalar(select(func.count(Token.id)).where(Token.camp_id == camp_id)) or 0
    return {
        "registrations": int(registrations),
        "outpatient": int(outpatient),
        "inpatient": int(inpatient),
        "tokens": int(tokens),
    }
