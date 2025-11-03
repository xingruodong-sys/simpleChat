import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Naiser-T3000 Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Data Loading Function ---
API_URL = "http://127.0.0.1:8001/api/dashboard/tasks"

@st.cache_data(ttl=30)  # Cache data for 30 seconds
def load_data():
    """Fetches task data from the backend API."""
    
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        print(data)
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return pd.DataFrame() # Return empty dataframe on error

# --- Helper Functions ---
def format_status(status_code):
    """Maps status code to a descriptive string and emoji."""
    status_map = {
        0: "🆕 New", 1: "⏳ Pending", 2: "🧠 BERT", 3: "🤖 LLM",
        4: "🛠️ Tool", 5: "↪️ Not Analyzed", 6: "🚫 N/A",
        98: "🔥 Exception", 99: "✅ Done"
    }
    return status_map.get(status_code, "❓ Unknown")

def format_timedelta(seconds):
    """Formats seconds into a human-readable string like 1m 23s."""
    if seconds < 0 or pd.isna(seconds):
        return "-"
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}m {seconds}s"

# --- Main Application ---
st.title("📊 Naiser-T3000 Task Dashboard")
st.markdown("Real-time overview of all AI analysis tasks.")

# Load data
df = load_data()

if df.empty:
    st.info("No active tasks found or unable to connect to the backend.")
else:
    # --- KPI Metrics ---
    st.header("System Health at a Glance", divider='blue')
    total_tasks = len(df)
    in_progress_tasks = len(df[df['status'].isin([1, 2, 3, 4])])
    exception_tasks = len(df[df['status'] == 98])

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Total Active Tasks", value=total_tasks)
    kpi2.metric(label="Tasks In Progress", value=in_progress_tasks)
    kpi3.metric(label="Tasks with Exceptions", value=exception_tasks)

    # --- Task Overview Table ---
    st.header("Active Task Details", divider='blue')

    # Create a display dataframe with formatted columns
    df_display = pd.DataFrame()
    df_display['ID'] = df['id']
    df_display['Status'] = df['status'].apply(format_status)
    df_display['Created At'] = pd.to_datetime(df['created_at'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate total processing time
    end_times = df[['bertEnd', 'llmEnd', 'analyzeEnd']].max(axis=1)
    df_display['Processing Time'] = (end_times - df['created_at']).apply(format_timedelta)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- Task Drill-Down Section ---
    st.header("Drill-Down Analysis", divider='blue')
    selected_id = st.selectbox("Select a Task ID to inspect:", options=df['id'])

    if selected_id:
        task_details = df[df['id'] == selected_id].iloc[0]

        st.subheader(f"Details for Task: `{task_details['id']}`")
        st.markdown(f"**Status:** {format_status(task_details['status'])}")

        # Timestamps and Durations
        with st.expander("Processing Timeline", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("BERT Time", format_timedelta(task_details['bertEnd'] - task_details['bertStart']))
            c2.metric("LLM Time", format_timedelta(task_details['llmEnd'] - task_details['llmStart']))
            c3.metric("Tool Time", format_timedelta(task_details['analyzeEnd'] - task_details['analyzeStart']))

        # Exception Details
        if task_details['status'] == 98 and task_details['exception_string']:
            st.error(f"**Exception Details:**\n```\n{task_details['exception_string']}\n```")

        # AI Module Outputs
        with st.expander("BERT Analysis Output"):
            st.write(f"Component: `{task_details['bertComponent']}`")
        
        with st.expander("LLM Analysis Output"):
            st.write(f"LLM Name: `{task_details['llmName']}`")
            st.write(f"Tokens Used: `{task_details['llmTokens']}`")

        with st.expander("Tool Analysis Output"):
            st.write(f"Tool Name: `{task_details['toolName']}`")
