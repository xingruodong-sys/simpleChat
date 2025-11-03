
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Naiser-T3000 History",
    page_icon="🗂️",
    layout="wide"
)

# --- Data Loading Function ---
API_URL = "http://127.0.0.1:8001/api/history/tasks"

@st.cache_data(ttl=60)  # Cache data for 60 seconds
def load_data():
    """Fetches all task history from the backend API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return pd.DataFrame() # Return empty dataframe on error

# --- Helper Functions ---
def format_status(status_code):
    """Maps status code to a descriptive string based on the backend Enum."""
    status_map = {
        0: "新建 (New)",
        1: "等待上传日志 (Pending)",
        2: "等待分析模块 (Waiting BERT)",
        3: "等待LLM分析 (Waiting LLM)",
        4: "等待TOOL分析 (Waiting Tool)",
        97: "异常 (Exception)",
        98: "完成 (Done BERT)",
        99: "完成 (Done)"
    }
    return status_map.get(status_code, f"未知 ({status_code})")

def format_timestamp(ts):
    """Formats a unix timestamp, returning '-' if the timestamp is 0 or invalid."""
    if pd.isna(ts) or ts == 0:
        return "-"
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

# --- Main Application ---
st.title("🗂️ All Task History")
st.markdown("Complete log of all tasks processed by the system.")

# Load data
df = load_data()

if df.empty:
    st.info("No tasks found or unable to connect to the backend.")
else:
    # --- Display Table ---
    st.header("Task Data", divider='blue')

    # Create a display dataframe with formatted columns
    df_display = df.copy()

    # Define all possible columns based on CoreData model
    core_data_columns = [
        'id', 'created_at', 'status', 'exception_string', 'isBert', 
        'bertComponent', 'bertStart', 'bertEnd', 'bertCorrect', 'isAnalyzed',
        'toolName', 'analyzeStart', 'analyzeEnd', 'llmName', 'llmStart', 
        'llmEnd', 'llmSuccess', 'llmTokens'
    ]
    
    # Filter list to only include columns that actually exist in the dataframe
    existing_columns = [col for col in core_data_columns if col in df_display.columns]
    df_display = df_display[existing_columns]

    # Format all timestamp columns
    timestamp_cols = [
        'created_at', 'bertStart', 'bertEnd', 'analyzeStart', 
        'analyzeEnd', 'llmStart', 'llmEnd'
    ]
    for col in timestamp_cols:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(format_timestamp)
    
    # Format status
    if 'status' in df_display.columns:
        df_display['status'] = df_display['status'].apply(format_status)
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- Auto-refresh ---
st.button("Refresh Data")
