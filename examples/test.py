
async def testMCPConnect():
    from Mcp.client import mcpClient
    client = mcpClient.MCPClient("mcpone")
    server = "http://10.10.90.143:8005/mcp"
    server = "http://10.10.91.17:8000/mcp"
    res = await mcpClient.connect(client, server)
    if res:
        for tool in client.tools.tools:
            name = tool.name
            description = tool.description
            for key in tool.inputSchema['properties']:
                print(key)
    print(res)

def testBert():
    from routers.webhooks import getComponentFromBertEx
    from src.helper import JiraSy
    syjira = JiraSy.JiraImp('http://10.10.88.63:8080/', "xingrd", "mko0MKO)")
    for issue in range(290, 300):
        key = 'AINMASDK-' + str(issue)
        print(key)
        content = syjira.getIssueContentExt(key)
        summary = content['summary']
        description = content['description']
        res = getComponentFromBertEx(summary, description)
        print(res)

def testassign():
    from src.helper import JiraSy
    syjira = JiraSy.JiraImp('http://10.10.88.63:8080/', "xingrd", "mko0MKO)")
    syjira.assigneeIssue(issueKey="AINMASDK-347", user="Naiser-T3000")

def testchangeIssueComponents():
    from src.helper import JiraSy
    syjira = JiraSy.JiraImp('http://10.10.88.63:8080/', "xingrd", "1qaz!QAZ1qaz")
    components = []
    components.append("BL_DBU")
    syjira.changeIssueComponents(issueKey="AINMASDK-347", components=components)

def testCopySmbFile():
    from src.utils import smbcopyer
    smbcopyer.copy_file_via_smb(
        server_ip="10.10.88.16",
        share_name="Zeekr_8295_Bugfile",  # 共享文件夹名称
        remote_base_path="/Customer Bug/BPBK-140319",  # 共享文件夹内的路径（注意用正斜杠）
        local_base_path="./test/logs/"
    )

def test_find_logcat_files():
    from src.utils.findlog import find_logcat_files
    print(find_logcat_files("./trace/AINMASDK-55", isDownload=False))

def test_assignee():
    from src.helper import JiraSy
    # syjira = JiraSy.JiraImp('http://10.10.88.63:8080/', "xingrd", "mko0MKO)")
    syJira = JiraSy.JiraImp('http://10.10.88.63:8080/', "Naiser-T3000", "1qaz!QAZ2w")
    syJira.assigneeIssue(issueKey="AINMASDK-3228", user="xingrd")

def test_json():
    import json
    src = {'Status': True, 'Comment': 'AI解析: 未分析出有效结论，请HMI人工重新进行分析。', 'Assignee': 'zhangl-zhang', 'Issue_Key': ''}
    srcd = json.dumps(src)
    
    json.loads(srcd)

def getIssueJsonAll():
    from src.helper import JiraSy
    import json
    # https://naisjira.neusoft.com/browse/NMASDK-85203
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")

    issue = dejira.jira.issue(
            "NMASDK-62216",
            expand="issuelinks"
    )
    # issue.raw 就是完整 dict
    # print(json.dumps(issue.raw, ensure_ascii=False, indent=2))
    with open("./d.json", "w", encoding="utf-8") as f:
        json.dump(issue.raw, f, ensure_ascii=False, indent=2)

def testBertVR():
    from routers.webhooks import getComponentFromBertEx
    from src.helper import JiraSy
    import csv
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
    jql = "project = NMASDK AND component = 'Voice Recognition'"
    keys = dejira.getIssuesByJql(jql)
    datas = []
    for key in keys:
        print(key)
        content = dejira.getIssueContentExt(key)
        summary = content['summary']
        description = content['description']
        res = getComponentFromBertEx(summary, description)
        datas.append({
            "issue_key": key,
            "component": res
        })
    with open("output.csv", "w", newline="", encoding="utf-8") as f:
        if datas:  # 确保数据不为空
            writer = csv.DictWriter(f, fieldnames=["issue_key", "component"])
            writer.writeheader()  # 写表头
            writer.writerows(datas)

def getAllFields():
    from src.helper import JiraSy
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
    custom_fields = dejira.jira.fields()
    print(custom_fields[0])
    # for field in custom_fields:
        # print(field)
        # print(field["name"], field["id"])

def testComponentLead():
    from src.helper import JiraSy
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
    leads = dejira.getProjectComponentsLead()
    print(leads["DBU"])

def transition():
    from src.helper import JiraSy
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
    dejira.transitionsIssue("NMASDK-87448", "To Repro")

def testassigneeIssueDe():
    from src.helper import JiraSy
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
    dejira.assigneeIssue(issueKey="NMASDK-87448", user="xingrd")
    

