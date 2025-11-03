from Mcp.server.jira import api
from src.helper.Redis import *
from src.helper import Ollama, Log
import streamlit as st

def calculate_component_changes_percentage():
    """计算组件变更的百分比"""
    # 获取FO和DEV的变更数据
    fo_changes = redis.smembers(COMPONENTS_CHANGE_BY_FO_SET)
    dev_changes = redis.smembers(COMPONENTS_CHANGE_BY_DEV_SET)
    
    # 计算总数
    fo_count = len(fo_changes) if fo_changes else 0
    dev_count = len(dev_changes) if dev_changes else 0
    total_count = fo_count + dev_count
    
    # 计算百分比
    if total_count > 0:
        fo_percentage = (fo_count / total_count) * 100
        dev_percentage = (dev_count / total_count) * 100
    else:
        fo_percentage = 0
        dev_percentage = 0
    
    # 创建结果字典
    result = {
        "total_changes": total_count,
        "fo_changes": {
            "count": fo_count,
            "percentage": round(fo_percentage, 2)
        },
        "dev_changes": {
            "count": dev_count,
            "percentage": round(dev_percentage, 2)
        }
    }
    
    return result

def display_percentages():
    """显示百分比数据"""
    st.header("组件变更百分比统计")
    
    result = calculate_component_changes_percentage()
    
    # 显示总数
    st.metric("总变更数", result["total_changes"])
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("组件负责人变更")
        st.metric("数量", result["fo_changes"]["count"])
        st.metric("百分比", f"{result['fo_changes']['percentage']}%")
        if result["fo_changes"]["count"] > 0:
            with st.expander("查看详细信息"):
                for issue in redis.smembers(COMPONENTS_CHANGE_BY_FO_SET):
                    st.write(f"[{issue}](https://jira.nts.neusoft.local/browse/{issue})")
    
    with col2:
        st.subheader("开发人员变更")
        st.metric("数量", result["dev_changes"]["count"])
        st.metric("百分比", f"{result['dev_changes']['percentage']}%")
        if result["dev_changes"]["count"] > 0:
            with st.expander("查看详细信息"):
                for issue in redis.smembers(COMPONENTS_CHANGE_BY_DEV_SET):
                    st.write(f"[{issue}](https://jira.nts.neusoft.local/browse/{issue})")
    
    # 显示饼图
    if result["total_changes"] > 0:
        st.subheader("变更比例分布")
        data = {
            "类型": ["组件负责人变更", "开发人员变更"],
            "数量": [result["fo_changes"]["count"], result["dev_changes"]["count"]],
            "百分比": [result["fo_changes"]["percentage"], result["dev_changes"]["percentage"]]
        }
        st.bar_chart(data, x="类型", y="百分比")

if __name__ == "__main__":
    display_percentages() 