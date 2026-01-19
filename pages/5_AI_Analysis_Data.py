import streamlit as st
import requests
import json
import pandas as pd

st.title("AI分析优质数据")

# 假设 API 运行在 localhost:8000，调整端口如果需要
API_URL = "http://127.0.0.1:8001/api/ai_analysis_data"

try:
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        if data:
            # 创建DataFrame
            df = pd.DataFrame(data)
            # 重命名列以更友好
            df.rename(columns={
                'TicketID': 'Ticket ID',
                'component': 'Component',
                'Summary': 'Summary',
                'Comments': 'Comments (JSON)'
            }, inplace=True)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 可选：展开显示comments
            st.header("Comments 详情")
            for idx, row in df.iterrows():
                with st.expander(f"Ticket: {row['Ticket ID']}"):
                    comments_str = row['Comments (JSON)']
                    try:
                        comments = json.loads(comments_str)
                        for comment in comments:
                            st.write(f"**Time:** {comment.get('Time', 'N/A')}")
                            st.write(f"**Author:** {comment.get('Author', 'N/A')}")
                            st.write(f"**Team:** {comment.get('team', 'N/A')}")
                            st.write(f"**Comment:** {comment.get('comment', 'N/A')}")
                            st.divider()
                    except json.JSONDecodeError:
                        st.write("Invalid comments format")
        else:
            st.write("No data available.")
    else:
        st.error(f"Failed to load data: {response.status_code}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to API: {str(e)}")