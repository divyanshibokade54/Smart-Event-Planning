"""CRUD tests using a fresh in-memory SQLite database."""

from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from crud.camps import create_camp, create_location, get_camp_summary, update_camp
from crud.care import create_admission, create_bed
from crud.patients import create_patient, create_registration, delete_patient, update_patient
from crud.resources import create_resource, create_resource_allocation
from database.connection import Base
from database.models import PatientType, ResourceCategory


@pytest.fixture
def db() -> Session:
    """Create a clean SQLite session for one test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    test_session = sessionmaker(bind=test_engine, expire_on_commit=False)
    with test_session() as session:
        yield session
    Base.metadata.drop_all(test_engine)


def make_camp(db: Session, capacity: int = 10):
    """Create a small camp fixture."""
    location = create_location(db, "Test Health Center", "1 Test Road", "Bengaluru")
    return create_camp(db, "Test Medical Camp", date.today(), location.id, capacity=capacity)


def test_duplicate_registration_is_blocked(db: Session):
    camp = make_camp(db)
    patient = create_patient(db, "Asha Rao", "+919999000001", age=30)
    create_registration(db, camp.id, patient.id, PatientType.OUTPATIENT)

    with pytest.raises(ValueError, match="already registered"):
        create_registration(db, camp.id, patient.id, PatientType.OUTPATIENT)


def test_camp_capacity_is_enforced(db: Session):
    camp = make_camp(db, capacity=1)
    first_patient = create_patient(db, "Asha Rao", "+919999000001")
    second_patient = create_patient(db, "Ravi Rao", "+919999000002")
    create_registration(db, camp.id, first_patient.id, PatientType.OUTPATIENT)

    with pytest.raises(ValueError, match="capacity"):
        create_registration(db, camp.id, second_patient.id, PatientType.OUTPATIENT)


def test_negative_stock_is_blocked(db: Session):
    camp = make_camp(db)
    resource = create_resource(db, "Test Gloves", ResourceCategory.MEDICINE, quantity_available=2)

    with pytest.raises(ValueError, match="cannot go below zero"):
        create_resource_allocation(db, camp.id, resource.id, quantity=3)


def test_occupied_bed_is_blocked(db: Session):
    camp = make_camp(db)
    first_patient = create_patient(db, "Asha Rao", "+919999000001")
    second_patient = create_patient(db, "Ravi Rao", "+919999000002")
    first_registration = create_registration(db, camp.id, first_patient.id, PatientType.INPATIENT)
    second_registration = create_registration(db, camp.id, second_patient.id, PatientType.INPATIENT)
    bed = create_bed(db, camp.id, "B-01")
    create_admission(db, first_registration.id, bed.id)

    with pytest.raises(ValueError, match="already occupied"):
        create_admission(db, second_registration.id, bed.id)


def test_update_and_delete_work(db: Session):
    patient = create_patient(db, "Asha Rao", "+919999000001")
    updated = update_patient(db, patient.id, full_name="Asha Sharma")
    assert updated.full_name == "Asha Sharma"

    delete_patient(db, patient.id)
    assert db.get(type(patient), patient.id) is None


def test_camp_update_and_summary_work(db: Session):
    camp = make_camp(db)
    patient = create_patient(db, "Asha Rao", "+919999000001")
    create_registration(db, camp.id, patient.id, PatientType.INPATIENT)
    updated = update_camp(db, camp.id, capacity=20)
    summary = get_camp_summary(db, updated.id)

    assert updated.capacity == 20
    assert summary == {"registrations": 1, "outpatient": 0, "inpatient": 1, "tokens": 0}
