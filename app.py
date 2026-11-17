import streamlit as st

st.title("Smart Event Planning System")

st.subheader("Welcome to Event Management")

st.write("Manage events, resources and participants.")

st.metric("Total Events", 5)
st.metric("Registered Participants", 500)


def main():
    if not st.session_state.get("logged_in", False):
        render_login_page()
        return

    current_role = st.session_state.get("role", UserRole.ATTENDEE)
    user_name = st.session_state.get("full_name", "User")
    username = st.session_state.get("username", "")
