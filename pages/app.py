
import streamlit as st
from src.helper import JiraSy, Ollama
from src.helper.Redis import *
from src.helper.chroma import *
import pandas as pd
import numpy as np
import json
import time
from pathlib import Path
import shutil

def bulkImport():
    st.subheader("批量导入监控")
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
    syjira = JiraSy.JiraImp('http://10.10.88.63:8080/', "xingrd", "1qaz!QAZ1qaz")
    temp_dir = Path("./trace/tmp").resolve()

    def createIssue(keys):
        data = []
        for key in keys:
            if redis.hexists(HH_TO_SY_JIRA_HASH, key):
                sykey = redis.hget(HH_TO_SY_JIRA_HASH, key)
                data.append([key, sykey, 'Exist'])
                continue

            content = dejira.getIssueContentExt(key)
            path = dejira.getCustomFieldValue(key, "customfield_12010")
            if content['type'] != 'Product bug':
                data.append([key, 'none', 'not bug'])
                continue
            description = content["description"] + '\n' + path if path else content["description"]
            temp_dir.mkdir(parents=True, exist_ok=True)
            dejira.download_attachment(issue_key=key, destination_path=temp_dir)
            new_issue_key = syjira.createIssue("AINMASDK", content["summary"], description, issuetype='Product bug')
            syjira.upload_attachment(new_issue_key, temp_dir)
            syjira.assigneeIssue(new_issue_key, "Naiser-T3000")
            redis.hset(HH_TO_SY_JIRA_HASH, key, new_issue_key)
            data.append([key, new_issue_key, 'Created'])
            shutil.rmtree(temp_dir)
        return data

    def showCreated(data):
        st.write("导入结果显示:")
        df = pd.DataFrame(
            data, columns=("HH ID", "SY ID", "是否新创建")
        )
        st.dataframe(df)

    def searchIssues(keys):
        data = []
        for key in keys:
            if redis.hexists(HH_TO_SY_JIRA_HASH, key):
                data.append([key, redis.hget(HH_TO_SY_JIRA_HASH, key)])
            else:
                data.append([key, 'None'])
        return data

    def showSearched(data):
        st.write("查询结果显示:")
        df = pd.DataFrame(
            data, columns=("HH ID", "SY ID")
        )
        st.dataframe(df)

    st.warning("按照jql批量导入")
    jql = st.text_input("请尽量缩小筛选的范围，不要一次性导入太多")
    col5, col6 = st.columns(2)
    with col5:
        if st.button("导入Jira数据", key="key1"):
            keys = dejira.getIssuesByJql(jql)
            data = createIssue(keys)
            showCreated(data)
    with col6:
        if st.button("查询数据", key="keys1", type="primary"):
            keys = dejira.getIssuesByJql(jql)
            data = searchIssues(keys)
            showSearched(data)

    st.divider()
    st.warning("输入起始导入JiraID，导入个数")
    col1, col2 = st.columns(2)    
    with col1:
        num1 = st.number_input("请输入从多少开始", value=0, step=1, format="%d", min_value=0)
    with col2:
        num2 = st.number_input("请输入个数", value=1, step=1, format="%d", min_value=1, max_value=100)

    col3, col4 = st.columns(2)
    with col3:
        if st.button("导入Jira数据", key="key2"):
            keys = []
            for i in range(num1, num1 + num2):
                key = 'NMASDK-' + str(i)
                keys.append(key)
            data = createIssue(keys)
            showCreated(data)
    with col4:
        if st.button("查询数据", key="keys2", type="primary"):
            keys = []
            for i in range(num1, num1 + num2):
                key = 'NMASDK-' + str(i)
                keys.append(key)
            data = searchIssues(keys)
            showSearched(data)
    
    st.divider()
    st.warning("按照csv文件导入")
    uploaded_file = st.file_uploader('你也可以上传需要解析的文件, 压缩包或者文件, 一个或多个文件均可')
    col7, col8 = st.columns(2)
    with col7:
        if st.button("导入Jira数据", key="key3"):
            data = []
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                if 'Issue key' in df.columns:
                    issue_keys = df['Issue key'].dropna().unique()  # 去除空值并去重
                    print("提取出的 issue keys：")
                    for key in issue_keys:
                        print(key)
                    data = createIssue(issue_keys)
                    showCreated(data)
    with col8:
        if st.button("查询数据", key="keys3", type="primary"):
            data = []
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                if 'Issue key' in df.columns:
                    issue_keys = df['Issue key'].dropna().unique()  # 去除空值并去重
                    print("提取出的 issue keys：")
                    for key in issue_keys:
                        print(key)
                    data = searchIssues(issue_keys)
                    showSearched(data)

    st.divider()
    st.warning("监控名下Bug清单")
    from streamlit_tags import st_tags

    # if "names" not in st.session_state:
    #     st.session_state.names = []
    names = redis.lrange(WATCHING_MATES_LIST, 0, -1)
    keywords = st_tags(
        label='输入监控人员:',
        text='Press enter to add more',
        value=names,
        suggestions=['wangjin.neu', 'meng.ff', 'tiandq', 
                    'qiuye', 'yushaobo', 'mazhch', 
                    'gelan', 'zheng-j', 'xingrd'],
        maxtags = 10,
        key='key4'
        )
    if keywords != names:
        while redis.llen(WATCHING_MATES_LIST):
            redis.lpop(WATCHING_MATES_LIST)
        for key in keywords:
            redis.lpush(WATCHING_MATES_LIST, key)
        print(keywords)

