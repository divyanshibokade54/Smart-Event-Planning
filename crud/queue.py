"""Basic CRUD operations for digital queue tokens."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from crud._utils import save
from database.models import (
    MedicalCamp,
    PatientRegistration,
    Token,
    TokenPriority,
    TokenStatus,
)


def create_token(
    db: Session,
    registration_id: int,
    camp_id: int,
    token_number: int,
    priority: TokenPriority = TokenPriority.NORMAL,
    status: TokenStatus = TokenStatus.WAITING,
) -> Token:
    """Create a queue token without smart queue generation."""
    if token_number <= 0:
        raise ValueError("Token number must be greater than zero")
    registration = db.get(PatientRegistration, registration_id)
    if registration is None:
        raise ValueError("Registration not found")
    if registration.camp_id != camp_id:
        raise ValueError("Token camp must match the registration camp")
    if db.get(MedicalCamp, camp_id) is None:
        raise ValueError("Camp not found")
    token = Token(
        registration_id=registration_id,
        camp_id=camp_id,
        token_number=token_number,
        priority=priority,
        status=status,
    )
    return save(db, token, "Token number or registration already exists for this camp")


def get_token_by_id(db: Session, token_id: int) -> Token | None:
    """Return one token by ID."""
    return db.get(Token, token_id)


def get_all_tokens(
    db: Session,
    camp_id: int | None = None,
    status: TokenStatus | None = None,
    priority: TokenPriority | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Token]:
    """Return tokens with optional queue filters and pagination."""
    statement = select(Token).order_by(Token.token_number).limit(limit).offset(offset)
    if camp_id is not None:
        statement = statement.where(Token.camp_id == camp_id)
    if status is not None:
        statement = statement.where(Token.status == status)
    if priority is not None:
        statement = statement.where(Token.priority == priority)
    return list(db.scalars(statement).all())


def update_token(db: Session, token_id: int, **changes: object) -> Token:
    """Update a token's basic status or priority."""
    token = db.get(Token, token_id)
    if token is None:
        raise ValueError("Token not found")
    if "token_number" in changes and int(changes["token_number"]) <= 0:
        raise ValueError("Token number must be greater than zero")
    for field, value in changes.items():
        if hasattr(token, field):
            setattr(token, field, value)
    return save(db, token, "Token could not be updated")
