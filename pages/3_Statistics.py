import streamlit as st
import requests
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Effective IP Statistics",
    page_icon="📈",
    layout="wide"
)

API_URL = "http://127.0.0.1:8001/api/statistics/effective_ip"

@st.cache_data(ttl=60)
def load_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

st.title("📈 Effective IP Statistics")
st.markdown("Analysis of AI vs Manual bug resolution metrics.")

df = load_data()

if not df.empty:
    # Convert numerical columns
    numeric_cols = ['create_at_to_ai_ana', 'create_at_to_manually_ana', 'create_at_to_integration', 'create_at_to_reject', 'create_at_to_resovled']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # KPIs
    st.header("Key Performance Indicators", divider='blue')
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate averages only for non-zero values
    ai_times = df[df['create_at_to_ai_ana'] > 0]['create_at_to_ai_ana']
    manual_times = df[df['create_at_to_manually_ana'] > 0]['create_at_to_manually_ana']
    
    avg_ai_time = ai_times.mean() if not ai_times.empty else 0
    avg_manual_time = manual_times.mean() if not manual_times.empty else 0
    
    # Convert seconds to hours for display
    def seconds_to_hours(seconds):
        return f"{seconds / 3600:.1f}h" if pd.notnull(seconds) and seconds > 0 else "N/A"

    col1.metric("Total Bugs Tracked", len(df))
    col2.metric("Avg Time to AI Analysis", seconds_to_hours(avg_ai_time))
    col3.metric("Avg Time to Manual Analysis", seconds_to_hours(avg_manual_time))
    
    # Tool Usage
    st.header("Tool & Component Analysis", divider='blue')
    c1, c2 = st.columns(2)
    
    with c1:
        if 'bert_component' in df.columns:
            st.subheader("Component Distribution")
            component_counts = df['bert_component'].value_counts().reset_index()
            component_counts.columns = ['Component', 'Count']
            chart_comp = alt.Chart(component_counts).mark_arc().encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Component", type="nominal"),
                tooltip=["Component", "Count"]
            )
            st.altair_chart(chart_comp, use_container_width=True)

    with c2:
        if 'tool_name' in df.columns:
            st.subheader("Tool Usage")
            tool_counts = df['tool_name'].value_counts().reset_index()
            tool_counts.columns = ['Tool', 'Count']
            chart_tool = alt.Chart(tool_counts).mark_bar().encode(
                x=alt.X('Count', title='Count'),
                y=alt.Y('Tool', sort='-x', title='Tool Name'),
                tooltip=['Tool', 'Count']
            )
            st.altair_chart(chart_tool, use_container_width=True)

    # Time Comparisons
    st.header("Time Efficiency Analysis", divider='blue')
    
    # Scatter plot: AI Time vs Manual Time
    if 'create_at_to_ai_ana' in df.columns and 'create_at_to_manually_ana' in df.columns:
        scatter_df = df[(df['create_at_to_ai_ana'] > 0) & (df['create_at_to_manually_ana'] > 0)].copy()
        if not scatter_df.empty:
            # Convert to hours for better plotting
            scatter_df['AI Time (h)'] = scatter_df['create_at_to_ai_ana'] / 3600
            scatter_df['Manual Time (h)'] = scatter_df['create_at_to_manually_ana'] / 3600
            
            chart_scatter = alt.Chart(scatter_df).mark_circle(size=60).encode(
                x='AI Time (h)',
                y='Manual Time (h)',
                color=alt.Color('bert_component', legend=alt.Legend(title="Component")),
                tooltip=['TicketID', 'bert_component', 'AI Time (h)', 'Manual Time (h)']
            ).interactive()
            
            st.altair_chart(chart_scatter, use_container_width=True)
        else:
            st.info("Not enough overlapping data for AI vs Manual time comparison (need cases where both happened).")

    # Raw Data
    st.header("Raw Data", divider='blue')
    st.dataframe(df, use_container_width=True)

else:
    st.info("No data available.")
