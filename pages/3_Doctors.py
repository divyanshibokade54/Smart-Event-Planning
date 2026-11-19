"""Manage doctor profiles, specializations, availability, and allocations."""

from datetime import date, time

import pandas as pd
import streamlit as st

from crud.camps import get_all_camps
from crud.doctors import (
    create_availability,
    create_doctor,
    create_doctor_allocation,
    create_specialization,
    delete_doctor,
    delete_specialization,
    get_all_doctors,
    get_all_specializations,
    get_all_doctor_allocations,
    update_doctor,
    update_specialization,
)
from utils.db_session import get_session


st.set_page_config(page_title="Medical Camp Management", page_icon="🏥", layout="wide")
st.title("Doctor Management")

db = get_session()
try:
    specializations = get_all_specializations(db)
    camps = get_all_camps(db)
    doctors = get_all_doctors(db)

    st.subheader("Add specialization")
    with st.form("specialization_form"):
        specialization_name = st.text_input("Specialization name")
        add_specialization_clicked = st.form_submit_button("Add specialization")
    if add_specialization_clicked:
        try:
            create_specialization(db, specialization_name)
            st.success("Specialization added successfully.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.dataframe(
        pd.DataFrame([{"ID": item.id, "Name": item.name} for item in specializations]),
        use_container_width=True,
        hide_index=True,
    )
    if specializations:
        specialization_options = {f"{item.name} (ID {item.id})": item.id for item in specializations}
        selected_specialization_label = st.selectbox("Edit or delete specialization", list(specialization_options))
        selected_specialization_id = specialization_options[selected_specialization_label]
        with st.form("edit_specialization_form"):
            edited_specialization_name = st.text_input("Name", value=selected_specialization_label.split(" (ID")[0])
            save_specialization_clicked = st.form_submit_button("Save specialization")
        if save_specialization_clicked:
            try:
                update_specialization(db, selected_specialization_id, name=edited_specialization_name)
                st.success("Specialization updated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Delete selected specialization"):
            try:
                delete_specialization(db, selected_specialization_id)
                st.success("Specialization deleted successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Add doctor")
    if not specializations:
        st.warning("Add a specialization before adding a doctor.")
    else:
        specialization_options = {f"{item.name} (ID {item.id})": item.id for item in specializations}
        with st.form("doctor_form"):
            doctor_name = st.text_input("Doctor full name")
            qualification = st.text_input("Qualification")
            license_number = st.text_input("License number")
            phone = st.text_input("Phone")
            experience_years = st.number_input("Experience years", min_value=0, value=1)
            consultation_minutes = st.number_input("Average consultation minutes", min_value=1, value=10)
            doctor_specialization_label = st.selectbox("Specialization", list(specialization_options))
            add_doctor_clicked = st.form_submit_button("Add doctor")
        if add_doctor_clicked:
            try:
                create_doctor(
                    db,
                    full_name=doctor_name,
                    specialization_id=specialization_options[doctor_specialization_label],
                    qualification=qualification or None,
                    experience_years=experience_years,
                    phone=phone or None,
                    license_number=license_number or None,
                    avg_consultation_minutes=consultation_minutes,
                )
                st.success("Doctor added successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Doctors")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "ID": doctor.id,
                    "Name": doctor.full_name,
                    "Specialization ID": doctor.specialization_id,
                    "Qualification": doctor.qualification,
                    "Active": doctor.is_active,
                }
                for doctor in doctors
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    if doctors:
        doctor_options = {f"{doctor.full_name} (ID {doctor.id})": doctor.id for doctor in doctors}
        selected_doctor_label = st.selectbox("Edit or delete doctor", list(doctor_options))
        selected_doctor_id = doctor_options[selected_doctor_label]
        selected_doctor = next(doctor for doctor in doctors if doctor.id == selected_doctor_id)
        with st.form("edit_doctor_form"):
            edited_doctor_name = st.text_input("Name", value=selected_doctor.full_name)
            edited_doctor_phone = st.text_input("Phone", value=selected_doctor.phone or "")
            edited_doctor_active = st.checkbox("Active", value=selected_doctor.is_active)
            save_doctor_clicked = st.form_submit_button("Save doctor")
        if save_doctor_clicked:
            try:
                update_doctor(db, selected_doctor_id, full_name=edited_doctor_name, phone=edited_doctor_phone or None, is_active=edited_doctor_active)
                st.success("Doctor updated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Delete selected doctor"):
            try:
                delete_doctor(db, selected_doctor_id)
                st.success("Doctor deleted successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Add doctor availability")
    if doctors:
        doctor_options = {f"{doctor.full_name} (ID {doctor.id})": doctor.id for doctor in doctors}
        with st.form("availability_form"):
            availability_doctor = st.selectbox("Doctor", list(doctor_options))
            availability_date = st.date_input("Available date", value=date.today())
            availability_start = st.time_input("Start time", value=time(9, 0))
            availability_end = st.time_input("End time", value=time(13, 0))
            add_availability_clicked = st.form_submit_button("Add availability")
        if add_availability_clicked:
            try:
                create_availability(db, doctor_options[availability_doctor], availability_date, availability_start, availability_end)
                st.success("Availability added successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Allocate doctor to camp")
    if doctors and camps:
        doctor_options = {f"{doctor.full_name} (ID {doctor.id})": doctor.id for doctor in doctors}
        camp_options = {f"{camp.name} (ID {camp.id})": camp.id for camp in camps}
        with st.form("allocation_form"):
            allocation_doctor = st.selectbox("Doctor", list(doctor_options))
            allocation_camp = st.selectbox("Camp", list(camp_options))
            room_label = st.text_input("Room label")
            allocate_clicked = st.form_submit_button("Allocate doctor")
        if allocate_clicked:
            try:
                create_doctor_allocation(db, doctor_options[allocation_doctor], camp_options[allocation_camp], room_label or None)
                st.success("Doctor allocated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    allocations = get_all_doctor_allocations(db)
    st.subheader("Doctor allocations")
    st.dataframe(
        pd.DataFrame([{"ID": item.id, "Doctor ID": item.doctor_id, "Camp ID": item.camp_id, "Room": item.room_label} for item in allocations]),
        use_container_width=True,
        hide_index=True,
    )
finally:
    db.close()
