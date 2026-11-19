"""CRUD operations for consultations, beds, and inpatient admissions."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from crud._utils import remove, save
from database.models import (
    Admission,
    Bed,
    Consultation,
    Doctor,
    MedicalCamp,
    PatientRegistration,
    PatientType,
)


def create_consultation(
    db: Session,
    registration_id: int,
    doctor_id: int,
    diagnosis: str | None = None,
    prescription: str | None = None,
    notes: str | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> Consultation:
    """Create a consultation for a registered patient and doctor."""
    if db.get(PatientRegistration, registration_id) is None:
        raise ValueError("Registration not found")
    if db.get(Doctor, doctor_id) is None:
        raise ValueError("Doctor not found")
    consultation = Consultation(
        registration_id=registration_id,
        doctor_id=doctor_id,
        diagnosis=diagnosis,
        prescription=prescription,
        notes=notes,
        started_at=started_at,
        ended_at=ended_at,
    )
    return save(db, consultation, "Consultation could not be created")


def get_consultation_by_id(db: Session, consultation_id: int) -> Consultation | None:
    """Return one consultation by ID."""
    return db.get(Consultation, consultation_id)


def get_all_consultations(
    db: Session,
    registration_id: int | None = None,
    doctor_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Consultation]:
    """Return consultations with optional registration/doctor filters."""
    statement = select(Consultation).order_by(Consultation.started_at).limit(limit).offset(offset)
    if registration_id is not None:
        statement = statement.where(Consultation.registration_id == registration_id)
    if doctor_id is not None:
        statement = statement.where(Consultation.doctor_id == doctor_id)
    return list(db.scalars(statement).all())


def update_consultation(db: Session, consultation_id: int, **changes: object) -> Consultation:
    """Update a consultation."""
    consultation = db.get(Consultation, consultation_id)
    if consultation is None:
        raise ValueError("Consultation not found")
    for field, value in changes.items():
        if hasattr(consultation, field):
            setattr(consultation, field, value)
    return save(db, consultation, "Consultation could not be updated")


def delete_consultation(db: Session, consultation_id: int) -> None:
    """Delete a consultation."""
    consultation = db.get(Consultation, consultation_id)
    if consultation is None:
        raise ValueError("Consultation not found")
    remove(db, consultation, "Consultation could not be deleted")


def create_bed(db: Session, camp_id: int, bed_number: str, is_occupied: bool = False) -> Bed:
    """Create a bed for a camp."""
    if db.get(MedicalCamp, camp_id) is None:
        raise ValueError("Camp not found")
    bed = Bed(camp_id=camp_id, bed_number=bed_number, is_occupied=is_occupied)
    return save(db, bed, "Bed number already exists for this camp")


def get_bed_by_id(db: Session, bed_id: int) -> Bed | None:
    """Return one bed by ID."""
    return db.get(Bed, bed_id)


def get_all_beds(
    db: Session,
    camp_id: int | None = None,
    is_occupied: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Bed]:
    """Return beds with optional camp/occupancy filters."""
    statement = select(Bed).order_by(Bed.bed_number).limit(limit).offset(offset)
    if camp_id is not None:
        statement = statement.where(Bed.camp_id == camp_id)
    if is_occupied is not None:
        statement = statement.where(Bed.is_occupied == is_occupied)
    return list(db.scalars(statement).all())


def update_bed(db: Session, bed_id: int, **changes: object) -> Bed:
    """Update a bed, without manually occupying it when an admission exists."""
    bed = db.get(Bed, bed_id)
    if bed is None:
        raise ValueError("Bed not found")
    if changes.get("is_occupied") is True and not bed.is_occupied:
        raise ValueError("A bed must be assigned through an admission")
    for field, value in changes.items():
        if hasattr(bed, field):
            setattr(bed, field, value)
    return save(db, bed, "Bed could not be updated")


def delete_bed(db: Session, bed_id: int) -> None:
    """Delete a bed that has no admissions."""
    bed = db.get(Bed, bed_id)
    if bed is None:
        raise ValueError("Bed not found")
    remove(db, bed, "Bed cannot be deleted while admissions exist")


def create_admission(
    db: Session,
    registration_id: int,
    bed_id: int,
    admitted_at: datetime | None = None,
    notes: str | None = None,
) -> Admission:
    """Admit an inpatient registration to an available bed."""
    registration = db.get(PatientRegistration, registration_id)
    if registration is None:
        raise ValueError("Registration not found")
    if registration.patient_type != PatientType.INPATIENT:
        raise ValueError("Only INPATIENT registrations can be admitted")
    bed = db.get(Bed, bed_id)
    if bed is None:
        raise ValueError("Bed not found")
    if bed.camp_id != registration.camp_id:
        raise ValueError("Bed and registration must belong to the same camp")
    if bed.is_occupied:
        raise ValueError("Bed is already occupied")
    if db.scalar(select(Admission.id).where(Admission.registration_id == registration_id)) is not None:
        raise ValueError("This registration already has an admission")
    admission = Admission(
        registration_id=registration_id,
        bed_id=bed_id,
        admitted_at=admitted_at or datetime.now(),
        notes=notes,
    )
    bed.is_occupied = True
    return save(db, admission, "Admission could not be created")


def get_admission_by_id(db: Session, admission_id: int) -> Admission | None:
    """Return one admission by ID."""
    return db.get(Admission, admission_id)


def get_all_admissions(
    db: Session,
    camp_id: int | None = None,
    bed_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Admission]:
    """Return admissions with optional camp/bed filters."""
    statement = select(Admission).join(Admission.registration).order_by(Admission.admitted_at).limit(limit).offset(offset)
    if camp_id is not None:
        statement = statement.where(PatientRegistration.camp_id == camp_id)
    if bed_id is not None:
        statement = statement.where(Admission.bed_id == bed_id)
    return list(db.scalars(statement).all())


def update_admission(db: Session, admission_id: int, **changes: object) -> Admission:
    """Update an admission and release its bed when discharged."""
    admission = db.get(Admission, admission_id)
    if admission is None:
        raise ValueError("Admission not found")
    if "bed_id" in changes and int(changes["bed_id"]) != admission.bed_id:
        raise ValueError("Changing an admission bed is not supported; discharge and create a new admission")
    for field, value in changes.items():
        if hasattr(admission, field):
            setattr(admission, field, value)
    bed = db.get(Bed, admission.bed_id)
    if bed is not None:
        bed.is_occupied = admission.discharged_at is None
    return save(db, admission, "Admission could not be updated")


def delete_admission(db: Session, admission_id: int) -> None:
    """Delete an admission and release its bed."""
    admission = db.get(Admission, admission_id)
    if admission is None:
        raise ValueError("Admission not found")
    bed = db.get(Bed, admission.bed_id)
    if bed is not None:
        bed.is_occupied = False
    remove(db, admission, "Admission could not be deleted")
