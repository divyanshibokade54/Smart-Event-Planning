from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class CampStatus(str, Enum):
    PLANNED = "PLANNED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResourceCategory(str, Enum):
    MEDICINE = "MEDICINE"
    EQUIPMENT = "EQUIPMENT"
    STAFF = "STAFF"
    LOGISTICS = "LOGISTICS"


class RegistrationStatus(str, Enum):
    REGISTERED = "REGISTERED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default="COORDINATOR")
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)

    camps: Mapped[list["MedicalCamp"]] = relationship(back_populates="location")


class MedicalCamp(Base):
    __tablename__ = "medical_camps"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    camp_date: Mapped[date] = mapped_column(Date, index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[CampStatus] = mapped_column(SqlEnum(CampStatus), default=CampStatus.PLANNED)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    location: Mapped[Location] = relationship(back_populates="camps")
    registrations: Mapped[list["PatientRegistration"]] = relationship(back_populates="camp")
    allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="camp")


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    category: Mapped[ResourceCategory] = mapped_column(SqlEnum(ResourceCategory))
    unit: Mapped[str] = mapped_column(String(30), default="units")
    quantity_available: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="resource")


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"))
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    camp: Mapped[MedicalCamp] = relationship(back_populates="allocations")
    resource: Mapped[Resource] = relationship(back_populates="allocations")


class PatientRegistration(Base):
    __tablename__ = "patient_registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    camp_id: Mapped[int] = mapped_column(ForeignKey("medical_camps.id"))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RegistrationStatus] = mapped_column(SqlEnum(RegistrationStatus), default=RegistrationStatus.REGISTERED)
    registered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    camp: Mapped[MedicalCamp] = relationship(back_populates="registrations")