def mcpServerConfig():
    st.subheader("mcp server 配置")
    componentList = [
        'DI_POS_SDS',
        'HMI',
        'System',
        'MapViewer',
        'DBU',
        'Positioning',
        'Activation',
        'Guidance',
        'Route Calculation',
        'TI',
        'Activation_DBU'
    ]
    if 'component' not in st.session_state:
        st.session_state.component = 'DI_POS_SDS'
    
    st.session_state.component = st.selectbox("选择模块", componentList)

    def add_item(component, key, value):
        redis.hset(component, key, value)
        return (f"Item '{key}' added successfully!")

    def delete_item(component, key):
        if redis.exists(component):
            redis.hdel(component, key)
            return (f"Item '{key}' deleted successfully!")
        else:
            return (f"Item '{key}' does not exist.")

    def update_item(component, key, new_value):
        if redis.exists(component):
            redis.hset(component, key, new_value)
            return (f"Item '{key}' updated successfully!")
        else:
            return (f"Item '{key}' does not exist.")

    def get_items(component:str):
        items = {}
        for key in redis.hgetall(component).keys():
            items[key] = redis.hget(component, key)
        return items
    
    def get_item(component:str, key:str):
        prompt = ''
        if redis.hexists(component, key):
            prompt = redis.hget(component, key)
        else:
            prompt = ""
        return prompt

    items = []
    for key in get_items(st.session_state.component).keys():
        items.append({
            'Tool ID': key,
            'Tool Prompt': redis.hget(st.session_state.component, key)
        })
    keys = list(get_items(st.session_state.component).keys())

    st.warning(f"当前模块为 {st.session_state.component}，共有 {len(keys)} 个Tool ID")
    menu = st.selectbox("菜单", ["添加数据", "删除数据"])
    if menu == "添加数据":
        with st.expander("添加数据", expanded=True):
            ToolID = st.text_input("Tool ID")
            if st.button("添加"):
                if ToolID:  # 简单验证
                    add_item(st.session_state.component, ToolID, '')
                    st.rerun()
                else:
                    st.warning("Tool ID不能为空")
    
    elif menu == "删除数据":
        if len(keys) > 0:
            id_to_delete = st.selectbox(
                "选择要删除的ID",
                keys
            )
            st.warning(f"你确定要删除ID为 {id_to_delete} 的数据吗?")
            if st.button("确认删除"):
                delete_item(st.session_state.component, id_to_delete)
                #刷新页面
                st.rerun()
        else:
            st.warning("没有数据可删除")

    # 新增的Prompt编辑区域
    with st.expander("Prompt编辑", expanded=True):
        updateToolPrompt = ''
        server_address = st.text_input("MCP Server地址", getMcpServerForModule(st.session_state.component))
        function_owner = st.text_input("接口人", getFunctionInterfaceForModule(st.session_state.component))
        if len(keys) > 0:
            id_to_update = st.selectbox(
                "选择要更新的ID",
                keys
            )
            updateToolPrompt = st.text_area(
                "Tool Prompt",
                value=get_item(st.session_state.component, id_to_update),
                height=500,
                key="prompt_editor1",
                help="支持Markdown格式和变量占位符"
            )

            # 保存按钮与状态同步
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💾 保存Prompt"):
                if updateToolPrompt:
                    update_item(st.session_state.component, id_to_update, updateToolPrompt)
                    st.toast("Prompt保存成功！", icon="✅")
                setMcpServerRes = setMcpServerForModule(st.session_state.component, server_address)
                setFunctionInterfaceForModule(st.session_state.component, function_owner)
                st.toast(setMcpServerRes)
        
        with col2:
            st.caption("当前字符数：{}".format(len(updateToolPrompt)))
    st.divider()
    with st.expander("使用方法", expanded=True):
        st.markdown("""
        1. 选择对应的模块后，在prompt编辑中配置好启动server服务的ip:port，点击保存。
        2. http://10.10.88.63:8080/ 登录沈阳Jira，创建票，ISSUE的log路径要填到描述中，将票打给账号，Naiser-T3000账号，等待结果。
        """)

