"""CRUD operations for resources, staff, and their camp allocations."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from crud._utils import remove, save
from database.models import (
    MedicalCamp,
    Resource,
    ResourceAllocation,
    ResourceCategory,
    Staff,
    StaffAllocation,
)


def create_resource(
    db: Session,
    name: str,
    category: ResourceCategory,
    unit: str = "units",
    quantity_available: int = 0,
    reorder_level: int = 0,
    expiry_date: date | None = None,
) -> Resource:
    """Create a resource and validate its stock quantity."""
    if quantity_available < 0 or reorder_level < 0:
        raise ValueError("Resource quantities cannot be negative")
    resource = Resource(
        name=name,
        category=category,
        unit=unit,
        quantity_available=quantity_available,
        reorder_level=reorder_level,
        expiry_date=expiry_date,
    )
    return save(db, resource, "Resource could not be created")


def get_resource_by_id(db: Session, resource_id: int) -> Resource | None:
    """Return one resource by ID."""
    return db.get(Resource, resource_id)


def get_all_resources(
    db: Session,
    category: ResourceCategory | None = None,
    below_reorder_level: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Resource]:
    """Return resources with optional category and stock filters."""
    statement = select(Resource).order_by(Resource.name).limit(limit).offset(offset)
    if category is not None:
        statement = statement.where(Resource.category == category)
    if below_reorder_level is True:
        statement = statement.where(Resource.quantity_available < Resource.reorder_level)
    elif below_reorder_level is False:
        statement = statement.where(Resource.quantity_available >= Resource.reorder_level)
    return list(db.scalars(statement).all())


def update_resource(db: Session, resource_id: int, **changes: object) -> Resource:
    """Update a resource and prevent negative stock."""
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise ValueError("Resource not found")
    if "quantity_available" in changes and int(changes["quantity_available"]) < 0:
        raise ValueError("Resource quantity_available cannot be negative")
    for field, value in changes.items():
        if hasattr(resource, field):
            setattr(resource, field, value)
    return save(db, resource, "Resource could not be updated")


def delete_resource(db: Session, resource_id: int) -> None:
    """Delete a resource that is not allocated."""
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise ValueError("Resource not found")
    remove(db, resource, "Resource cannot be deleted while allocations exist")


def create_resource_allocation(db: Session, camp_id: int, resource_id: int, quantity: int, notes: str | None = None) -> ResourceAllocation:
    """Allocate stock to a camp and decrease available quantity."""
    if quantity <= 0:
        raise ValueError("Allocation quantity must be greater than zero")
    if db.get(MedicalCamp, camp_id) is None:
        raise ValueError("Camp not found")
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise ValueError("Resource not found")
    if resource.quantity_available < quantity:
        raise ValueError("Resource quantity_available cannot go below zero")
    resource.quantity_available -= quantity
    allocation = ResourceAllocation(camp_id=camp_id, resource_id=resource_id, quantity=quantity, notes=notes)
    return save(db, allocation, "Resource allocation could not be created")


def get_resource_allocation_by_id(db: Session, allocation_id: int) -> ResourceAllocation | None:
    """Return one resource allocation by ID."""
    return db.get(ResourceAllocation, allocation_id)


def get_all_resource_allocations(
    db: Session,
    camp_id: int | None = None,
    resource_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ResourceAllocation]:
    """Return resource allocations with optional filters."""
    statement = select(ResourceAllocation).order_by(ResourceAllocation.allocated_at).limit(limit).offset(offset)
    if camp_id is not None:
        statement = statement.where(ResourceAllocation.camp_id == camp_id)
    if resource_id is not None:
        statement = statement.where(ResourceAllocation.resource_id == resource_id)
    return list(db.scalars(statement).all())


def update_resource_allocation(db: Session, allocation_id: int, **changes: object) -> ResourceAllocation:
    """Update allocation quantity while keeping inventory accurate."""
    allocation = db.get(ResourceAllocation, allocation_id)
    if allocation is None:
        raise ValueError("Resource allocation not found")
    new_quantity = int(changes.get("quantity", allocation.quantity))
    if new_quantity <= 0:
        raise ValueError("Allocation quantity must be greater than zero")
    resource = db.get(Resource, allocation.resource_id)
    if resource is None:
        raise ValueError("Resource not found")
    difference = new_quantity - allocation.quantity
    if difference > resource.quantity_available:
        raise ValueError("Resource quantity_available cannot go below zero")
    resource.quantity_available -= difference
    allocation.quantity = new_quantity
    if "notes" in changes:
        allocation.notes = changes["notes"]
    return save(db, allocation, "Resource allocation could not be updated")


def delete_resource_allocation(db: Session, allocation_id: int) -> None:
    """Delete an allocation and return its quantity to inventory."""
    allocation = db.get(ResourceAllocation, allocation_id)
    if allocation is None:
        raise ValueError("Resource allocation not found")
    resource = db.get(Resource, allocation.resource_id)
    if resource is not None:
        resource.quantity_available += allocation.quantity
    remove(db, allocation, "Resource allocation could not be deleted")


def create_staff(db: Session, full_name: str, role_title: str, phone: str | None = None, is_available: bool = True) -> Staff:
    """Create a non-login staff member."""
    return save(db, Staff(full_name=full_name, role_title=role_title, phone=phone, is_available=is_available), "Staff member could not be created")


def get_staff_by_id(db: Session, staff_id: int) -> Staff | None:
    """Return one staff member by ID."""
    return db.get(Staff, staff_id)


def get_all_staff(db: Session, is_available: bool | None = None, limit: int = 100, offset: int = 0) -> list[Staff]:
    """Return staff with an optional availability filter."""
    statement = select(Staff).order_by(Staff.full_name).limit(limit).offset(offset)
    if is_available is not None:
        statement = statement.where(Staff.is_available == is_available)
    return list(db.scalars(statement).all())


def update_staff(db: Session, staff_id: int, **changes: object) -> Staff:
    """Update a staff member."""
    staff = db.get(Staff, staff_id)
    if staff is None:
        raise ValueError("Staff member not found")
    for field, value in changes.items():
        if hasattr(staff, field):
            setattr(staff, field, value)
    return save(db, staff, "Staff member could not be updated")


def delete_staff(db: Session, staff_id: int) -> None:
    """Delete a staff member."""
    staff = db.get(Staff, staff_id)
    if staff is None:
        raise ValueError("Staff member not found")
    remove(db, staff, "Staff member cannot be deleted while allocations exist")


def create_staff_allocation(db: Session, staff_id: int, camp_id: int, duty_role: str) -> StaffAllocation:
    """Assign available staff to a camp."""
    staff = db.get(Staff, staff_id)
    if staff is None:
        raise ValueError("Staff member not found")
    if not staff.is_available:
        raise ValueError("Staff member is not available")
    if db.get(MedicalCamp, camp_id) is None:
        raise ValueError("Camp not found")
    allocation = StaffAllocation(staff_id=staff_id, camp_id=camp_id, duty_role=duty_role)
    return save(db, allocation, "Staff member is already allocated to this camp")


def get_staff_allocation_by_id(db: Session, allocation_id: int) -> StaffAllocation | None:
    """Return one staff allocation by ID."""
    return db.get(StaffAllocation, allocation_id)


def get_all_staff_allocations(
    db: Session,
    staff_id: int | None = None,
    camp_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[StaffAllocation]:
    """Return staff allocations with optional filters."""
    statement = select(StaffAllocation).order_by(StaffAllocation.id).limit(limit).offset(offset)
    if staff_id is not None:
        statement = statement.where(StaffAllocation.staff_id == staff_id)
    if camp_id is not None:
        statement = statement.where(StaffAllocation.camp_id == camp_id)
    return list(db.scalars(statement).all())


def update_staff_allocation(db: Session, allocation_id: int, **changes: object) -> StaffAllocation:
    """Update a staff allocation."""
    allocation = db.get(StaffAllocation, allocation_id)
    if allocation is None:
        raise ValueError("Staff allocation not found")
    for field, value in changes.items():
        if hasattr(allocation, field):
            setattr(allocation, field, value)
    return save(db, allocation, "Staff allocation could not be updated")


def delete_staff_allocation(db: Session, allocation_id: int) -> None:
    """Delete a staff allocation."""
    allocation = db.get(StaffAllocation, allocation_id)
    if allocation is None:
        raise ValueError("Staff allocation not found")
    remove(db, allocation, "Staff allocation could not be deleted")
