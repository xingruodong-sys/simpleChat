import streamlit as st
import requests
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Effective IP Statistics",
    page_icon="📈",
    layout="wide"
)

AI_API_URL = "http://127.0.0.1:8001/api/statistics/effective_ip"
MANUAL_API_URL = "http://127.0.0.1:8001/api/statistics/manual_efficiency"
BERT_CORRECT_API_URL = "http://127.0.0.1:8001/api/statistics/bert_correct"
BERT_HISTORY_API_URL = "http://127.0.0.1:8001/api/statistics/bert_correct_history"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from {url}: {e}")
        return pd.DataFrame()

def seconds_to_hours(seconds):
    return f"{seconds / 3600:.1f}h" if pd.notnull(seconds) and seconds > 0 else "N/A"

st.title("📈 Effective IP Statistics")
st.markdown("Analysis of AI vs Manual bug resolution metrics.")

# --- AI vs Manual Analysis (Existing) ---
st.header("AI vs Manual Analysis", divider='rainbow')
df_ai = load_data(AI_API_URL)

if not df_ai.empty:
    # Convert numerical columns
    numeric_cols = ['create_at_to_ai_ana', 'create_at_to_manually_ana', 'create_at_to_integration', 'create_at_to_reject', 'create_at_to_resovled']
    for col in numeric_cols:
        if col in df_ai.columns:
            df_ai[col] = pd.to_numeric(df_ai[col], errors='coerce').fillna(0)
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    
    ai_times = df_ai[df_ai['create_at_to_ai_ana'] > 0]['create_at_to_ai_ana']
    manual_times = df_ai[df_ai['create_at_to_manually_ana'] > 0]['create_at_to_manually_ana']
    
    avg_ai_time = ai_times.mean() if not ai_times.empty else 0
    avg_manual_time = manual_times.mean() if not manual_times.empty else 0
    
    col1.metric("Total AI-Tracked Bugs", len(df_ai))
    col2.metric("Avg Time to AI Analysis", seconds_to_hours(avg_ai_time))
    col3.metric("Avg Time to Manual Analysis (in AI flow)", seconds_to_hours(avg_manual_time))

    # Tool Usage
    c1, c2 = st.columns(2)
    with c1:
        if 'bert_component' in df_ai.columns:
            st.subheader("Component Distribution")
            component_counts = df_ai['bert_component'].value_counts().reset_index()
            component_counts.columns = ['Component', 'Count']
            chart_comp = alt.Chart(component_counts).mark_arc().encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Component", type="nominal"),
                tooltip=["Component", "Count"]
            )
            st.altair_chart(chart_comp, use_container_width=True)

    with c2:
        if 'tool_name' in df_ai.columns:
            st.subheader("Tool Usage")
            tool_counts = df_ai['tool_name'].value_counts().reset_index()
            tool_counts.columns = ['Tool', 'Count']
            chart_tool = alt.Chart(tool_counts).mark_bar().encode(
                x=alt.X('Count', title='Count'),
                y=alt.Y('Tool', sort='-x', title='Tool Name'),
                tooltip=['Tool', 'Count']
            )
            st.altair_chart(chart_tool, use_container_width=True)
            
    # Time Comparisons
    if 'create_at_to_ai_ana' in df_ai.columns and 'create_at_to_manually_ana' in df_ai.columns:
        scatter_df = df_ai[(df_ai['create_at_to_ai_ana'] > 0) & (df_ai['create_at_to_manually_ana'] > 0)].copy()
        if not scatter_df.empty:
            scatter_df['AI Time (h)'] = scatter_df['create_at_to_ai_ana'] / 3600
            scatter_df['Manual Time (h)'] = scatter_df['create_at_to_manually_ana'] / 3600
            st.subheader("Time Efficiency Comparison")
            chart_scatter = alt.Chart(scatter_df).mark_circle(size=60).encode(
                x='AI Time (h)',
                y='Manual Time (h)',
                color=alt.Color('bert_component', legend=alt.Legend(title="Component")),
                tooltip=['TicketID', 'bert_component', 'AI Time (h)', 'Manual Time (h)']
            ).interactive()
            st.altair_chart(chart_scatter, use_container_width=True)

    with st.expander("AI Analysis Raw Data"):
        st.dataframe(df_ai, use_container_width=True)
else:
    st.info("No AI analysis data available.")

# --- Manual Baseline Section ---
st.header("Manual Efficiency Baseline (No AI)", divider='orange')
df_manual = load_data(MANUAL_API_URL)