def showPercentComponentChange():
    st.subheader("组件变更统计")

    # 显示数据统计
    col1, col2 = st.columns(2)
    with col1:
        total = redis.scard(COMPONENTS_CHANGE_BY_DEV_SET_IN_GIVEN_ISSUE)
        st.metric(label="开发人员变更数量", value=total)
        if total > 0:
            with st.expander("查看详细信息"):
                for issue in redis.smembers(COMPONENTS_CHANGE_BY_DEV_SET_IN_GIVEN_ISSUE):
                    st.write(f"[{issue}](https://jira.nts.neusoft.local/browse/{issue})")

    with col2:
        total = redis.scard(COMPONENTS_CHANGE_BY_FO_SET_IN_GIVEN_ISSUE)
        st.metric(label="组件负责人变更数量", value=total)
        if total > 0:
            with st.expander("查看详细信息"):
                for issue in redis.smembers(COMPONENTS_CHANGE_BY_FO_SET_IN_GIVEN_ISSUE):
                    st.write(f"[{issue}](https://jira.nts.neusoft.local/browse/{issue})")

    componentTable = [
        COMPONENTS_MAP_HASH,
        COMPONENTS_HMI_HASH,
        COMPONENTS_SEARCH_HASH,
        COMPONENTS_GUIDANCE_HASH,
        COMPONENTS_DBU_POS_HASH,
        COMPONENTS_ACTIVITION_HASH,
        COMPONENTS_SYSTEM_HASH,
        COMPONENTS_ROUTE_HASH,
        COMPONENTS_TI_HASH,
        COMPONENTS_ACTIVITION_DBU_HASH,
        COMPONENTS_HMI_VR_HASH,
    ]
    total = 0
    for component in componentTable:
        total += redis.hlen(component)
    # 饼图显示比例
    if redis.scard(COMPONENTS_CHANGE_BY_DEV_SET_IN_GIVEN_ISSUE) > 0 or redis.scard(COMPONENTS_CHANGE_BY_FO_SET_IN_GIVEN_ISSUE) > 0:
        data = {
            "类型": ["组件负责人变更", "开发人员变更"],
            "数量": [redis.scard(COMPONENTS_CHANGE_BY_FO_SET_IN_GIVEN_ISSUE), redis.scard(COMPONENTS_CHANGE_BY_DEV_SET_IN_GIVEN_ISSUE)]
        }
        st.bar_chart(data, x="类型", y="数量")
    # 显示组件变更的百分比
    st.subheader("组件变更百分比")
    if total > 0:
        data = {
            "组件": [],
            "变更数量": [],
            "百分比": []
        }
        count = redis.scard(COMPONENTS_CHANGE_BY_DEV_SET_IN_GIVEN_ISSUE) + redis.scard(COMPONENTS_CHANGE_BY_FO_SET_IN_GIVEN_ISSUE)
        data["组件"].append(total)
        data["变更数量"].append(count)
        data["百分比"].append(f"{(count / total) * 100:.2f}%")
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def showCommonSpecimen():
    st.divider()
    st.header("通用准确样本列表")
    
    componentTable = [
        COMPONENTS_MAP_HASH,
        COMPONENTS_HMI_HASH,
        COMPONENTS_SEARCH_HASH,
        COMPONENTS_GUIDANCE_HASH,
        COMPONENTS_DBU_POS_HASH,
        COMPONENTS_ACTIVITION_HASH,
        COMPONENTS_SYSTEM_HASH,
        COMPONENTS_ROUTE_HASH,
        COMPONENTS_TI_HASH,
        COMPONENTS_ACTIVITION_DBU_HASH,
        COMPONENTS_HMI_VR_HASH,
    ]
    
    for component in componentTable:
        st.write(f'模块{component}有{redis.hlen(component)}个样本')
        data = []
        for key in redis.hkeys(component):
            jstr = redis.hget(component, key)
            dictitem = json.loads(jstr)
            data.append([key, 
                        dictitem[COMMITMODULE], 
                        dictitem[REALMODULE], 
                        dictitem[ISSUETYPE], 
                        dictitem[USER], 
                        dictitem[SUMMARY]])
        df = pd.DataFrame(
            data, columns=(ISSUE, COMMITMODULE, REALMODULE, ISSUETYPE,'analyzer', SUMMARY)
        )
        st.dataframe(df)
        st.write(f'----------------------------------------')

