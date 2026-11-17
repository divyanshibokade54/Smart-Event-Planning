# Medical Camp Management Database

Database-only foundation for the **Smart Event Planning Platform with Resource Coordination System**, focused on medical camp management.

## Database structure

- `users`: coordinators, doctors, volunteers, and administrators
- `locations`: places where camps are conducted
- `medical_camps`: camp schedule, capacity, and status
- `resources`: medicines, equipment, staff, and logistics inventory
- `resource_allocations`: resources assigned to a camp
- `patient_registrations`: patients registered for a camp

The SQLAlchemy ORM definitions are in `database/models.py`. The connection and session configuration are in `database/connection.py`.

## Initialize the database using Command Prompt

```cmd
venv\Scripts\activate
python -m database.init_db
python -m database.seed_data
```

This creates the local SQLite database file `medical_camp.db` and inserts sample medical-camp data. The backend and Streamlit frontend can be added after the database design is approved by your mentor.
