import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="BERT Samples",
    page_icon="📂",
    layout="wide"
)

st.title("📂 BERT Specimen Data")
st.markdown("View extracted BERT training samples.")

API_BASE_URL = "http://127.0.0.1:8001/api/bert_samples"

# 1. Fetch Categories
@st.cache_data(ttl=3600)
def fetch_categories():
    try:
        response = requests.get(f"{API_BASE_URL}/categories")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch categories: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return []

categories = fetch_categories()

# 2. Sidebar Control
with st.sidebar:
    st.header("Filter")
    selected_category = st.selectbox(
        "Select Component Category",
        options=categories if categories else []
    )

# 3. Fetch Data
@st.cache_data(ttl=60)
def fetch_api_data(category):
    if not category:
        return []
    try:
        response = requests.get(f"{API_BASE_URL}/data", params={"category": category})
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return []

raw_data = fetch_api_data(selected_category)

# 4. Display Data
col1, col2 = st.columns(2)
col1.metric("Total Samples", len(raw_data) if raw_data else 0)

if raw_data:
    df = pd.DataFrame(raw_data)
    
    # Search box
    search_term = st.text_input("Search Summary or Issue Key", "")
    if search_term:
        df = df[
            df['Summary'].str.contains(search_term, case=False, na=False) | 
            df['Issue Key'].str.contains(search_term, case=False, na=False)
        ]
    
    st.dataframe(
        df,
        column_config={
            "Issue Key": st.column_config.TextColumn("Jira ID", width="small"),
            "Summary": st.column_config.TextColumn("Summary", width="large"),
            "Real Module": st.column_config.TextColumn("Real Module", width="medium"),
            "Commit Module": st.column_config.TextColumn("Commit Module", width="medium"),
            "User": st.column_config.TextColumn("Developer", width="small"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"bert_samples_{selected_category}.csv",
        mime="text/csv",
    )
else:
    if selected_category:
        st.info("No data found for this category.")
    else:
        st.warning("Please select a category (or ensure API is running).")
