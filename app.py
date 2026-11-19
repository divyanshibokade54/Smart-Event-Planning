"""Home page for the Medical Camp Management Streamlit application."""

import streamlit as st

from crud.camps import get_all_camps
from crud.doctors import get_all_doctors
from crud.emergency import get_all_alerts
from crud.patients import get_all_registrations
from crud.resources import get_all_resources
from database.models import EmergencyStatus, PatientType
from utils.db_session import get_session


st.set_page_config(page_title="Medical Camp Management", page_icon="🏥", layout="wide")


def load_dashboard_counts() -> dict[str, int]:
    """Read the current dashboard counts from the database."""
    db = get_session()
    try:
        return {
            "camps": len(get_all_camps(db)),
            "registrations": len(get_all_registrations(db)),
            "outpatients": len(get_all_registrations(db, patient_type=PatientType.OUTPATIENT)),
            "inpatients": len(get_all_registrations(db, patient_type=PatientType.INPATIENT)),
            "doctors": len(get_all_doctors(db, is_active=True)),
            "low_stock": len(get_all_resources(db, below_reorder_level=True)),
            "open_alerts": len(get_all_alerts(db, status=EmergencyStatus.OPEN)),
        }
    finally:
        db.close()


st.title("🏥 Medical Camp Management")
st.caption("Smart Event Planning Platform with Resource Coordination System")
st.info("Use the pages in the sidebar to manage camps, patients, doctors, and resources.")

try:
    counts = load_dashboard_counts()
    columns = st.columns(7)
    columns[0].metric("Total Camps", counts["camps"])
    columns[1].metric("Patients Registered", counts["registrations"])
    columns[2].metric("OPD", counts["outpatients"])
    columns[3].metric("IPD", counts["inpatients"])
    columns[4].metric("Doctors", counts["doctors"])
    columns[5].metric("Low Stock", counts["low_stock"])
    columns[6].metric("Open Alerts", counts["open_alerts"])
except Exception as exc:
    st.error(f"The dashboard could not read the database: {exc}")