def testMCP():
    from src.helper import JiraSy
    syJira = JiraSy.JiraImp('http://10.10.88.63:8080/', "Naiser-T3000", "1qaz!QAZ2w")
    jql = "assignee = 'Naiser-T3000' AND resolution = unresolved ORDER BY priority DESC, created ASC"
    issues = syJira.getIssuesByJql(jql=jql)
    for issue in issues:
        syJira.assigneeIssue(issue, "xingrd")

def testIsLogcatFile():
    from src.utils.findlog import is_logcat_file
    print(is_logcat_file("/home/lix/Code/python/naispilot/trace/AINMASDK-3729/temp_logcat_files/WTLog_2025-10-16_10-39-12/mobilelog_compress/mobilelog_compress/APLog_2025_1016_095848__19/main_log_2__2025_1016_100124"))

def testMatchTime():
    from src.utils.text_utils import extract_and_format_time
    print(extract_and_format_time("2025/07/18 07:38:21"))

async def testChat():
    from src.helper.Ollama import chat_with_tools
    print(await chat_with_tools(issue_key="AINMASDK-247",prompt="""
Looking in indexes: https://mirrors.aliyun.com/pypi/simple/ Requirement already satisfied: ollama in ./.venv/lib/python3.13/site-packages (0.5.1) Collecting ollama Downloading https://mirrors.aliyun.com/pypi/packages/b5/c1/edc9f41b425ca40b26b7c104c5f6841a4537bb2552bfa6ca66e81405bb95/ollama-0.6.0-py3-none-any.whl (14 kB) Requirement already satisfied: httpx>=0.27 in ./.venv/lib/python3.13/site-packages (from ollama) (0.28.1) Requirement already satisfied: pydantic>=2.9 in ./.venv/lib/python3.13/site-packages (from ollama) (2.11.5) Requirement already satisfied: anyio in ./.venv/lib/python3.13/site-packages (from httpx>=0.27->ollama) (4.9.0) Requirement already satisfied: certifi in ./.venv/lib/python3.13/site-packages (from httpx>=0.27->ollama) (2025.4.26) Requirement already satisfied: httpcore==1.* in ./.venv/lib/python3.13/site-packages (from httpx>=0.27->ollama) (1.0.9) Requirement already satisfied: idna in ./.venv/lib/python3.13/site-packages (from httpx>=0.27->ollama) (3.10) Requirement already satisfied: h11>=0.16 in ./.venv/lib/python3.13/site-packages (from httpcore==1.*->httpx>=0.27->ollama) (0.16.0) Requirement already satisfied: annotated-types>=0.6.0 in ./.venv/lib/python3.13/site-packages (from pydantic>=2.9->ollama) (0.7.0) Requirement already satisfied: pydantic-core==2.33.2 in ./.venv/lib/python3.13/site-packages (from pydantic>=2.9->ollama) (2.33.2) Requirement already satisfied: typing-extensions>=4.12.2 in ./.venv/lib/python3.13/site-packages (from pydantic>=2.9->ollama) (4.13.2) Requirement already satisfied: typing-inspection>=0.4.0 in ./.venv/lib/python3.13/site-packages (from pydantic>=2.9->ollama) (0.4.1) Requirement already satisfied: sniffio>=1.1 in ./.venv/lib/python3.13/site-packages (from anyio->httpx>=0.27->ollama) (1.3.1) Installing collected packages: ollama Attempting uninstall: ollama Found existing installation: ollama 0.5.1 Uninstalling ollama-0.5.1: Successfully uninstalled ollama-0.5.1 Successfully installed ollama-0.6.0 [notice] A new release of pip is available: 24.3.1 -> 25.2 [notice] To update, run: pip install --upgrade pip (.venv) lix@lix-ThinkCentre-M920t-N000:~/Code/python/naispilot$ python3 -m examples Traceback (most recent call last): File "/home/lix/Code/python/naispilot/src/helper/Ollama.py", line 157, in chat_with_tools response = client.chat( model= modelname, ...<3 lines>... timeout=timeout, ) TypeError: Client.chat() got an unexpected keyword argument 'timeout'升级到6.0还是不支持
""", modelname="qwen3:32b"))

def testGetModels():
    from src.helper import Ollama
    print(Ollama.get_modes())

def testDeleteOldFolder():
    from src.utils.findlog import delete_oldest_folder
    delete_oldest_folder("./trace", 200)


def main():
    # testMatchPath()
    # testMatchTime()
    # asyncio.run(testMCPConnect())
    # testBert()
    # testxxhash()
    # testassign()
    # testchangeIssueComponents()
    # testCopySmbFile()
    # test_find_logcat_files()
    # test_assignee()
    # test_json()
    # getIssueJsonAll()
    # testBertVR()
    # getAllFields()
    # testComponentLead()
    # transition()
    # testassigneeIssueDe()
    # testMCP()
    # testIsLogcatFile()
    # testMatchTime()
    # asyncio.run(testChat())
    # testGetModels()
    testDeleteOldFolder()