def showSpecimen():
    st.divider()
    st.header("准确样本列表")
    data2 = []
    componentTable = {
        'MapViewer': 0,
        'Route Calculation': 0,
        'DI_POI_SDS': 0,
        'Guidance': 0
    }
    total1 = 0
    for key in redis.hkeys(SPECIMEN_STANDARD_HASH):
        total1 = total1 + 1
        jstr = redis.hget(SPECIMEN_STANDARD_HASH, key)
        dictitem = json.loads(jstr)
        data2.append([key, 
                     dictitem[REALMODULE], 
                     dictitem[COMMITMODULE], 
                     dictitem[MATCH], 
                     dictitem[RESOLVER]])
        if dictitem[MATCH]:
            match = match + 1
        componentTable[dictitem[REALMODULE]] = componentTable[dictitem[REALMODULE]] + 1

    df2 = pd.DataFrame(
        data2, columns=(ISSUE, REALMODULE, COMMITMODULE, MATCH, RESOLVER)
    )
    st.dataframe(df2)
    st.write(f'总样本{total1}个，有{match}个修改人和component匹配，匹配率{match / total1}')
    for item in componentTable.keys():
        st.write(f'模块{item}有{componentTable[item]}个样本')


def query():
    st.subheader("总结历史调查方法")
    impl = ChromaDBImpl('jira_no_comments')
    user_input = st.text_input("请输入内容：", key="input")

    # 创建一个检索按钮
    if st.button("检索"):
        # 定义正则表达式规则
        pattern = r"^NMASDK-\d+$"
        
        # 检查输入内容是否符合规则
        if re.match(pattern, user_input):
            # 如果符合规则，模拟检索逻辑
            search_result = f"检索到的内容：{user_input}"
            res, ids, dis = do_query(impl, user_input)
            prompt = getPromptForSummary() + '\n' + res
            result = Ollama.chat(system_prompt=getSystemPromptForSummary(), prompt=prompt, modelname=redis.get(SETTING_LLM_MODEL_FOR_SUMMARY), key=None, data=None)
            st.write(f"总结结果：{ids}")
            st.write(f"距离：{dis}")
            st.write(result)
        else:
            st.warning("输入内容不符合规则，请输入类似 'NMASDK-1' 的格式！")