if not df_manual.empty:
    if 'create_at_to_manually_ana' in df_manual.columns:
        df_manual['create_at_to_manually_ana'] = pd.to_numeric(df_manual['create_at_to_manually_ana'], errors='coerce').fillna(0)
    
    m_times = df_manual[df_manual['create_at_to_manually_ana'] > 0]['create_at_to_manually_ana']
    avg_m_time = m_times.mean() if not m_times.empty else 0
    
    mc1, mc2 = st.columns(2)
    mc1.metric("Total Manual Baseline Bugs", len(df_manual))
    mc2.metric("Avg Manual Analysis Time", seconds_to_hours(avg_m_time))
    
    # Histogram of manual times
    if not m_times.empty:
        st.subheader("Manual Analysis Time Distribution")
        hist_df = pd.DataFrame({'Time (h)': m_times / 3600})
        chart_hist = alt.Chart(hist_df).mark_bar().encode(
            x=alt.X('Time (h)', bin=alt.Bin(maxbins=30)),
            y='count()'
        )
        st.altair_chart(chart_hist, use_container_width=True)

    with st.expander("Manual Baseline Raw Data"):
        st.dataframe(df_manual, use_container_width=True)
else:
    st.info("No manual baseline data available.")

# --- BERT Correctness Section ---
st.header("AI Module Classification Accuracy", divider='green')
df_bert = load_data(BERT_CORRECT_API_URL)

if not df_bert.empty:
    # Ensure 'correct' column is boolean
    if 'correct' in df_bert.columns:
        # Some redis data might be strings "true"/"false" or 0/1, force convert
        df_bert['correct'] = df_bert['correct'].apply(lambda x: str(x).lower() == 'true' if isinstance(x, str) else bool(x))
        
    total_samples = len(df_bert)
    correct_samples = len(df_bert[df_bert['correct'] == True])
    accuracy = (correct_samples / total_samples) * 100 if total_samples > 0 else 0
    
    bc1, bc2 = st.columns(2)
    bc1.metric("Total Classified Samples", total_samples)
    bc2.metric("Overall Accuracy", f"{accuracy:.2f}%")
    
    # Accuracy by Component
    if 'bert component' in df_bert.columns and 'correct' in df_bert.columns:
        st.subheader("Accuracy by Component")
        
        # Calculate accuracy per component
        comp_stats = df_bert.groupby('bert component')['correct'].agg(['count', 'sum']).reset_index()
        comp_stats.columns = ['Component', 'Total', 'Correct']
        comp_stats['Accuracy'] = (comp_stats['Correct'] / comp_stats['Total']) * 100
        
        # Chart
        chart_acc = alt.Chart(comp_stats).mark_bar().encode(
            x=alt.X('Component', sort='-y'),
            y=alt.Y('Accuracy', title='Accuracy (%)', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('Accuracy', scale=alt.Scale(scheme='greens'), legend=None),
            tooltip=['Component', 'Total', 'Correct', alt.Tooltip('Accuracy', format='.2f')]
        )
        st.altair_chart(chart_acc, use_container_width=True)

    with st.expander("Classification Raw Data"):
        st.dataframe(df_bert, use_container_width=True)
else:
    st.info("No classification accuracy data available.")

# --- BERT History Section ---
st.header("AI Classification Trends (Weekly & Cumulative)", divider='violet')
df_history = load_data(BERT_HISTORY_API_URL)

if not df_history.empty:
    # Use week_start_str as the main date axis
    if 'week_start_str' in df_history.columns:
        df_history['Date'] = df_history['week_start_str']
    elif 'timestamp' in df_history.columns:
         # Fallback for old data if any
        df_history['Date'] = pd.to_datetime(df_history['timestamp'], unit='s').dt.strftime('%Y-%m-%d')
    
    # Line Chart for Rates
    st.subheader("Accuracy Trend")
    
    base = alt.Chart(df_history).encode(x=alt.X('Date', title='Week Start'))
    
    line_weekly = base.mark_line(color='orange').encode(
        y=alt.Y('weekly_rate', title='Rate (0-1)'),
        tooltip=['Date', 'week_end_str', 'weekly_rate', 'weekly_correct', 'weekly_error']
    )
    
    line_cum = base.mark_line(color='green').encode(
        y=alt.Y('cumulative_rate', title='Rate (0-1)'),
        tooltip=['Date', 'cumulative_rate', 'cumulative_correct', 'cumulative_error']
    )
    
    chart_trend = (line_weekly + line_cum).resolve_scale(y='shared').properties(title="Weekly (Orange) vs Cumulative (Green) Accuracy Rate")
    st.altair_chart(chart_trend, use_container_width=True)
    
    # Metrics for latest run
    latest = df_history.iloc[-1]
    hc1, hc2, hc3, hc4 = st.columns(4)
    hc1.metric("Latest Weekly Correct", latest.get('weekly_correct', 0))
    hc2.metric("Latest Weekly Rate", f"{latest.get('weekly_rate', 0)*100:.2f}%")
    hc3.metric("Cumulative Correct", latest.get('cumulative_correct', 0))
    hc4.metric("Cumulative Rate", f"{latest.get('cumulative_rate', 0)*100:.2f}%")

    with st.expander("History Raw Data"):
        st.dataframe(df_history, use_container_width=True)
else:
    st.info("No history statistics available.")