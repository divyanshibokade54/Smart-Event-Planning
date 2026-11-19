"""Insert small, repeatable sample data for local development."""

from datetime import date, timedelta

from sqlalchemy import select

from database.connection import SessionLocal
from database.init_db import initialize_database
from database.models import Location, MedicalCamp, Resource, ResourceCategory


def seed() -> None:
    """Create missing sample records without duplicating existing records."""
    initialize_database()

    with SessionLocal() as db:
        location = db.scalar(
            select(Location).where(
                Location.name == "Community Health Center",
                Location.address == "12 Main Road",
            )
        )
        if location is None:
            location = Location(
                name="Community Health Center",
                address="12 Main Road",
                city="Bengaluru",
            )
            db.add(location)
            db.flush()

        camp = db.scalar(
            select(MedicalCamp).where(MedicalCamp.name == "Community Wellness Camp")
        )
        if camp is None:
            db.add(
                MedicalCamp(
                    name="Community Wellness Camp",
                    description="Free health screening and consultation camp.",
                    camp_date=date.today() + timedelta(days=7),
                    capacity=150,
                    location_id=location.id,
                )
            )

        sample_resources = [
            {
                "name": "Paracetamol tablets",
                "category": ResourceCategory.MEDICINE,
                "unit": "strips",
                "quantity_available": 500,
                "reorder_level": 100,
            },
            {
                "name": "Blood pressure monitor",
                "category": ResourceCategory.EQUIPMENT,
                "unit": "units",
                "quantity_available": 4,
                "reorder_level": 1,
            },
            {
                "name": "Examination tables",
                "category": ResourceCategory.EQUIPMENT,
                "unit": "units",
                "quantity_available": 6,
                "reorder_level": 2,
            },
        ]
        for resource_data in sample_resources:
            resource = db.scalar(
                select(Resource).where(Resource.name == resource_data["name"])
            )
            if resource is None:
                db.add(Resource(**resource_data))

        db.commit()
        print("Seed data inserted or already present.")


if __name__ == "__main__":
    seed()