def queryMuti():
    st.subheader("Chroma多数据检索")
    st.warning("Chroma的DB数据从50000到65000,请不要输入这个区间的数据")

    impl = ChromaDBImpl('jira_strip')
    # 输入两个数
    col1, col2 = st.columns(2)    
    # 显示数据统计
    with col1:
        num1 = st.number_input("请输入从多少开始", value=0, step=1, format="%d")
    with col2:
        num2 = st.number_input("请输入到多少结束", value=0, step=1, format="%d")

    # 检索按钮
    if st.button("检索数据"):
        data = []
        if num1 > num2:
            st.error("错误: 第一个整数应小于或等于第二个整数。")
        # 调用函数检索数据
        for i in range(num1, num2):
            key = 'NMASDK-' + str(i)
            source, ids, dis, res, success = do_query_strip(impl, key)
            if success is False:
                st.warning(f"问题 {key} 不是Product bug类型，跳过检索。")
                continue
            ids = ids[0]
            dis = dis[0]
            # data.append([
            #     str(key) + "\n" + str(src),
            #     str(ids[0]) + "\n" + str(dis[0]) + "\n" + str(res[0]),
            #     str(ids[1]) + "\n" + str(dis[1]) + "\n" + str(res[1]),
            #     str(ids[2]) + "\n" + str(dis[2]) + "\n" + str(res[2]),
            #     str(ids[3]) + "\n" + str(dis[3]) + "\n" + str(res[3]),
            #     str(ids[4]) + "\n" + str(dis[4]) + "\n" + str(res[4]),
            # ])
            data.append([
                source,
                dis,
                ids,
                res
            ])

        # 显示结果
        st.write("检索结果显示:")
        df = pd.DataFrame(
            # data, columns=(ISSUE, '1', '2', '3', '4', '5')
            data, columns=(ISSUE, '1', '2', '3')
        )
        st.dataframe(df)

