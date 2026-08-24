import streamlit as st
from datetime import date
from services.excel_service import generate_incident_id, create_incident
from utils.validators import validate_incident_payload
from config.config import CUSTODIANS


def render_incident_reporting():
    st.title("📝 Incident Reporting")
    st.write("Create a new EFQ incident")
    
    with st.form("incident_form", clear_on_submit=False):
        # Read-only Incident ID
        incident_id = generate_incident_id()
        col1, col2 = st.columns([0.3, 0.7])
        with col1:
            st.text_input("Incident ID", value=incident_id, disabled=True)
        
        # Row 1: Date & OEM
        col1, col2 = st.columns(2)
        with col1:
            incident_date = st.date_input("Date", value=date.today())
        with col2:
            oem = st.text_input("OEM")
        
        # Row 2: Vehicle Variant & Vehicle Application
        col1, col2 = st.columns(2)
        with col1:
            vehicle_variant = st.text_input("Vehicle Variant")
        with col2:
            vehicle_application = st.text_input("Vehicle Application")
        
        # Row 3: ECU Part Number & Severity
        col1, col2 = st.columns(2)
        with col1:
            ecu_part_number = st.text_input("ECU Part Number")
        with col2:
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        
        # Row 4: Issue Type & Custodian
        col1, col2 = st.columns(2)
        with col1:
            issue_type = st.selectbox("Issue Type", ["0 KM", "Field Issue"])
        with col2:
            custodian = st.selectbox("Assigned Custodian", CUSTODIANS)
        
        # Dealer Information
        dealer_info = st.text_input("Dealer Information")
        
        # Customer Complaint (mandatory)
        customer_complaint = st.text_area("Customer Complaint", height=80)
        
        # Description
        description = st.text_area("Description", height=80)
        
        # Buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Submit Incident")
        with col2:
            reset = st.form_submit_button("Reset Form")
        
        if reset:
            st.rerun()
        
        if submitted:
            payload = {
                "Date": incident_date,
                "OEM": oem,
                "CustomerComplaint": customer_complaint,
                "DealerInfo": dealer_info,
                "VehicleVariant": vehicle_variant,
                "VehicleApplication": vehicle_application,
                "ECUPartNumber": ecu_part_number,
                "Severity": severity,
                "IssueType": issue_type,
                "Custodian": custodian,
                "Description": description,
                "Status": "New",
            }
            
            missing = validate_incident_payload(payload)
            if missing:
                st.error("Please complete all mandatory fields:\n- " + "\n- ".join(missing))
            else:
                incident_id = create_incident(payload)
                st.success(f"✓ Incident {incident_id} created successfully.")
                st.balloons()
