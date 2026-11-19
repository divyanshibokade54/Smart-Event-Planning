"""CRUD operations for emergency alerts and notifications."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from crud._utils import remove, save
from database.models import (
    AlertNotification,
    EmergencyAlert,
    EmergencySeverity,
    EmergencyStatus,
    MedicalCamp,
    User,
)


def create_alert(
    db: Session,
    camp_id: int,
    description: str,
    severity: EmergencySeverity = EmergencySeverity.MEDIUM,
    raised_by: int | None = None,
    status: EmergencyStatus = EmergencyStatus.OPEN,
) -> EmergencyAlert:
    """Create an emergency alert."""
    if db.get(MedicalCamp, camp_id) is None:
        raise ValueError("Camp not found")
    if raised_by is not None and db.get(User, raised_by) is None:
        raise ValueError("Raising user not found")
    alert = EmergencyAlert(
        camp_id=camp_id,
        description=description,
        severity=severity,
        raised_by=raised_by,
        status=status,
    )
    return save(db, alert, "Emergency alert could not be created")


def get_alert_by_id(db: Session, alert_id: int) -> EmergencyAlert | None:
    """Return one emergency alert by ID."""
    return db.get(EmergencyAlert, alert_id)


def get_all_alerts(
    db: Session,
    camp_id: int | None = None,
    severity: EmergencySeverity | None = None,
    status: EmergencyStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[EmergencyAlert]:
    """Return alerts with optional filters and pagination."""
    statement = select(EmergencyAlert).order_by(EmergencyAlert.created_at.desc()).limit(limit).offset(offset)
    if camp_id is not None:
        statement = statement.where(EmergencyAlert.camp_id == camp_id)
    if severity is not None:
        statement = statement.where(EmergencyAlert.severity == severity)
    if status is not None:
        statement = statement.where(EmergencyAlert.status == status)
    return list(db.scalars(statement).all())


def update_alert(db: Session, alert_id: int, **changes: object) -> EmergencyAlert:
    """Update an emergency alert."""
    alert = db.get(EmergencyAlert, alert_id)
    if alert is None:
        raise ValueError("Emergency alert not found")
    for field, value in changes.items():
        if hasattr(alert, field):
            setattr(alert, field, value)
    return save(db, alert, "Emergency alert could not be updated")


def delete_alert(db: Session, alert_id: int) -> None:
    """Delete an emergency alert and its notifications."""
    alert = db.get(EmergencyAlert, alert_id)
    if alert is None:
        raise ValueError("Emergency alert not found")
    remove(db, alert, "Emergency alert could not be deleted")


def create_notification(db: Session, alert_id: int, recipient_user_id: int, is_read: bool = False) -> AlertNotification:
    """Create an alert notification for a login user."""
    if db.get(EmergencyAlert, alert_id) is None:
        raise ValueError("Emergency alert not found")
    if db.get(User, recipient_user_id) is None:
        raise ValueError("Notification recipient not found")
    notification = AlertNotification(
        alert_id=alert_id,
        recipient_user_id=recipient_user_id,
        is_read=is_read,
    )
    return save(db, notification, "Alert notification could not be created")


def get_notification_by_id(db: Session, notification_id: int) -> AlertNotification | None:
    """Return one notification by ID."""
    return db.get(AlertNotification, notification_id)


def get_all_notifications(
    db: Session,
    alert_id: int | None = None,
    recipient_user_id: int | None = None,
    is_read: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AlertNotification]:
    """Return notifications with optional filters and pagination."""
    statement = select(AlertNotification).order_by(AlertNotification.sent_at.desc()).limit(limit).offset(offset)
    if alert_id is not None:
        statement = statement.where(AlertNotification.alert_id == alert_id)
    if recipient_user_id is not None:
        statement = statement.where(AlertNotification.recipient_user_id == recipient_user_id)
    if is_read is not None:
        statement = statement.where(AlertNotification.is_read == is_read)
    return list(db.scalars(statement).all())


def update_notification(db: Session, notification_id: int, **changes: object) -> AlertNotification:
    """Update a notification."""
    notification = db.get(AlertNotification, notification_id)
    if notification is None:
        raise ValueError("Alert notification not found")
    for field, value in changes.items():
        if hasattr(notification, field):
            setattr(notification, field, value)
    return save(db, notification, "Alert notification could not be updated")


def delete_notification(db: Session, notification_id: int) -> None:
    """Delete a notification."""
    notification = db.get(AlertNotification, notification_id)
    if notification is None:
        raise ValueError("Alert notification not found")
    remove(db, notification, "Alert notification could not be deleted")
