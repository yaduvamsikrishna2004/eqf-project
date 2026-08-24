import streamlit as st
import pandas as pd
import plotly.express as px
from services.excel_service import get_incidents, get_resolutions
from config.config import CUSTODIANS


def render_management_dashboard():
    st.title("📊 Management Dashboard")
    st.write("Executive-level view of incident analysis and trends")
    
    # Load data
    incidents_df = get_incidents()
    resolutions_df = get_resolutions()
    
    if incidents_df.empty:
        st.info("No incidents to display yet.")
        return
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        selected_oems = st.multiselect(
            "OEM",
            incidents_df["OEM"].unique(),
            default=incidents_df["OEM"].unique(),
        )
    
    with col2:
        selected_severity = st.multiselect(
            "Severity",
            ["Low", "Medium", "High", "Critical"],
            default=["Low", "Medium", "High", "Critical"],
        )
    
    with col3:
        selected_status = st.multiselect(
            "Status",
            incidents_df["Status"].unique(),
            default=incidents_df["Status"].unique(),
        )
    
    with col4:
        selected_issue_type = st.multiselect(
            "Issue Type",
            ["0 KM", "Field Issue"],
            default=["0 KM", "Field Issue"],
        )
    
    with col5:
        selected_custodians = st.multiselect(
            "Custodian",
            incidents_df["Custodian"].unique(),
            default=incidents_df["Custodian"].unique(),
        )
    
    date_range = st.date_input("Date Range", value=(incidents_df["Date"].min(), incidents_df["Date"].max()), key="date_range")
    
    # Apply filters
    filtered_df = incidents_df.copy()
    filtered_df = filtered_df[
        (filtered_df["OEM"].isin(selected_oems))
        & (filtered_df["Severity"].isin(selected_severity))
        & (filtered_df["Status"].isin(selected_status))
        & (filtered_df["IssueType"].isin(selected_issue_type))
        & (filtered_df["Custodian"].isin(selected_custodians))
        & (pd.to_datetime(filtered_df["Date"]) >= pd.Timestamp(date_range[0]))
        & (pd.to_datetime(filtered_df["Date"]) <= pd.Timestamp(date_range[1]))
    ]
    
    st.divider()
    
    # KPI Cards
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_incidents = len(filtered_df)
    open_incidents = len(filtered_df[filtered_df["Status"] != "Closed"])
    closed_incidents = len(filtered_df[filtered_df["Status"] == "Closed"])
    critical_incidents = len(filtered_df[filtered_df["Severity"] == "Critical"])
    
    # Calculate average resolution time
    merged_df = filtered_df.merge(resolutions_df, on="IncidentID", how="left")
    avg_resolution_time = 0
    if not merged_df.empty and merged_df["ResolutionDate"].notna().any():
        merged_df["CreatedAt_dt"] = pd.to_datetime(merged_df["CreatedAt"], errors="coerce")
        merged_df["ResolutionDate_dt"] = pd.to_datetime(merged_df["ResolutionDate"], errors="coerce")
        resolution_times = (merged_df["ResolutionDate_dt"] - merged_df["CreatedAt_dt"]).dt.days
        avg_resolution_time = int(resolution_times.mean()) if not resolution_times.empty else 0
    
    overdue_count = 0  # Placeholder; implement overdue logic as needed
    
    with col1:
        st.metric("Total Incidents", total_incidents)
    with col2:
        st.metric("Open Incidents", open_incidents)
    with col3:
        st.metric("Closed Incidents", closed_incidents)
    with col4:
        st.metric("Critical Incidents", critical_incidents)
    with col5:
        st.metric("Avg Resolution (days)", avg_resolution_time)
    with col6:
        st.metric("Overdue", overdue_count)
    
    st.divider()
    
    # Charts
    st.subheader("Analytics Charts")
    
    col1, col2 = st.columns(2)
    
    # Chart 1: OEM Wise Incidents (Bar)
    with col1:
        oem_counts = filtered_df["OEM"].value_counts().reset_index()
        oem_counts.columns = ["OEM", "Count"]
        fig_oem = px.bar(oem_counts, x="OEM", y="Count", title="OEM Wise Incidents", color="Count")
        st.plotly_chart(fig_oem, use_container_width=True)
    
    # Chart 2: Severity Distribution (Donut)
    with col2:
        severity_counts = filtered_df["Severity"].value_counts().reset_index()
        severity_counts.columns = ["Severity", "Count"]
        fig_severity = px.pie(severity_counts, values="Count", names="Severity", hole=0.3, title="Severity Distribution")
        st.plotly_chart(fig_severity, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    # Chart 3: Status Distribution (Pie)
    with col1:
        status_counts = filtered_df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_status = px.pie(status_counts, values="Count", names="Status", title="Status Distribution")
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Chart 4: Issue Type Distribution (Bar)
    with col2:
        issue_counts = filtered_df["IssueType"].value_counts().reset_index()
        issue_counts.columns = ["IssueType", "Count"]
        fig_issue = px.bar(issue_counts, x="IssueType", y="Count", title="Issue Type Distribution", color="Count")
        st.plotly_chart(fig_issue, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    # Chart 5: Monthly Incident Trend (Line)
    with col1:
        filtered_df["YearMonth"] = pd.to_datetime(filtered_df["Date"]).dt.to_period("M").astype(str)
        monthly_counts = filtered_df.groupby("YearMonth").size().reset_index(name="Count")
        fig_monthly = px.line(monthly_counts, x="YearMonth", y="Count", title="Monthly Incident Trend", markers=True)
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Chart 6: Custodian Workload (Bar)
    with col2:
        custodian_counts = filtered_df["Custodian"].value_counts().reset_index()
        custodian_counts.columns = ["Custodian", "Count"]
        fig_custodian = px.bar(custodian_counts, x="Custodian", y="Count", title="Custodian Workload", color="Count")
        st.plotly_chart(fig_custodian, use_container_width=True)
    
    # Chart 7: Custodian Resolution Performance
    st.subheader("Custodian Resolution Performance")
    custodian_perf = []
    for custodian in filtered_df["Custodian"].unique():
        custodian_data = filtered_df[filtered_df["Custodian"] == custodian]
        total = len(custodian_data)
        closed = len(custodian_data[custodian_data["Status"] == "Closed"])
        resolution_rate = (closed / total * 100) if total > 0 else 0
        custodian_perf.append({"Custodian": custodian, "Resolution Rate (%)": resolution_rate})
    
    perf_df = pd.DataFrame(custodian_perf)
    fig_perf = px.bar(perf_df, x="Custodian", y="Resolution Rate (%)", title="Custodian Resolution Performance", color="Resolution Rate (%)")
    st.plotly_chart(fig_perf, use_container_width=True)
