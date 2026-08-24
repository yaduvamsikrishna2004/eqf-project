import streamlit as st
from config.config import EXCEL_FILE, ROLES
from services.excel_service import initialize_database

# Initialize database (create Excel file & sheets if needed)
try:
    initialize_database()
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    st.stop()

# Page configuration
st.set_page_config(page_title="EFQ Project Dashboard", layout="wide")

# Initialize session state
if "role" not in st.session_state:
    st.session_state.role = "Reporter"
if "username" not in st.session_state:
    st.session_state.username = "Admin"

# Sidebar
st.sidebar.title("EFQ Project Dashboard")

def on_role_change():
    st.session_state.role = st.session_state.role_selector

st.sidebar.selectbox(
    "Select Role",
    ROLES,
    index=ROLES.index(st.session_state.role),
    key="role_selector",
    on_change=on_role_change,
)

st.sidebar.text_input("Current User", value=st.session_state.username, key="username_input")
st.session_state.username = st.session_state.username_input

st.sidebar.markdown(f"**Excel DB:** {EXCEL_FILE}")
st.sidebar.markdown(f"**Role:** {st.session_state.role}")
st.sidebar.markdown(f"**User:** {st.session_state.username}")

# Dynamic module routing based on role
if st.session_state.role == "Reporter":
    from modules import render_incident_reporting
    render_incident_reporting()

elif st.session_state.role == "Custodian":
    from modules import render_custodian_dashboard
    render_custodian_dashboard()

elif st.session_state.role == "Management":
    from modules import render_management_dashboard
    render_management_dashboard()
