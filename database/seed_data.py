from datetime import date, timedelta

from sqlalchemy import select

from database.connection import SessionLocal
from database.init_db import initialize_database
from database.models import Location, MedicalCamp, Resource, ResourceCategory


def seed() -> None:
    initialize_database()
    with SessionLocal() as db:
        if db.scalar(select(MedicalCamp.id).limit(1)):
            print("Seed data already exists.")
            return

        location = Location(name="Community Health Center", address="12 Main Road", city="Bengaluru")
        db.add(location)
        db.flush()
        db.add(
            MedicalCamp(
                name="Community Wellness Camp",
                description="Free health screening and consultation camp.",
                camp_date=date.today() + timedelta(days=7),
                capacity=150,
                location_id=location.id,
            )
        )
        db.add_all(
            [
                Resource(name="Paracetamol tablets", category=ResourceCategory.MEDICINE, unit="strips", quantity_available=500, reorder_level=100),
                Resource(name="Blood pressure monitor", category=ResourceCategory.EQUIPMENT, unit="units", quantity_available=4, reorder_level=1),
                Resource(name="Examination tables", category=ResourceCategory.EQUIPMENT, unit="units", quantity_available=6, reorder_level=2),
            ]
        )
        db.commit()
        print("Seed data inserted successfully.")


if __name__ == "__main__":
    seed()