def showMcpClient():
    # 初始化session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "connected" not in st.session_state:
        st.session_state.connected = False
    if "mcp_llm_model" not in st.session_state:
        st.session_state.mcp_llm_model = "qwen3:32b"
    if "tools" not in st.session_state:
        st.session_state.tools = None
    if "models" not in st.session_state:
        st.session_state.models = Ollama.get_modes()
    if "mcp" not in st.session_state:
        st.session_state.mcp = ''

    # 页面布局
    st.title("MCP Chat")
    from Mcp.client import mcpClient
    _mcp = mcpClient.MCPClient('mcpone')

    # 顶部控制栏
    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        st.session_state.mcp_llm_model = st.selectbox("选择 LLM 模型", st.session_state.models, index=st.session_state.models.index(st.session_state.mcp_llm_model))
    with col2:
        server_address = st.text_input("MCP Server地址", "http://10.10.90.4:8030/mcp")
    with col3:
        if st.button("连接服务器"):
            st.session_state.connected = mcpClient.connect_sync(_mcp, server_address)
            if st.session_state.connected:
                st.session_state.tools = _mcp.tools
                st.session_state.mcp = _mcp
    
                if st.session_state.tools is mcpClient.types.ListToolsResult:
                    for tool in st.session_state.tools.tools:
                        st.warning(f'tool name={tool.name}, tool description={tool.description}')
    # 连接状态指示器
    status_color = "green" if st.session_state.connected else "red"
    status_text = "已连接" if st.session_state.connected else "未连接"
    st.markdown(
        f'<div style="display: inline-block; padding: 0.5rem; background-color: {status_color}; '
        f'color: white; border-radius: 0.5rem;">{status_text}</div>',
        unsafe_allow_html=True
    )

    # 聊天记录显示区域
    st.divider()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 底部输入框
    if prompt := st.chat_input("输入你的消息..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成模拟回复
        with st.chat_message("assistant"):
            def func(name, arguments):
                return mcpClient.call_sync(st.session_state.mcp, name, arguments)
            response = Ollama.chat_with_tools(system_prompt='', prompt=prompt, modelname=st.session_state.mcp_llm_model, key=None, data=None, tools=st.session_state.tools, function=func)
            st.markdown(response)
        
        # 添加助手消息
        st.session_state.messages.append({"role": "assistant", "content": response})

def moduleRecognition():
    st.subheader("模块识别")
    st.warning("输入起始导入Jira ID和结束Jira ID")
    # if "models" not in st.session_state:
    #     st.session_state.models = Ollama.get_modes()
    # st.session_state.mcp_llm_model = st.selectbox("选择 LLM 模型", st.session_state.models, index=st.session_state.models.index(st.session_state.mcp_llm_model))
    # 输入框
    col1, col2 = st.columns(2)    
    # 显示数据统计
    with col1:
        num1 = st.number_input("请输入从多少开始", value=0, step=1, format="%d")
    with col2:
        num2 = st.number_input("请输入到多少结束", value=0, step=1, format="%d")

    # 创建一个识别按钮
    if st.button("导入Jira数据"):
        data = []
        if num1 > num2:
            st.error("错误: 第一个整数应小于或等于第二个整数。")
        dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
        syjira = JiraSy.JiraImp('http://10.10.88.63:8080/', "xingrd", "1qaz!QAZ1qaz")
        # 调用函数检索数据
        for i in range(num1, num2):
            key = 'NMASDK-' + str(i)
            content = dejira.getIssueContentExt(key)
            new_issue_key = syjira.createIssue("AINMASDK", content["summary"], description=content["description"], issuetype='Product bug')
            syjira.assigneeIssue(new_issue_key, "Naiser-T3000")
            data.append([new_issue_key, content["components"]])

        # 显示结果
        st.write("导入结果显示:")
        df = pd.DataFrame(
            data, columns=(ISSUE, "COMPONENTS")
        )
        st.dataframe(df)

with st.sidebar:
    st.header("导航")
    page = st.radio("选择页面", 
                   ["🏠 工作区", "模块变更比例统计", "MCP Client", "Chroma Search", "模块识别", "mcp server config", "批量导入监控"],
                   index=0)

if page == '🏠 工作区':
    st.title("工作区")
    # query()

    itemlist = ''
    for item in getWorkingList():
        itemlist += ', ' + item 
    st.info('当前监控列表' + itemlist)

    # 显示当前生效的Prompt
    st.divider()
    st.subheader("当前生效的Prompt")
    st.code(getPrompt(), language="text")
    st.code(getSystemPrompt(), language="text")

    data = []
    totaltime = 0
    fasttime = 10000
    lowtime = 0
    avatime = 0
    for key in redis.hkeys(PROJECT_ISSUE_ANALYZED):
        jstr = redis.hget(PROJECT_ISSUE_ANALYZED, key)
        dictitem = json.loads(jstr)
        data.append([dictitem[ISSUE], time.asctime(time.localtime(dictitem[STARTTIME])), time.asctime(time.localtime(dictitem[FINISHTIME])), dictitem[FINISHTIME] - dictitem[STARTTIME], dictitem[RESULT], dictitem[CONTENT]])
        spend = dictitem[FINISHTIME] - dictitem[STARTTIME]
        if spend < fasttime:
            fasttime = spend
        if spend > lowtime:
            lowtime = spend
        totaltime += spend
    if len(redis.hkeys(PROJECT_ISSUE_ANALYZED)) > 0:
        avatime = totaltime / len(redis.hkeys(PROJECT_ISSUE_ANALYZED))
    # 创建一个随机数据的DataFrame
    df = pd.DataFrame(
        data, columns=(ISSUE,STARTTIME,FINISHTIME,'用时',RESULT,CONTENT)
    )

    st.divider()
    # 使用st.table展示DataFrame
    st.header('分析结果')
    st.dataframe(df, 
                #  use_container_width=True, 
                 hide_index=True, 
                 height=400,
                 column_config={
                    "长文本列": st.column_config.TextColumn(
                        width="large",
                        help="自动换行文本列"
                    )
                })
    
    st.write(f'平均用时：{avatime}')
    st.write(f'最快用时：{fasttime}')
    st.write(f'最慢用时：{lowtime}')


    st.divider()
    st.header("自选统计、component变更统计")
    
    total = 0
    match = 0
    data1 = []
    for key in redis.hkeys(USER_GIVEN_ISSUE_ANALYZED):
        total = total + 1
        jstr = redis.hget(USER_GIVEN_ISSUE_ANALYZED, key)
        dictitem = json.loads(jstr)
        data1.append([dictitem[ISSUE], 
                     dictitem[ANALYZEMODULE], 
                     dictitem[REALMODULE], 
                     dictitem[MATCH], 
                     dictitem[RESULT], 
                     dictitem[CONTENT]])
        spend = dictitem[FINISHTIME] - dictitem[STARTTIME]
        if dictitem[MATCH]:
            match = match + 1
    
    # 创建一个随机数据的DataFrame
    df1 = pd.DataFrame(
        data1, columns=(ISSUE,ANALYZEMODULE,REALMODULE,MATCH,RESULT,CONTENT)
    )

    st.dataframe(df1, 
                #  use_container_width=True, 
                 hide_index=True, 
                 height=400,
                 column_config={
                    "长文本列": st.column_config.TextColumn(
                        width="large",
                        help="自动换行文本列"
                    )
                })

    st.write(f'总共分析了{total}个问题，有{match}个分析正确，正确率{match / total}')

    st.divider()
    col1, col2 = st.columns(2)
    
    # 获取由FO(组件负责人)变更的数据
    fo_changes = redis.smembers(COMPONENTS_CHANGE_BY_FO_SET)
    fo_count = len(fo_changes) if fo_changes else 0
    
    # 获取由开发人员变更的数据
    dev_changes = redis.smembers(COMPONENTS_CHANGE_BY_DEV_SET)
    dev_count = len(dev_changes) if dev_changes else 0
    
    # 显示数据统计
    with col1:
        st.subheader("组件负责人变更")
        st.metric(label="变更数量", value=fo_count)
        if fo_changes:
            with st.expander("查看详细信息"):
                for issue in fo_changes:
                    st.write(f"[{issue}](https://jira.nts.neusoft.local/browse/{issue})")
    
    with col2:
        st.subheader("开发人员变更")
        st.metric(label="变更数量", value=dev_count)
        if dev_changes:
            with st.expander("查看详细信息"):
                for issue in dev_changes:
                    st.write(f"[{issue}](https://jira.nts.neusoft.local/browse/{issue})")
    
    # 饼图显示比例
    if fo_count > 0 or dev_count > 0:
        st.subheader("组件变更比例")
        data = {
            "类型": ["组件负责人变更", "开发人员变更"],
            "数量": [fo_count, dev_count]
        }
        st.bar_chart(data, x="类型", y="数量")


    # showSpecimen()
    showCommonSpecimen()

if page == 'MCP Client':
    showMcpClient()

if page == "Chroma Search":
    # query()
    st.divider()
    queryMuti()

if page == '模块识别':
    moduleRecognition()

if page == "模块变更比例统计":
    showPercentComponentChange()

if page == "mcp server config":
    mcpServerConfig()    

if page == "批量导入监控":
    bulkImport()

if __name__ == "__main__":
   print("-------------------------------------------------")
