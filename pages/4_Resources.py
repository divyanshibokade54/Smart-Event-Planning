"""Manage resource inventory and camp allocations."""

import pandas as pd
import streamlit as st

from crud.camps import get_all_camps
from crud.resources import (
    create_resource,
    create_resource_allocation,
    delete_resource,
    get_all_resource_allocations,
    get_all_resources,
    update_resource,
)
from database.models import ResourceCategory
from utils.db_session import get_session


st.set_page_config(page_title="Medical Camp Management", page_icon="🏥", layout="wide")
st.title("Resource Coordination")


def resource_style(row):
    """Highlight resources below their reorder level."""
    color = "background-color: #ffcccc" if row["Low stock"] else ""
    return [color] * len(row)


db = get_session()
try:
    camps = get_all_camps(db)
    resources = get_all_resources(db)

    st.subheader("Add resource")
    with st.form("resource_form"):
        resource_name = st.text_input("Resource name")
        resource_category = st.selectbox("Category", list(ResourceCategory), format_func=lambda item: item.value)
        unit = st.text_input("Unit", value="units")
        quantity_available = st.number_input("Available quantity", min_value=0, value=10)
        reorder_level = st.number_input("Reorder level", min_value=0, value=2)
        expiry_date = st.date_input("Expiry date (optional)", value=None)
        add_resource_clicked = st.form_submit_button("Add resource")
    if add_resource_clicked:
        try:
            create_resource(
                db,
                name=resource_name,
                category=resource_category,
                unit=unit,
                quantity_available=quantity_available,
                reorder_level=reorder_level,
                expiry_date=expiry_date,
            )
            st.success("Resource added successfully.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    resource_rows = [
        {
            "ID": resource.id,
            "Name": resource.name,
            "Category": resource.category.value,
            "Available": resource.quantity_available,
            "Reorder level": resource.reorder_level,
            "Low stock": resource.quantity_available < resource.reorder_level,
        }
        for resource in resources
    ]
    st.subheader("Inventory")
    inventory_df = pd.DataFrame(resource_rows)
    if not inventory_df.empty:
        st.dataframe(inventory_df.style.apply(resource_style, axis=1), use_container_width=True, hide_index=True)
    else:
        st.info("No resources have been added yet.")

    if resources:
        resource_options = {f"{resource.name} (ID {resource.id})": resource.id for resource in resources}
        selected_resource_label = st.selectbox("Edit or delete resource", list(resource_options))
        selected_resource_id = resource_options[selected_resource_label]
        selected_resource = next(resource for resource in resources if resource.id == selected_resource_id)
        with st.form("edit_resource_form"):
            edited_resource_name = st.text_input("Name", value=selected_resource.name)
            edited_quantity = st.number_input("Available quantity", min_value=0, value=selected_resource.quantity_available)
            edited_reorder = st.number_input("Reorder level", min_value=0, value=selected_resource.reorder_level)
            save_resource_clicked = st.form_submit_button("Save resource")
        if save_resource_clicked:
            try:
                update_resource(db, selected_resource_id, name=edited_resource_name, quantity_available=edited_quantity, reorder_level=edited_reorder)
                st.success("Resource updated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Delete selected resource"):
            try:
                delete_resource(db, selected_resource_id)
                st.success("Resource deleted successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Allocate resource to camp")
    if not camps:
        st.warning("Create a camp before allocating resources.")
    elif not resources:
        st.warning("Add a resource before creating an allocation.")
    else:
        camp_options = {f"{camp.name} (ID {camp.id})": camp.id for camp in camps}
        resource_options = {f"{resource.name} (ID {resource.id})": resource.id for resource in resources}
        with st.form("resource_allocation_form"):
            allocation_camp = st.selectbox("Camp", list(camp_options))
            allocation_resource = st.selectbox("Resource", list(resource_options))
            allocation_quantity = st.number_input("Quantity", min_value=1, value=1)
            allocation_notes = st.text_input("Notes")
            allocate_resource_clicked = st.form_submit_button("Allocate resource")
        if allocate_resource_clicked:
            try:
                create_resource_allocation(
                    db,
                    camp_id=camp_options[allocation_camp],
                    resource_id=resource_options[allocation_resource],
                    quantity=allocation_quantity,
                    notes=allocation_notes or None,
                )
                st.success("Resource allocated successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    allocations = get_all_resource_allocations(db)
    st.subheader("Resource allocations")
    st.dataframe(
        pd.DataFrame(
            [{"ID": item.id, "Camp ID": item.camp_id, "Resource ID": item.resource_id, "Quantity": item.quantity, "Notes": item.notes} for item in allocations]
        ),
        use_container_width=True,
        hide_index=True,
    )
finally:
    db.close()
