"""Create repeatable sample data for local development and demonstrations."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from database.connection import SessionLocal
from database.init_db import initialize_database
from database.models import (
    Admission,
    AlertNotification,
    Bed,
    CampStatus,
    Consultation,
    Doctor,
    DoctorAllocation,
    DoctorAvailability,
    EmergencyAlert,
    EmergencySeverity,
    EmergencyStatus,
    Gender,
    Location,
    MedicalCamp,
    Patient,
    PatientRegistration,
    PatientType,
    RegistrationStatus,
    Resource,
    ResourceAllocation,
    ResourceCategory,
    Specialization,
    Staff,
    StaffAllocation,
    Token,
    TokenPriority,
    TokenStatus,
    User,
    UserRole,
)


def _first(db, model, *conditions):
    """Return the first record matching all conditions."""
    return db.scalar(select(model).where(*conditions))


def _get_or_create(db, model, conditions: tuple, values: dict):
    """Return an existing record or add a new one."""
    record = _first(db, model, *conditions)
    if record is None:
        record = model(**values)
        db.add(record)
        db.flush()
    return record


def _create_availability_if_missing(db, doctor: Doctor, available_date: date, start: time, end: time) -> None:
    """Create one availability row only when it does not exist."""
    existing = _first(
        db,
        DoctorAvailability,
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.available_date == available_date,
        DoctorAvailability.start_time == start,
    )
    if existing is None:
        db.add(
            DoctorAvailability(
                doctor_id=doctor.id,
                available_date=available_date,
                start_time=start,
                end_time=end,
            )
        )


def _create_registration_if_missing(
    db,
    camp: MedicalCamp,
    patient: Patient,
    patient_type: PatientType,
    status: RegistrationStatus,
    symptoms: str,
) -> PatientRegistration:
    """Create one registration for a patient and camp."""
    registration = _first(
        db,
        PatientRegistration,
        PatientRegistration.camp_id == camp.id,
        PatientRegistration.patient_id == patient.id,
    )
    if registration is None:
        registration = PatientRegistration(
            camp_id=camp.id,
            patient_id=patient.id,
            patient_type=patient_type,
            status=status,
            symptoms=symptoms,
        )
        db.add(registration)
        db.flush()
    return registration


def seed() -> None:
    """Insert the complete demonstration dataset without duplicates."""
    initialize_database()

    with SessionLocal() as db:
        today = date.today()

        user_specs = [
            ("Admin User", "admin@medicalcamp.local", UserRole.ADMIN),
            ("Dr. Ananya Rao", "doctor@medicalcamp.local", UserRole.DOCTOR),
            ("Camp Coordinator", "coordinator@medicalcamp.local", UserRole.COORDINATOR),
            ("Camp Attendee", "attendee@medicalcamp.local", UserRole.ATTENDEE),
        ]
        users = {}
        for full_name, email, role in user_specs:
            users[role] = _get_or_create(
                db,
                User,
                (User.email == email,),
                {
                    "full_name": full_name,
                    "email": email,
                    "password_hash": "seeded-demo-password-hash",
                    "role": role,
                    "phone": "+919800000001",
                    "is_active": True,
                },
            )

        location_specs = [
            ("Community Health Center", "12 Main Road", "Bengaluru"),
            ("Rural Primary Health Center", "45 Village Road", "Mysuru"),
            ("City School Hall", "8 Lake View Road", "Mangaluru"),
        ]
        locations = {}
        for name, address, city in location_specs:
            locations[name] = _get_or_create(
                db,
                Location,
                (Location.name == name, Location.address == address),
                {"name": name, "address": address, "city": city},
            )

        camp_specs = [
            ("Community Wellness Camp", locations["Community Health Center"], today + timedelta(days=14), CampStatus.PLANNED),
            ("Women and Child Health Camp", locations["City School Hall"], today, CampStatus.ONGOING),
            ("Rural Health Outreach Camp", locations["Rural Primary Health Center"], today - timedelta(days=7), CampStatus.COMPLETED),
            ("Emergency Relief Camp", locations["Community Health Center"], today + timedelta(days=30), CampStatus.CANCELLED),
        ]
        camps = {}
        for name, location, camp_date, status in camp_specs:
            camps[name] = _get_or_create(
                db,
                MedicalCamp,
                (MedicalCamp.name == name,),
                {
                    "name": name,
                    "description": f"Medical services provided through {name}.",
                    "camp_date": camp_date,
                    "start_time": time(9, 0),
                    "end_time": time(16, 0),
                    "capacity": 100,
                    "status": status,
                    "location_id": location.id,
                    "created_by": users[UserRole.COORDINATOR].id,
                },
            )

        specialization_names = [
            "General Medicine",
            "Pediatrics",
            "Gynecology",
            "Ophthalmology",
            "Dentistry",
            "Dermatology",
        ]
        specializations = {}
        for name in specialization_names:
            specializations[name] = _get_or_create(
                db,
                Specialization,
                (Specialization.name == name,),
                {"name": name},
            )

        doctor_specs = [
            ("Dr. Ananya Rao", "General Medicine", "MBBS", 8, "DL-1001"),
            ("Dr. Vikram Singh", "Pediatrics", "MD Pediatrics", 12, "DL-1002"),
            ("Dr. Meera Nair", "Gynecology", "MBBS, DGO", 10, "DL-1003"),
            ("Dr. Rohan Shah", "Ophthalmology", "MS Ophthalmology", 7, "DL-1004"),
            ("Dr. Kavya Iyer", "Dentistry", "BDS", 6, "DL-1005"),
            ("Dr. Arjun Kapoor", "Dermatology", "MD Dermatology", 9, "DL-1006"),
            ("Dr. Priya Menon", "General Medicine", "MBBS", 5, "DL-1007"),
            ("Dr. Rahul Joshi", "Pediatrics", "DCH", 11, "DL-1008"),
        ]
        doctors = []
        for index, (full_name, specialization, qualification, experience, license_number) in enumerate(doctor_specs):
            doctor = _get_or_create(
                db,
                Doctor,
                (Doctor.license_number == license_number,),
                {
                    "full_name": full_name,
                    "specialization_id": specializations[specialization].id,
                    "qualification": qualification,
                    "experience_years": experience,
                    "phone": f"+9197000000{index + 10:02d}",
                    "license_number": license_number,
                    "user_id": users[UserRole.DOCTOR].id if index == 0 else None,
                    "avg_consultation_minutes": 10,
                    "is_active": True,
                },
            )
            doctors.append(doctor)
            _create_availability_if_missing(db, doctor, camps["Women and Child Health Camp"].camp_date, time(9, 0), time(13, 0))
            _create_availability_if_missing(db, doctor, camps["Community Wellness Camp"].camp_date, time(10, 0), time(15, 0))
            allocation_camp = camps["Women and Child Health Camp"] if index < 4 else camps["Community Wellness Camp"]
            if _first(
                db,
                DoctorAllocation,
                DoctorAllocation.doctor_id == doctor.id,
                DoctorAllocation.camp_id == allocation_camp.id,
            ) is None:
                db.add(DoctorAllocation(doctor_id=doctor.id, camp_id=allocation_camp.id, room_label=f"Room {index + 1}"))

        indian_names = [
            "Aarav Sharma", "Aditi Verma", "Arjun Patel", "Bhavna Joshi", "Chaitanya Rao",
            "Deepa Nair", "Esha Mehta", "Farhan Khan", "Gauri Desai", "Harish Kumar",
            "Ishita Singh", "Jatin Shah", "Kavita Iyer", "Lakshmi Menon", "Manish Gupta",
            "Neha Reddy", "Omkar Kulkarni", "Pooja Mishra", "Qasim Ali", "Riya Kapoor",
            "Sanjay Das", "Tanvi Bhat", "Uday Shetty", "Vaishnavi Naik", "Wasim Ansari",
            "Yamini Sethi", "Zoya Khan", "Abhishek Roy", "Anjali Sinha", "Bharat Yadav",
            "Charu Pillai", "Devendra Pawar", "Ekta Choudhary", "Faisal Ahmed", "Geeta Das",
            "Hemant Joshi", "Ira Banerjee", "Kiran Patil", "Lata Rao", "Mohan Reddy",
        ]
        genders = [Gender.MALE, Gender.FEMALE, Gender.MALE, Gender.FEMALE]
        patients = []
        for index, full_name in enumerate(indian_names):
            patient = _get_or_create(
                db,
                Patient,
                (Patient.full_name == full_name, Patient.phone == f"+91900000{index + 1:04d}"),
                {
                    "full_name": full_name,
                    "phone": f"+91900000{index + 1:04d}",
                    "age": 18 + (index * 3 % 63),
                    "gender": genders[index % len(genders)],
                    "blood_group": ["A+", "B+", "O+", "AB+"][index % 4],
                    "address": f"{index + 1} Main Street, Bengaluru",
                },
            )
            patients.append(patient)

        ongoing_camp = camps["Women and Child Health Camp"]
        completed_camp = camps["Rural Health Outreach Camp"]
        ongoing_registrations = []
        completed_registrations = []
        for index, patient in enumerate(patients):
            patient_type = PatientType.INPATIENT if index < 5 else PatientType.OUTPATIENT
            ongoing_registrations.append(
                _create_registration_if_missing(
                    db,
                    ongoing_camp,
                    patient,
                    patient_type,
                    RegistrationStatus.REGISTERED,
                    "Routine screening and consultation",
                )
            )
        for index, patient in enumerate(patients[:20]):
            patient_type = PatientType.INPATIENT if index < 5 else PatientType.OUTPATIENT
            completed_registrations.append(
                _create_registration_if_missing(
                    db,
                    completed_camp,
                    patient,
                    patient_type,
                    RegistrationStatus.COMPLETED,
                    "Completed community health consultation",
                )
            )

        for index, registration in enumerate(ongoing_registrations):
            if _first(db, Token, Token.registration_id == registration.id) is None:
                priority = TokenPriority.URGENT if index % 10 == 0 else TokenPriority.NORMAL
                status = TokenStatus.COMPLETED if index < 2 else TokenStatus.IN_CONSULTATION if index == 2 else TokenStatus.WAITING
                db.add(
                    Token(
                        registration_id=registration.id,
                        camp_id=ongoing_camp.id,
                        token_number=index + 1,
                        priority=priority,
                        status=status,
                        called_at=datetime.now() if index < 3 else None,
                        completed_at=datetime.now() if index < 2 else None,
                    )
                )

        for index, registration in enumerate(completed_registrations):
            if _first(db, Consultation, Consultation.registration_id == registration.id) is None:
                db.add(
                    Consultation(
                        registration_id=registration.id,
                        doctor_id=doctors[index % len(doctors)].id,
                        diagnosis="Routine health assessment completed",
                        prescription="Follow the prescribed care plan",
                        notes="Seeded consultation record",
                        started_at=datetime.now() - timedelta(days=7),
                        ended_at=datetime.now() - timedelta(days=7),
                    )
                )

        for camp in camps.values():
            for bed_index in range(1, 11):
                _get_or_create(
                    db,
                    Bed,
                    (Bed.camp_id == camp.id, Bed.bed_number == f"B-{bed_index:02d}"),
                    {"camp_id": camp.id, "bed_number": f"B-{bed_index:02d}", "is_occupied": False},
                )

        for index, registration in enumerate(ongoing_registrations[:5]):
            bed = _first(db, Bed, Bed.camp_id == ongoing_camp.id, Bed.bed_number == f"B-{index + 1:02d}")
            admission = _first(db, Admission, Admission.registration_id == registration.id)
            if admission is None:
                db.add(
                    Admission(
                        registration_id=registration.id,
                        bed_id=bed.id,
                        admitted_at=datetime.now(),
                        notes="Seeded observation admission",
                    )
                )
                bed.is_occupied = True

        resource_specs = [
            ("Paracetamol tablets", ResourceCategory.MEDICINE, "strips", 20, 100),
            ("Oral rehydration salts", ResourceCategory.MEDICINE, "packets", 80, 50),
            ("Antibiotic capsules", ResourceCategory.MEDICINE, "strips", 200, 50),
            ("Insulin vials", ResourceCategory.MEDICINE, "vials", 40, 20),
            ("Antiseptic solution", ResourceCategory.MEDICINE, "bottles", 75, 25),
            ("Syringes", ResourceCategory.MEDICINE, "boxes", 80, 100),
            ("Blood pressure monitor", ResourceCategory.EQUIPMENT, "units", 8, 2),
            ("Glucometer", ResourceCategory.EQUIPMENT, "units", 6, 2),
            ("Examination tables", ResourceCategory.EQUIPMENT, "units", 12, 4),
            ("Wheelchairs", ResourceCategory.EQUIPMENT, "units", 5, 1),
            ("First aid kits", ResourceCategory.EQUIPMENT, "kits", 10, 3),
            ("Drinking water cans", ResourceCategory.LOGISTICS, "cans", 30, 10),
            ("Patient files", ResourceCategory.LOGISTICS, "packs", 25, 5),
            ("Registration desks", ResourceCategory.LOGISTICS, "units", 4, 1),
            ("Privacy screens", ResourceCategory.LOGISTICS, "units", 8, 2),
        ]
        resources = []
        for name, category, unit, quantity, reorder_level in resource_specs:
            resources.append(
                _get_or_create(
                    db,
                    Resource,
                    (Resource.name == name,),
                    {
                        "name": name,
                        "category": category,
                        "unit": unit,
                        "quantity_available": quantity,
                        "reorder_level": reorder_level,
                        "expiry_date": today + timedelta(days=180) if category == ResourceCategory.MEDICINE else None,
                    },
                )
            )

        for resource, quantity in [(resources[2], 10), (resources[6], 2), (resources[11], 5), (resources[13], 1)]:
            if _first(
                db,
                ResourceAllocation,
                ResourceAllocation.camp_id == ongoing_camp.id,
                ResourceAllocation.resource_id == resource.id,
            ) is None:
                db.add(
                    ResourceAllocation(
                        camp_id=ongoing_camp.id,
                        resource_id=resource.id,
                        quantity=quantity,
                        notes="Seeded camp allocation",
                    )
                )
                resource.quantity_available -= quantity

        staff_specs = [
            ("Sita Rao", "Nurse"), ("Ramesh Kumar", "Nurse"), ("Anita Das", "Pharmacist"),
            ("Vijay Patil", "Volunteer"), ("Sunita Nair", "Nurse"), ("Mohan Singh", "Volunteer"),
            ("Rekha Shah", "Pharmacist"), ("Arvind Joshi", "Volunteer"), ("Meena Iyer", "Nurse"),
            ("Karthik Menon", "Volunteer"),
        ]
        staff_members = []
        for index, (full_name, role_title) in enumerate(staff_specs):
            staff_members.append(
                _get_or_create(
                    db,
                    Staff,
                    (Staff.full_name == full_name,),
                    {
                        "full_name": full_name,
                        "role_title": role_title,
                        "phone": f"+91880000{index + 1:04d}",
                        "is_available": True,
                    },
                )
            )
        for index, staff in enumerate(staff_members):
            allocation_camp = ongoing_camp if index < 5 else camps["Community Wellness Camp"]
            if _first(
                db,
                StaffAllocation,
                StaffAllocation.staff_id == staff.id,
                StaffAllocation.camp_id == allocation_camp.id,
            ) is None:
                db.add(
                    StaffAllocation(
                        staff_id=staff.id,
                        camp_id=allocation_camp.id,
                        duty_role=staff.role_title,
                    )
                )

        alert_specs = [
            (ongoing_camp, EmergencySeverity.HIGH, "Patient requires urgent medical attention", EmergencyStatus.OPEN),
            (completed_camp, EmergencySeverity.MEDIUM, "Minor equipment issue reported during camp", EmergencyStatus.RESOLVED),
        ]
        for camp, severity, description, status in alert_specs:
            alert = _first(
                db,
                EmergencyAlert,
                EmergencyAlert.camp_id == camp.id,
                EmergencyAlert.description == description,
            )
            if alert is None:
                alert = EmergencyAlert(
                    camp_id=camp.id,
                    raised_by=users[UserRole.COORDINATOR].id,
                    severity=severity,
                    description=description,
                    status=status,
                    resolved_at=datetime.now() if status == EmergencyStatus.RESOLVED else None,
                )
                db.add(alert)
                db.flush()
            for recipient in (users[UserRole.ADMIN], users[UserRole.COORDINATOR]):
                if _first(
                    db,
                    AlertNotification,
                    AlertNotification.alert_id == alert.id,
                    AlertNotification.recipient_user_id == recipient.id,
                ) is None:
                    db.add(AlertNotification(alert_id=alert.id, recipient_user_id=recipient.id))

        db.commit()
        print("Seed data inserted or already present.")


if __name__ == "__main__":
    seed()
