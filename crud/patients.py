"""CRUD operations for patients and camp registrations."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from crud._utils import remove, save
from database.models import (
    Gender,
    MedicalCamp,
    Patient,
    PatientRegistration,
    PatientType,
    RegistrationStatus,
)


def create_patient(
    db: Session,
    full_name: str,
    phone: str,
    age: int | None = None,
    gender: Gender | None = None,
    blood_group: str | None = None,
    address: str | None = None,
) -> Patient:
    """Create a patient after validating age."""
    if age is not None and not 0 <= age <= 120:
        raise ValueError("Patient age must be between 0 and 120")
    patient = Patient(
        full_name=full_name,
        phone=phone,
        age=age,
        gender=gender,
        blood_group=blood_group,
        address=address,
    )
    return save(db, patient, "A patient with this name and phone already exists")


def get_patient_by_id(db: Session, patient_id: int) -> Patient | None:
    """Return one patient by ID."""
    return db.get(Patient, patient_id)


def get_all_patients(
    db: Session,
    name: str | None = None,
    phone: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Patient]:
    """Return patients with optional filters and pagination."""
    statement = select(Patient).order_by(Patient.full_name).limit(limit).offset(offset)
    if name:
        statement = statement.where(Patient.full_name.ilike(f"%{name}%"))
    if phone:
        statement = statement.where(Patient.phone.ilike(f"%{phone}%"))
    return list(db.scalars(statement).all())


def search_patients(db: Session, name_or_phone: str, limit: int = 100, offset: int = 0) -> list[Patient]:
    """Search patients by part of their name or phone."""
    value = f"%{name_or_phone}%"
    statement = (
        select(Patient)
        .where(or_(Patient.full_name.ilike(value), Patient.phone.ilike(value)))
        .order_by(Patient.full_name)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def update_patient(db: Session, patient_id: int, **changes: object) -> Patient:
    """Update a patient."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise ValueError("Patient not found")
    if "age" in changes and changes["age"] is not None and not 0 <= int(changes["age"]) <= 120:
        raise ValueError("Patient age must be between 0 and 120")
    for field, value in changes.items():
        if hasattr(patient, field):
            setattr(patient, field, value)
    return save(db, patient, "Patient could not be updated")


def delete_patient(db: Session, patient_id: int) -> None:
    """Delete a patient who has no registrations."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise ValueError("Patient not found")
    remove(db, patient, "Patient cannot be deleted while registrations exist")


def create_registration(
    db: Session,
    camp_id: int,
    patient_id: int,
    patient_type: PatientType,
    symptoms: str | None = None,
    status: RegistrationStatus = RegistrationStatus.REGISTERED,
) -> PatientRegistration:
    """Register a patient while enforcing capacity and uniqueness."""
    camp = db.get(MedicalCamp, camp_id)
    if camp is None:
        raise ValueError("Camp not found")
    if db.get(Patient, patient_id) is None:
        raise ValueError("Patient not found")
    active_count = db.scalar(
        select(func.count(PatientRegistration.id)).where(
            PatientRegistration.camp_id == camp_id,
            PatientRegistration.status != RegistrationStatus.CANCELLED,
        )
    ) or 0
    if active_count >= camp.capacity:
        raise ValueError("Camp capacity has been reached")
    registration = PatientRegistration(
        camp_id=camp_id,
        patient_id=patient_id,
        patient_type=patient_type,
        symptoms=symptoms,
        status=status,
    )
    return save(db, registration, "Patient already registered for this camp")


def get_registration_by_id(db: Session, registration_id: int) -> PatientRegistration | None:
    """Return one registration by ID."""
    return db.get(PatientRegistration, registration_id)


def get_all_registrations(
    db: Session,
    camp_id: int | None = None,
    patient_type: PatientType | None = None,
    status: RegistrationStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PatientRegistration]:
    """Return registrations with optional filters and pagination."""
    statement = select(PatientRegistration).order_by(PatientRegistration.registered_at).limit(limit).offset(offset)
    if camp_id is not None:
        statement = statement.where(PatientRegistration.camp_id == camp_id)
    if patient_type is not None:
        statement = statement.where(PatientRegistration.patient_type == patient_type)
    if status is not None:
        statement = statement.where(PatientRegistration.status == status)
    return list(db.scalars(statement).all())


def update_registration(db: Session, registration_id: int, **changes: object) -> PatientRegistration:
    """Update a registration."""
    registration = db.get(PatientRegistration, registration_id)
    if registration is None:
        raise ValueError("Registration not found")
    for field, value in changes.items():
        if hasattr(registration, field):
            setattr(registration, field, value)
    return save(db, registration, "Registration could not be updated")


def delete_registration(db: Session, registration_id: int) -> None:
    """Delete a registration."""
    registration = db.get(PatientRegistration, registration_id)
    if registration is None:
        raise ValueError("Registration not found")
    remove(db, registration, "Registration could not be deleted")
