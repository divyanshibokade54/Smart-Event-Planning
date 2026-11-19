"""Register patients for OPD or IPD care at a medical camp."""

import pandas as pd
import streamlit as st

from crud.camps import get_all_camps
from crud.patients import (
    create_patient,
    create_registration,
    delete_patient,
    delete_registration,
    get_all_patients,
    get_all_registrations,
    update_patient,
    update_registration,
)
from database.models import Gender, PatientType, RegistrationStatus
from utils.db_session import get_session


st.set_page_config(page_title="Medical Camp Management", page_icon="🏥", layout="wide")
st.title("Patient Registration")

db = get_session()
try:
    camps = get_all_camps(db)
    st.subheader("Register a patient")
    if not camps:
        st.warning("Create a medical camp before registering patients.")
    else:
        camp_options = {f"{camp.name} ({camp.camp_date})": camp.id for camp in camps}
        with st.form("patient_registration_form"):
            full_name = st.text_input("Patient full name")
            phone = st.text_input("Phone number")
            age = st.number_input("Age", min_value=0, max_value=120, value=30)
            gender = st.selectbox("Gender", list(Gender), format_func=lambda item: item.value)
            blood_group = st.text_input("Blood group", placeholder="Example: O+")
            address = st.text_input("Address")
            camp_label = st.selectbox("Medical camp", list(camp_options))
            patient_type = st.selectbox("Patient type", list(PatientType), format_func=lambda item: item.value)
            symptoms = st.text_area("Symptoms")
            register_clicked = st.form_submit_button("Register patient")
        if register_clicked:
            try:
                patient = create_patient(
                    db,
                    full_name=full_name,
                    phone=phone,
                    age=age,
                    gender=gender,
                    blood_group=blood_group or None,
                    address=address or None,
                )
                registration = create_registration(
                    db,
                    camp_id=camp_options[camp_label],
                    patient_id=patient.id,
                    patient_type=patient_type,
                    symptoms=symptoms or None,
                )
                st.success(f"Patient registered successfully. Registration ID: {registration.id}")
            except ValueError as exc:
                st.error(str(exc))

    patients = get_all_patients(db)
    registrations = get_all_registrations(db)
    st.subheader("Patients")
    st.dataframe(
        pd.DataFrame(
            [
                {"ID": patient.id, "Name": patient.full_name, "Phone": patient.phone, "Age": patient.age, "Gender": patient.gender.value if patient.gender else ""}
                for patient in patients
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    if patients:
        patient_options = {f"{patient.full_name} ({patient.phone})": patient.id for patient in patients}
        selected_patient_label = st.selectbox("Edit or delete patient", list(patient_options))
        selected_patient_id = patient_options[selected_patient_label]
        selected_patient = next(patient for patient in patients if patient.id == selected_patient_id)
        with st.form("edit_patient_form"):
            edit_patient_name = st.text_input("Name", value=selected_patient.full_name)
            edit_patient_phone = st.text_input("Phone", value=selected_patient.phone)
            edit_patient_age = st.number_input("Age", min_value=0, max_value=120, value=selected_patient.age or 0)
            save_patient_clicked = st.form_submit_button("Save patient")
        if save_patient_clicked:
            try:
                update_patient(db, selected_patient_id, full_name=edit_patient_name, phone=edit_patient_phone, age=edit_patient_age)
                st.success("Patient updated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Delete selected patient"):
            try:
                delete_patient(db, selected_patient_id)
                st.success("Patient deleted successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Registrations")
    st.dataframe(
        pd.DataFrame(
            [
                {"ID": item.id, "Camp ID": item.camp_id, "Patient ID": item.patient_id, "Type": item.patient_type.value, "Status": item.status.value}
                for item in registrations
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    if registrations:
        registration_options = {f"Registration {item.id} (Patient {item.patient_id})": item.id for item in registrations}
        selected_registration = st.selectbox("Edit or delete registration", list(registration_options))
        selected_registration_id = registration_options[selected_registration]
        with st.form("edit_registration_form"):
            edit_type = st.selectbox("Patient type", list(PatientType), format_func=lambda item: item.value)
            edit_status = st.selectbox("Status", list(RegistrationStatus), format_func=lambda item: item.value)
            save_registration_clicked = st.form_submit_button("Save registration")
        if save_registration_clicked:
            try:
                update_registration(db, selected_registration_id, patient_type=edit_type, status=edit_status)
                st.success("Registration updated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Delete selected registration"):
            try:
                delete_registration(db, selected_registration_id)
                st.success("Registration deleted successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
finally:
    db.close()
