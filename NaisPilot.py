
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Welcome to Nais-Pilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* Center the title and make it more prominent */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    /* Style for the cards */
    .feature-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        height: 100%;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: scale(1.05);
    }
    .feature-card h3 {
        color: #3498db;
        margin-bottom: 15px;
    }
    .feature-card .emoji {
        font-size: 3rem;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown('<p class="main-header">Welcome to Nais-Pilot</p>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; font-size: 1.2rem; color: #566573;">
    Your intelligent assistant for navigating the complexities of Jira.
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Introduction to Naiser-T3000 ---
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("""
    <div style="text-align: center; font-size: 7rem;">
        🤖
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("Meet Your New AI Teammate: Naiser-T3000")
    st.write("""
        Hello! I'm **Naiser-T3000**, a specialized AI integrated into your Jira workflow. 
        My mission is to provide initial analysis and insights on newly created issues, 
        helping your team save time, reduce noise, and focus on what truly matters.

        Think of me as the first responder for every new ticket, ensuring it's understood, categorized, and ready for action.
    """)

st.divider()

# --- Features Section ---
st.header("What I Can Do For You", anchor=False, divider='rainbow')

cols = st.columns(3, gap="large")

features = [
    {
        "emoji": "🔍",
        "title": "Automatic Issue Analysis",
        "text": "As soon as an issue is created, I perform a deep-dive analysis of its description and summary to understand the core request."
    },
    {
        "emoji": "📝",
        "title": "Intelligent Summarization",
        "text": "I generate a concise, easy-to-read summary, highlighting the key points so you can grasp the issue's context in seconds."
    },
    {
        "emoji": "🏷️",
        "title": "Smart Suggestions",
        "text": "Based on my analysis, I can suggest relevant labels, components, or even potential priority levels to streamline the triage process."
    }
]

for i, feature in enumerate(features):
    with cols[i]:
        st.markdown(f"""
        <div class="feature-card">
            <div class="emoji">{feature['emoji']}</div>
            <h3>{feature['title']}</h3>
            <p>{feature['text']}</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# --- Call to Action / Navigation ---
st.header("Get Started", anchor=False)
st.write("Ready to see me in action? Here's where you can go:")

col_nav1, col_nav2 = st.columns(2)

with col_nav1:
    if st.button("📊 Go to Dashboard", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Dashboard.py")
    st.write("See a real-time feed of my latest analyses and the status of monitored issues.")

with col_nav2:
    if st.button("⚙️ Configure Settings", use_container_width=True):
        st.switch_page("pages/2_Settings.py")
    st.write("Adjust my behavior, set timeouts, and manage how I interact with your projects.")

