"""CRUD operations for specializations, doctors, availability, and allocations."""

from datetime import date, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from crud._utils import remove, save
from database.models import (
    Doctor,
    DoctorAllocation,
    DoctorAvailability,
    MedicalCamp,
    Specialization,
    User,
)


def create_specialization(db: Session, name: str) -> Specialization:
    """Create a specialization."""
    return save(db, Specialization(name=name), "Specialization already exists")


def get_specialization_by_id(db: Session, specialization_id: int) -> Specialization | None:
    """Return one specialization by ID."""
    return db.get(Specialization, specialization_id)


def get_all_specializations(db: Session, name: str | None = None, limit: int = 100, offset: int = 0) -> list[Specialization]:
    """Return specializations with an optional name filter."""
    statement = select(Specialization).order_by(Specialization.name).limit(limit).offset(offset)
    if name:
        statement = statement.where(Specialization.name.ilike(f"%{name}%"))
    return list(db.scalars(statement).all())


def update_specialization(db: Session, specialization_id: int, **changes: object) -> Specialization:
    """Update a specialization."""
    specialization = db.get(Specialization, specialization_id)
    if specialization is None:
        raise ValueError("Specialization not found")
    for field, value in changes.items():
        if hasattr(specialization, field):
            setattr(specialization, field, value)
    return save(db, specialization, "Specialization could not be updated")


def delete_specialization(db: Session, specialization_id: int) -> None:
    """Delete a specialization that is not assigned to a doctor."""
    specialization = db.get(Specialization, specialization_id)
    if specialization is None:
        raise ValueError("Specialization not found")
    remove(db, specialization, "Specialization cannot be deleted while doctors use it")


def create_doctor(
    db: Session,
    full_name: str,
    specialization_id: int,
    qualification: str | None = None,
    experience_years: int = 0,
    phone: str | None = None,
    license_number: str | None = None,
    user_id: int | None = None,
    avg_consultation_minutes: int = 10,
    is_active: bool = True,
) -> Doctor:
    """Create a doctor profile."""
    if db.get(Specialization, specialization_id) is None:
        raise ValueError("Specialization not found")
    if user_id is not None and db.get(User, user_id) is None:
        raise ValueError("User not found")
    if experience_years < 0 or avg_consultation_minutes <= 0:
        raise ValueError("Doctor experience cannot be negative and consultation minutes must be positive")
    doctor = Doctor(
        full_name=full_name,
        specialization_id=specialization_id,
        qualification=qualification,
        experience_years=experience_years,
        phone=phone,
        license_number=license_number,
        user_id=user_id,
        avg_consultation_minutes=avg_consultation_minutes,
        is_active=is_active,
    )
    return save(db, doctor, "Doctor could not be created")


def get_doctor_by_id(db: Session, doctor_id: int) -> Doctor | None:
    """Return one doctor by ID."""
    return db.get(Doctor, doctor_id)


def get_all_doctors(
    db: Session,
    specialization_id: int | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Doctor]:
    """Return doctors with optional specialization and active filters."""
    statement = select(Doctor).order_by(Doctor.full_name).limit(limit).offset(offset)
    if specialization_id is not None:
        statement = statement.where(Doctor.specialization_id == specialization_id)
    if is_active is not None:
        statement = statement.where(Doctor.is_active == is_active)
    return list(db.scalars(statement).all())


def update_doctor(db: Session, doctor_id: int, **changes: object) -> Doctor:
    """Update a doctor profile."""
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise ValueError("Doctor not found")
    if "specialization_id" in changes and db.get(Specialization, int(changes["specialization_id"])) is None:
        raise ValueError("Specialization not found")
    for field, value in changes.items():
        if hasattr(doctor, field):
            setattr(doctor, field, value)
    return save(db, doctor, "Doctor could not be updated")


def delete_doctor(db: Session, doctor_id: int) -> None:
    """Delete a doctor profile."""
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise ValueError("Doctor not found")
    remove(db, doctor, "Doctor could not be deleted")


