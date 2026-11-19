"""Create and manage medical camps and their locations."""

from datetime import date, time

import pandas as pd
import streamlit as st

from crud.camps import (
    create_camp,
    create_location,
    delete_camp,
    delete_location,
    get_all_camps,
    get_all_locations,
    update_camp,
    update_location,
)
from database.models import CampStatus
from utils.db_session import get_session


st.set_page_config(page_title="Medical Camp Management", page_icon="🏥", layout="wide")
st.title("Camps and Locations")


def camp_rows(camps):
    """Convert camp ORM objects into table rows."""
    return [
        {
            "ID": camp.id,
            "Name": camp.name,
            "Date": camp.camp_date,
            "Status": camp.status.value,
            "Capacity": camp.capacity,
            "Location ID": camp.location_id,
        }
        for camp in camps
    ]


db = get_session()
try:
    locations = get_all_locations(db)
    camps = get_all_camps(db)

    st.subheader("Create location")
    with st.form("create_location_form"):
        location_name = st.text_input("Location name")
        address = st.text_input("Address")
        city = st.text_input("City")
        create_location_clicked = st.form_submit_button("Create location")
    if create_location_clicked:
        try:
            create_location(db, location_name, address, city or None)
            st.success("Location created successfully.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.subheader("Locations")
    st.dataframe(
        pd.DataFrame([{"ID": x.id, "Name": x.name, "Address": x.address, "City": x.city} for x in locations]),
        use_container_width=True,
        hide_index=True,
    )
    if locations:
        selected_location_id = st.selectbox("Edit or delete location", [x.id for x in locations])
        selected_location = next(x for x in locations if x.id == selected_location_id)
        with st.form("edit_location_form"):
            edit_name = st.text_input("Name", value=selected_location.name)
            edit_address = st.text_input("Address", value=selected_location.address)
            edit_city = st.text_input("City", value=selected_location.city or "")
            edit_location_clicked = st.form_submit_button("Save location")
        if edit_location_clicked:
            try:
                update_location(db, selected_location_id, name=edit_name, address=edit_address, city=edit_city or None)
                st.success("Location updated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Delete selected location"):
            try:
                delete_location(db, selected_location_id)
                st.success("Location deleted successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Create medical camp")
    if not locations:
        st.warning("Create a location before creating a camp.")
    else:
        location_options = {f"{x.name} ({x.city or 'city not set'})": x.id for x in locations}
        with st.form("create_camp_form"):
            camp_name = st.text_input("Camp name")
            description = st.text_area("Description")
            camp_date = st.date_input("Camp date", value=date.today())
            start_time = st.time_input("Start time", value=time(9, 0))
            end_time = st.time_input("End time", value=time(16, 0))
            capacity = st.number_input("Patient capacity", min_value=1, value=100)
            camp_status = st.selectbox("Status", list(CampStatus), format_func=lambda item: item.value)
            camp_location_label = st.selectbox("Location", list(location_options))
            create_camp_clicked = st.form_submit_button("Create camp")
        if create_camp_clicked:
            try:
                create_camp(
                    db,
                    name=camp_name,
                    description=description or None,
                    camp_date=camp_date,
                    start_time=start_time,
                    end_time=end_time,
                    capacity=capacity,
                    status=camp_status,
                    location_id=location_options[camp_location_label],
                )
                st.success("Medical camp created successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Medical camps")
    st.dataframe(pd.DataFrame(camp_rows(camps)), use_container_width=True, hide_index=True)
    if camps:
        camp_options = {f"{x.name} (ID {x.id})": x.id for x in camps}
        selected_camp_label = st.selectbox("Edit or delete camp", list(camp_options))
        selected_camp_id = camp_options[selected_camp_label]
        selected_camp = next(x for x in camps if x.id == selected_camp_id)
        with st.form("edit_camp_form"):
            edit_camp_name = st.text_input("Camp name", value=selected_camp.name)
            edit_capacity = st.number_input("Capacity", min_value=1, value=selected_camp.capacity)
            edit_status = st.selectbox(
                "Status",
                list(CampStatus),
                index=list(CampStatus).index(selected_camp.status),
                format_func=lambda item: item.value,
            )
            save_camp_clicked = st.form_submit_button("Save camp")
        if save_camp_clicked:
            try:
                update_camp(db, selected_camp_id, name=edit_camp_name, capacity=edit_capacity, status=edit_status)
                st.success("Camp updated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Delete selected camp"):
            try:
                delete_camp(db, selected_camp_id)
                st.success("Camp deleted successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
finally:
    db.close()
