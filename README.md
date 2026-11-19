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

## Phase 1A database schema

The SQLAlchemy model now defines 19 tables covering users, camps, patients, OPD/IPD registration, digital tokens, doctors, care, beds, resources, staff, and emergency alerts.

`python -m database.init_db` creates missing tables and prints the table list. It does not alter columns in an existing SQLite table. Because the existing local database contains the earlier six-table schema, it must be reset after confirming that the data is seed data only.

The reset command asks for the exact confirmation word `RESET`:

```cmd
python -m database.reset_db --seed
```

A backup is stored under `backups/` before schema changes. The backup folder is ignored by Git.

## Phase 1B: CRUD layer and seed data

The CRUD layer is implemented in the `crud/` package. It keeps database operations separate from the user interface and uses SQLAlchemy 2.0 `select()` statements.

Available CRUD modules:

- `crud/camps.py` — locations and medical camps
- `crud/patients.py` — patients and camp registrations
- `crud/doctors.py` — specializations, doctors, availability, and allocations
- `crud/resources.py` — resources, resource allocations, staff, and staff allocations
- `crud/emergency.py` — emergency alerts and notifications
- `crud/queue.py` — basic digital queue tokens
- `crud/care.py` — consultations, beds, and admissions

CRUD operations validate business rules such as camp capacity, duplicate registrations, available resource quantity, and occupied beds. Database constraint errors are rolled back and returned as readable `ValueError` messages.

`database/seed_data.py` creates repeatable demonstration data: 3 locations, 4 camps, 8 doctors, 40 patients, 60 registrations, tokens, consultations, beds, admissions, resources, staff, alerts, notifications, and users. Running the seed script again does not duplicate records.

CRUD tests are located in `tests/test_crud.py` and use an isolated in-memory SQLite database. The current test suite contains 6 passing tests.

## Phase 1C: Streamlit database connection

The Streamlit frontend now reads live data through the CRUD layer.

The home page displays:

- Total camps
- Patients registered
- OPD registrations
- IPD registrations
- Active doctors
- Resources below reorder level
- Open emergency alerts

Available Streamlit pages:

- `pages/1_Camps.py` — create, view, edit, and delete locations and camps
- `pages/2_Patient_Registration.py` — register OPD/IPD patients and manage registrations
- `pages/3_Doctors.py` — manage specializations, doctors, availability, and camp allocations
- `pages/4_Resources.py` — manage inventory, allocations, and low-stock resources

The shared helper in `utils/db_session.py` caches the SQLAlchemy engine with `st.cache_resource` and creates a fresh session for each page run. Streamlit pages do not contain raw SQL or ORM queries.

## Run the Streamlit application

After confirming that the local database contains only seed data, recreate and seed the current schema:

```powershell
.\venv\Scripts\Activate.ps1
python -m database.reset_db --seed
```

When prompted, type `RESET`. Then start Streamlit:

```powershell
python -m streamlit run app.py
```

Open `http://localhost:8501` in a browser.

Expected seeded dashboard values:

```text
Total Camps: 4
Patients Registered: 60
OPD: 50
IPD: 10
Doctors: 8
Low Stock: 2
Open Alerts: 1
```

## Manual Streamlit verification

1. Create, edit, and delete a camp from the Camps page.
2. Register both an outpatient and an inpatient and confirm the registration ID.
3. Add a specialization, doctor, availability record, and camp allocation.
4. Add a resource, verify low-stock highlighting, and allocate it to a camp.
5. Return to the home page and verify that the dashboard values reflect the database changes.
