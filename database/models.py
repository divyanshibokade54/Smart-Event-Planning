"""SQLAlchemy ORM models for the Medical Camp Management database."""

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class UserRole(str, Enum):
    """Roles that may log in to the future application."""

    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    COORDINATOR = "COORDINATOR"
    ATTENDEE = "ATTENDEE"


class CampStatus(str, Enum):
    """Lifecycle states for a medical camp."""

    PLANNED = "PLANNED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Gender(str, Enum):
    """Supported patient gender values."""

    FEMALE = "FEMALE"
    MALE = "MALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class PatientType(str, Enum):
    """Whether a patient is treated as an outpatient or inpatient."""

    OUTPATIENT = "OUTPATIENT"
    INPATIENT = "INPATIENT"


class RegistrationStatus(str, Enum):
    """Status of a patient's camp registration."""

    REGISTERED = "REGISTERED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TokenPriority(str, Enum):
    """Priority used by the smart queue."""

    NORMAL = "NORMAL"
    SENIOR = "SENIOR"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class TokenStatus(str, Enum):
    """Lifecycle states for a queue token."""

    WAITING = "WAITING"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class ResourceCategory(str, Enum):
    """Types of resources coordinated by a camp."""

    MEDICINE = "MEDICINE"
    EQUIPMENT = "EQUIPMENT"
    STAFF = "STAFF"
    LOGISTICS = "LOGISTICS"


class EmergencySeverity(str, Enum):
    """Severity levels for emergency alerts."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EmergencyStatus(str, Enum):
    """Lifecycle states for emergency alerts."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class User(Base):
    """A person allowed to log in to the future platform."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.ATTENDEE, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    created_camps: Mapped[list["MedicalCamp"]] = relationship(back_populates="creator")
    doctor_profiles: Mapped[list["Doctor"]] = relationship(back_populates="user")
    raised_alerts: Mapped[list["EmergencyAlert"]] = relationship(back_populates="raised_by_user")
    alert_notifications: Mapped[list["AlertNotification"]] = relationship(back_populates="recipient_user")


class Location(Base):
    """A physical place where one or more camps can be hosted."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)

    camps: Mapped[list["MedicalCamp"]] = relationship(back_populates="location")


