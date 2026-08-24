import streamlit as st
from datetime import datetime
from services.excel_service import (
    get_incidents,
    get_incident_by_id,
    update_incident,
    get_activities_by_incident,
    log_activity,
    create_resolution,
    update_resolution,
    get_resolution_by_incident,
    generate_resolution_id,
)


def render_custodian_dashboard():
    st.title("🔍 Custodian Dashboard")
    
    # KPI Cards
    incidents_df = get_incidents()
    if not incidents_df.empty:
        open_count = len(incidents_df[incidents_df["Status"] != "Closed"])
        closed_count = len(incidents_df[incidents_df["Status"] == "Closed"])
        critical_count = len(incidents_df[incidents_df["Severity"] == "Critical"])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("My Open Incidents", open_count)
        with col2:
            st.metric("My Closed Incidents", closed_count)
        with col3:
            st.metric("Critical Items", critical_count)
        with col4:
            st.metric("Total Assigned", len(incidents_df))
    
    st.divider()
    
    # Incident List
    st.subheader("📋 Select Incident to Investigate")
    
    if incidents_df.empty:
        st.info("No incidents assigned to you.")
        return
    
    incident_options = [
        f"[{row['Status']}] {row['IncidentID']} - {row['Severity']} - {row['OEM']}"
        for _, row in incidents_df.iterrows()
    ]
    
    selected_option = st.selectbox("Select incident:", incident_options)
    if not selected_option:
        return
    
    incident_id = selected_option.split(" ")[1]
    incident = get_incident_by_id(incident_id)
    if incident is None:
        st.error("Incident not found.")
        return
    
    # Display Incident Details
    st.subheader(f"Incident: {incident_id}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("OEM", incident["OEM"])
    with col2:
        st.metric("Severity", incident["Severity"])
    with col3:
        st.metric("Status", incident["Status"])
    with col4:
        st.metric("Date", str(incident["Date"]))
    
    st.write(f"**Customer Complaint:** {incident['CustomerComplaint']}")
    st.write(f"**Description:** {incident['Description']}")
    
    st.divider()
    
    # Investigation Form
    st.subheader("🔬 Investigation & Solution")
    
    resolution = get_resolution_by_incident(incident_id)
    is_new_resolution = resolution is None
    
    if resolution is None:
        resolution = {
            "ResolutionID": generate_resolution_id(),
            "IncidentID": incident_id,
            "RootCause": "",
            "InvestigationDetails": "",
            "Recommendation": "",
            "ProposedSolution": "",
            "CorrectiveAction": "",
            "PreventiveAction": "",
            "ValidationMethod": "",
            "ValidationResult": "Not Tested",
            "ResolutionOwner": "",
            "TargetDate": None,
            "ResolutionDate": None,
            "ResolutionStatus": "Not Started",
            "Remarks": "",
        }
    
    with st.form(f"investigation_form_{incident_id}", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Investigation Phase")
            investigation_details = st.text_area(
                "Investigation Details",
                value=resolution.get("InvestigationDetails", ""),
                height=100,
                key=f"investigation_{incident_id}",
            )
            
            root_cause = st.text_area(
                "Root Cause",
                value=resolution.get("RootCause", ""),
                height=100,
                key=f"root_cause_{incident_id}",
            )
        
        with col2:
            st.subheader("Solution Phase")
            recommendation = st.text_area(
                "Recommendation",
                value=resolution.get("Recommendation", ""),
                height=100,
                key=f"rec_{incident_id}",
            )
            
            proposed_solution = st.text_area(
                "Proposed Solution",
                value=resolution.get("ProposedSolution", ""),
                height=100,
                key=f"proposed_{incident_id}",
            )
        
        st.write("---")
        
        # Action Phase
        st.subheader("Action Phase")
        col1, col2 = st.columns(2)
        
        with col1:
            corrective_action = st.text_area(
                "Corrective Action",
                value=resolution.get("CorrectiveAction", ""),
                height=100,
                key=f"corrective_{incident_id}",
            )
        
        with col2:
            preventive_action = st.text_area(
                "Preventive Action",
                value=resolution.get("PreventiveAction", ""),
                height=100,
                key=f"preventive_{incident_id}",
            )
        
        st.write("---")
        
        # Validation Phase
        st.subheader("Validation Phase")
        col1, col2 = st.columns(2)
        
        with col1:
            validation_method = st.text_area(
                "Validation Method",
                value=resolution.get("ValidationMethod", ""),
                height=80,
                key=f"val_method_{incident_id}",
            )
            
            validation_result = st.selectbox(
                "Validation Result",
                ["Not Tested", "Pass", "Fail", "Conditional Pass"],
                index=["Not Tested", "Pass", "Fail", "Conditional Pass"].index(
                    resolution.get("ValidationResult", "Not Tested")
                ),
                key=f"val_result_{incident_id}",
            )
        
        with col2:
            resolution_owner = st.text_input(
                "Resolution Owner",
                value=resolution.get("ResolutionOwner", ""),
                key=f"owner_{incident_id}",
            )
            
            target_date = st.date_input(
                "Target Date",
                value=resolution.get("TargetDate"),
                key=f"target_{incident_id}",
            )
            
            resolution_status = st.selectbox(
                "Resolution Status",
                ["Not Started", "In Progress", "Ready for Validation", "Validated", "Closed"],
                index=["Not Started", "In Progress", "Ready for Validation", "Validated", "Closed"].index(
                    resolution.get("ResolutionStatus", "Not Started")
                ),
                key=f"res_status_{incident_id}",
            )
        
        st.write("---")
        
        remarks = st.text_area(
            "Remarks",
            value=resolution.get("Remarks", ""),
            height=80,
            key=f"remarks_{incident_id}",
        )
        
        # Status Transition Logic
        st.subheader("Status Update")
        col1, col2 = st.columns([0.7, 0.3])
        
        with col1:
            new_status = st.selectbox(
                "Change Incident Status",
                ["New", "Investigation Started", "Root Cause Identified", "Action In Progress", "Validation", "Closed"],
                index=["New", "Investigation Started", "Root Cause Identified", "Action In Progress", "Validation", "Closed"].index(
                    incident.get("Status", "New")
                ),
                key=f"incident_status_{incident_id}",
            )
        
        with col2:
            close_incident = st.checkbox("Mark as Closed", key=f"close_{incident_id}")
        
        # Submit Button
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Investigation & Solution")
        with col2:
            reset = st.form_submit_button("Reset")
        
        if reset:
            st.rerun()
        
        if submitted:
            resolution_data = {
                "RootCause": root_cause,
                "InvestigationDetails": investigation_details,
                "Recommendation": recommendation,
                "ProposedSolution": proposed_solution,
                "CorrectiveAction": corrective_action,
                "PreventiveAction": preventive_action,
                "ValidationMethod": validation_method,
                "ValidationResult": validation_result,
                "ResolutionOwner": resolution_owner,
                "TargetDate": target_date,
                "ResolutionStatus": resolution_status,
                "Remarks": remarks,
            }
            
            # Save resolution
            if is_new_resolution:
                create_resolution(incident_id, resolution_data)
                log_activity(incident_id, "Resolution Created", st.session_state.get("username", "Unknown"))
            else:
                update_resolution(incident_id, resolution_data)
                log_activity(incident_id, "Resolution Updated", st.session_state.get("username", "Unknown"))
            
            # Update incident status
            if close_incident and new_status == "Closed":
                incident["Status"] = "Closed"
                incident["ResolutionDate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_activity(incident_id, "Status Changed to Closed", st.session_state.get("username", "Unknown"))
            else:
                incident["Status"] = new_status
                log_activity(incident_id, f"Status Changed to {new_status}", st.session_state.get("username", "Unknown"))
            
            update_incident(incident_id, incident)
            st.success("✓ Investigation & solution saved successfully.")
            st.rerun()
    
    # Activity History Expander
    st.write("---")
    with st.expander("📅 Activity History"):
        activities = get_activities_by_incident(incident_id)
        if activities.empty:
            st.info("No activities recorded yet.")
        else:
            for _, activity in activities.iterrows():
                st.write(f"**{activity['Timestamp']}** - {activity['Action']}")
                st.caption(f"User: {activity['User']}")
                st.write("")
