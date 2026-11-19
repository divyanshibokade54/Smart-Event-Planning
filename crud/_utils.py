"""Small shared helpers for CRUD transaction handling."""

from typing import TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


ModelType = TypeVar("ModelType")


def save(db: Session, obj: ModelType, error_message: str) -> ModelType:
    """Add, commit, refresh, and translate integrity errors."""
    try:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(error_message) from exc


def remove(db: Session, obj: ModelType, error_message: str) -> None:
    """Delete an object and translate integrity errors."""
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(error_message) from exc