class MedicalCamp(Base):
    """A planned, ongoing, completed, or cancelled medical camp."""

    __tablename__ = "medical_camps"
    __table_args__ = (CheckConstraint("capacity > 0", name="ck_medical_camps_capacity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    camp_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[CampStatus] = mapped_column(SqlEnum(CampStatus), default=CampStatus.PLANNED, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    location: Mapped[Location] = relationship(back_populates="camps")
    creator: Mapped[User | None] = relationship(back_populates="created_camps")
    registrations: Mapped[list["PatientRegistration"]] = relationship(back_populates="camp", cascade="all, delete-orphan")
    tokens: Mapped[list["Token"]] = relationship(back_populates="camp", cascade="all, delete-orphan")
    doctor_allocations: Mapped[list["DoctorAllocation"]] = relationship(back_populates="camp", cascade="all, delete-orphan")
    beds: Mapped[list["Bed"]] = relationship(back_populates="camp", cascade="all, delete-orphan")
    resource_allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="camp", cascade="all, delete-orphan")
    staff_allocations: Mapped[list["StaffAllocation"]] = relationship(back_populates="camp", cascade="all, delete-orphan")
    emergency_alerts: Mapped[list["EmergencyAlert"]] = relationship(back_populates="camp", cascade="all, delete-orphan")


class Patient(Base):
    """A person who may register for multiple medical camps."""

    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("full_name", "phone", name="uq_patients_full_name_phone"),
        CheckConstraint("age IS NULL OR (age >= 0 AND age <= 120)", name="ck_patients_age_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30), index=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(SqlEnum(Gender), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(5), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    registrations: Mapped[list["PatientRegistration"]] = relationship(back_populates="patient")


class PatientRegistration(Base):
    """A patient's registration in one specific medical camp."""

    __tablename__ = "patient_registrations"
    __table_args__ = (
        UniqueConstraint("camp_id", "patient_id", name="uq_registration_camp_patient"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    patient_type: Mapped[PatientType] = mapped_column(SqlEnum(PatientType), index=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RegistrationStatus] = mapped_column(SqlEnum(RegistrationStatus), default=RegistrationStatus.REGISTERED, index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    camp: Mapped[MedicalCamp] = relationship(back_populates="registrations")
    patient: Mapped[Patient] = relationship(back_populates="registrations")
    token: Mapped["Token | None"] = relationship(back_populates="registration", uselist=False, cascade="all, delete-orphan")
    consultations: Mapped[list["Consultation"]] = relationship(back_populates="registration", cascade="all, delete-orphan")
    admission: Mapped["Admission | None"] = relationship(back_populates="registration", uselist=False, cascade="all, delete-orphan")


class Token(Base):
    """A digital queue token issued for a camp registration."""

    __tablename__ = "tokens"
    __table_args__ = (
        UniqueConstraint("registration_id", name="uq_tokens_registration_id"),
        UniqueConstraint("camp_id", "token_number", name="uq_tokens_camp_token_number"),
        CheckConstraint("token_number > 0", name="ck_tokens_token_number_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("patient_registrations.id"), unique=True, index=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"), index=True)
    token_number: Mapped[int] = mapped_column(Integer)
    priority: Mapped[TokenPriority] = mapped_column(SqlEnum(TokenPriority), default=TokenPriority.NORMAL, index=True)
    status: Mapped[TokenStatus] = mapped_column(SqlEnum(TokenStatus), default=TokenStatus.WAITING, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    called_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    registration: Mapped[PatientRegistration] = relationship(back_populates="token")
    camp: Mapped[MedicalCamp] = relationship(back_populates="tokens")


class Specialization(Base):
    """A doctor's medical specialization."""

    __tablename__ = "specializations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="specialization")


class Doctor(Base):
    """A doctor profile, optionally linked to a login user."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    specialization_id: Mapped[int] = mapped_column(ForeignKey("specializations.id"), index=True)
    license_number: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(150), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    avg_consultation_minutes: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User | None] = relationship(back_populates="doctor_profiles")
    specialization: Mapped[Specialization] = relationship(back_populates="doctors")
    availability: Mapped[list["DoctorAvailability"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    allocations: Mapped[list["DoctorAllocation"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    consultations: Mapped[list["Consultation"]] = relationship(back_populates="doctor")


class DoctorAvailability(Base):
    """A date and time range when a doctor is available."""

    __tablename__ = "doctor_availability"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    available_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    doctor: Mapped[Doctor] = relationship(back_populates="availability")


class DoctorAllocation(Base):
    """Assignment of one doctor to one camp."""

    __tablename__ = "doctor_allocations"
    __table_args__ = (UniqueConstraint("doctor_id", "camp_id", name="uq_doctor_camp_allocation"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"), index=True)
    room_label: Mapped[str | None] = mapped_column(String(50), nullable=True)

    doctor: Mapped[Doctor] = relationship(back_populates="allocations")
    camp: Mapped[MedicalCamp] = relationship(back_populates="doctor_allocations")


class Consultation(Base):
    """A consultation between a registered patient and a doctor."""

    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("patient_registrations.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescription: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    registration: Mapped[PatientRegistration] = relationship(back_populates="consultations")
    doctor: Mapped[Doctor] = relationship(back_populates="consultations")


class Bed(Base):
    """An inpatient bed available at a camp."""

    __tablename__ = "beds"
    __table_args__ = (UniqueConstraint("camp_id", "bed_number", name="uq_beds_camp_bed_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"), index=True)
    bed_number: Mapped[str] = mapped_column(String(30))
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False)

    camp: Mapped[MedicalCamp] = relationship(back_populates="beds")
    admissions: Mapped[list["Admission"]] = relationship(back_populates="bed")


class Admission(Base):
    """An inpatient admission connected to one registration and bed."""

    __tablename__ = "admissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("patient_registrations.id"), unique=True, index=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), index=True)
    admitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    discharged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    registration: Mapped[PatientRegistration] = relationship(back_populates="admission")
    bed: Mapped[Bed] = relationship(back_populates="admissions")


class Resource(Base):
    """A medicine, equipment item, staff resource, or logistics item."""

    __tablename__ = "resources"
    __table_args__ = (CheckConstraint("quantity_available >= 0", name="ck_resources_quantity_nonnegative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    category: Mapped[ResourceCategory] = mapped_column(SqlEnum(ResourceCategory), index=True)
    unit: Mapped[str] = mapped_column(String(30), default="units")
    quantity_available: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="resource")


class ResourceAllocation(Base):
    """Quantity of one resource assigned to one camp."""

    __tablename__ = "resource_allocations"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_resource_allocations_quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"), index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    allocated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    camp: Mapped[MedicalCamp] = relationship(back_populates="resource_allocations")
    resource: Mapped[Resource] = relationship(back_populates="allocations")


class Staff(Base):
    """A non-login nurse, pharmacist, volunteer, or similar staff member."""

    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    role_title: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    allocations: Mapped[list["StaffAllocation"]] = relationship(back_populates="staff", cascade="all, delete-orphan")


class StaffAllocation(Base):
    """Assignment of one staff member to one camp."""

    __tablename__ = "staff_allocations"
    __table_args__ = (UniqueConstraint("staff_id", "camp_id", name="uq_staff_camp_allocation"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), index=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"), index=True)
    duty_role: Mapped[str] = mapped_column(String(80))

    staff: Mapped[Staff] = relationship(back_populates="allocations")
    camp: Mapped[MedicalCamp] = relationship(back_populates="staff_allocations")


class EmergencyAlert(Base):
    """An emergency alert raised during a camp."""

    __tablename__ = "emergency_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"), index=True)
    raised_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    severity: Mapped[EmergencySeverity] = mapped_column(SqlEnum(EmergencySeverity), default=EmergencySeverity.MEDIUM, index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[EmergencyStatus] = mapped_column(SqlEnum(EmergencyStatus), default=EmergencyStatus.OPEN, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    camp: Mapped[MedicalCamp] = relationship(back_populates="emergency_alerts")
    raised_by_user: Mapped[User | None] = relationship(back_populates="raised_alerts")
    notifications: Mapped[list["AlertNotification"]] = relationship(back_populates="alert", cascade="all, delete-orphan")


class AlertNotification(Base):
    """A notification of an emergency alert sent to a login user."""

    __tablename__ = "alert_notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("emergency_alerts.id"), index=True)
    recipient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    alert: Mapped[EmergencyAlert] = relationship(back_populates="notifications")
    recipient_user: Mapped[User] = relationship(back_populates="alert_notifications")