def create_availability(
    db: Session,
    doctor_id: int,
    available_date: date,
    start_time: time,
    end_time: time,
) -> DoctorAvailability:
    """Create a doctor's available time range."""
    if start_time >= end_time:
        raise ValueError("Availability start time must be before end time")
    if db.get(Doctor, doctor_id) is None:
        raise ValueError("Doctor not found")
    availability = DoctorAvailability(
        doctor_id=doctor_id,
        available_date=available_date,
        start_time=start_time,
        end_time=end_time,
    )
    return save(db, availability, "Doctor availability could not be created")


def get_availability_by_id(db: Session, availability_id: int) -> DoctorAvailability | None:
    """Return one availability record by ID."""
    return db.get(DoctorAvailability, availability_id)


def get_all_availability(
    db: Session,
    doctor_id: int | None = None,
    available_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DoctorAvailability]:
    """Return availability with optional doctor/date filters."""
    statement = select(DoctorAvailability).order_by(DoctorAvailability.available_date).limit(limit).offset(offset)
    if doctor_id is not None:
        statement = statement.where(DoctorAvailability.doctor_id == doctor_id)
    if available_date is not None:
        statement = statement.where(DoctorAvailability.available_date == available_date)
    return list(db.scalars(statement).all())


def update_availability(db: Session, availability_id: int, **changes: object) -> DoctorAvailability:
    """Update an availability record."""
    availability = db.get(DoctorAvailability, availability_id)
    if availability is None:
        raise ValueError("Doctor availability not found")
    start_time = changes.get("start_time", availability.start_time)
    end_time = changes.get("end_time", availability.end_time)
    if start_time >= end_time:
        raise ValueError("Availability start time must be before end time")
    for field, value in changes.items():
        if hasattr(availability, field):
            setattr(availability, field, value)
    return save(db, availability, "Doctor availability could not be updated")


def delete_availability(db: Session, availability_id: int) -> None:
    """Delete an availability record."""
    availability = db.get(DoctorAvailability, availability_id)
    if availability is None:
        raise ValueError("Doctor availability not found")
    remove(db, availability, "Doctor availability could not be deleted")


def create_doctor_allocation(db: Session, doctor_id: int, camp_id: int, room_label: str | None = None) -> DoctorAllocation:
    """Assign a doctor to a camp."""
    if db.get(Doctor, doctor_id) is None:
        raise ValueError("Doctor not found")
    if db.get(MedicalCamp, camp_id) is None:
        raise ValueError("Camp not found")
    allocation = DoctorAllocation(doctor_id=doctor_id, camp_id=camp_id, room_label=room_label)
    return save(db, allocation, "Doctor is already allocated to this camp")


def get_doctor_allocation_by_id(db: Session, allocation_id: int) -> DoctorAllocation | None:
    """Return one doctor allocation by ID."""
    return db.get(DoctorAllocation, allocation_id)


def get_all_doctor_allocations(
    db: Session,
    doctor_id: int | None = None,
    camp_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DoctorAllocation]:
    """Return doctor allocations with optional filters."""
    statement = select(DoctorAllocation).order_by(DoctorAllocation.id).limit(limit).offset(offset)
    if doctor_id is not None:
        statement = statement.where(DoctorAllocation.doctor_id == doctor_id)
    if camp_id is not None:
        statement = statement.where(DoctorAllocation.camp_id == camp_id)
    return list(db.scalars(statement).all())


def update_doctor_allocation(db: Session, allocation_id: int, **changes: object) -> DoctorAllocation:
    """Update a doctor allocation."""
    allocation = db.get(DoctorAllocation, allocation_id)
    if allocation is None:
        raise ValueError("Doctor allocation not found")
    for field, value in changes.items():
        if hasattr(allocation, field):
            setattr(allocation, field, value)
    return save(db, allocation, "Doctor allocation could not be updated")


def delete_doctor_allocation(db: Session, allocation_id: int) -> None:
    """Delete a doctor allocation."""
    allocation = db.get(DoctorAllocation, allocation_id)
    if allocation is None:
        raise ValueError("Doctor allocation not found")
    remove(db, allocation, "Doctor allocation could not be deleted")
