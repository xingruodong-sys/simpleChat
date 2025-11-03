
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from src.helper import JiraSy, Ollama, Log
from src.utils import smbcopyer, findlog, settings, coreData
from src.utils.text_utils import *
from Mcp.client import mcpClient
from typing import Optional, List, Dict
from pydantic import BaseModel
import requests
import os
import traceback
import json
import time

class TicketProgress(Exception): pass
class TicketError(Exception): pass
class TicketTestError(Exception): pass

class JiraWebhookData(BaseModel):
    """Jira Webhook 数据模型"""
    webhookEvent: str
    issue: Optional[dict] = None
    user: Optional[dict] = None
    changelog: Optional[dict] = None
    comment: Optional[dict] = None

router = APIRouter()

@router.post("/jira")
async def handle_jira_webhook(
    request: Request,
    payload: JiraWebhookData,
):
    webhook_event = payload.webhookEvent

    # print(await request.body())
    if webhook_event.startswith("jira:issue_updated") or webhook_event.startswith("jira:issue_created"):
        if payload.changelog:
            Log.info(f"{payload.issue.get("key")}, issue_updated Changes:")
            for change in payload.changelog.get('items', []):
                Log.info(f" - {change.get('field')}: {change.get('fromString')} -> {change.get('toString')}")
                if (change.get('field') == 'assignee' and change.get('toString') == 'Naiser-T3000') or \
                   (change.get('field') == 'status' and change.get('toString') == 'Autotransition1') or \
                   (change.get('field') == 'Link to attachments'):
                    await handle_issue_update(payload)
        else:
            Log.info(f"{payload.issue.get("key")}, {webhook_event}, no change log, ")
    else:
        Log.info(f"Unhandled event type: {webhook_event}")

    return JSONResponse(
        content={"status": "success", "message": "Webhook received"},
        status_code=status.HTTP_200_OK
    )

async def handle_issue_update(payload: JiraWebhookData):
    response = ''
    try:
        Log.info(f"Issue updated: {payload.issue.get('key')}")
        issue_key = payload.issue.get('key')
        fields = payload.issue.get('fields')
        summary = fields.get('summary')
        components = fields.get('components')
        component_current = components[0].get('name') if components else ""
        description = fields.get('description')
        from_user = payload.user.get('name')
        jiraConfig = settings.get_jira_settings()
        syJira = JiraSy.JiraImp(jira_server=str(jiraConfig.url), username=jiraConfig.username, password=jiraConfig.password)
        ComponentsLead = syJira.getProjectComponentsLead(project=jiraConfig.project)
        interfaceMan = ComponentsLead.get(component_current) if component_current else ""
        path = syJira.getLogPath(issue_key)

        preCheck(issue_key, jiraConfig, component_current, path, summary, fields)
        if getNeedBertStatus(issueKey=issue_key, syJira=syJira):
            component = getComponent(issue_key, summary, description, component_current, syJira)
            interfaceMan = ComponentsLead.get(component) if component else ""
        Log.info(f"interfaceMan: {interfaceMan}")
        client = await getMCPConnection(issue_key, component)
        response = await analyzeIssue(issue_key, client, summary, description, fields, path, syJira)
        Log.info(f"{issue_key} -> 解析完成，更新JIRA")
        resDict = json.loads(response)
        comment = resDict['Comment']
        if syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
            if resDict.get('Assignee') and resDict['Assignee'] != None:
                syJira.assigneeIssue(issue_key, resDict['Assignee'])
            else:
                syJira.assigneeIssue(issue_key, interfaceMan)

            if resDict.get('Compoment') and resDict['Compoment'] != None:
                syJira.changeIssueComponents(issue_key, [resDict['Compoment']])

        if comment:
            MAX_COMMENT_LENGTH = 30000
            if len(comment) > MAX_COMMENT_LENGTH:
                comment = comment[:MAX_COMMENT_LENGTH]
            syJira.addComment(issue_key, comment)
        core_data = coreData.get_core_data(issue_key)
        core_data.status = coreData.Status.DONE.code
        coreData.save_core_data(issue_key, core_data)

    except TicketTestError as e:
        Log.info(f"TicketTestError: {str(e)}")
        if syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
            syJira.addComment(issue_key, str(e))
            syJira.transitionsIssue(issue_key, to_status="To Repro")
            syJira.assigneeIssue(issue_key, from_user)
    except TicketError as e:
        Log.info(f"Ticket: interfaceMan = {interfaceMan}")
        if syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
            syJira.addComment(issue_key, str(e))
            syJira.assigneeIssue(issue_key, interfaceMan)
    except TicketProgress as e:
        return
    except Exception as e:
        stack_trace = traceback.format_exc()
        if isinstance(response, str):
            error = stack_trace + "\n" + response
        else:
            error = stack_trace
        if syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
            syJira.addComment(issue_key, str(error))
            syJira.assigneeIssue(issue_key, interfaceMan)
        core_data = coreData.get_core_data(issue_key)
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = str(e)
        coreData.save_core_data(issue_key, core_data)
        Log.info(error)

def preCheck(issue_key, jiraConfig, component_current, path, summary, fields):
    current_assignee = fields.get('assignee').get('name')
    core_data = coreData.get_core_data(issue_key)
    if core_data.id == "":
        core_data.id = issue_key
        core_data.created_at = time.time()
        core_data.status = coreData.Status.NEW.code

    coreData.save_core_data(issue_key, core_data)

    if current_assignee != jiraConfig.username:
        Log.info(f"当前处理用户不是T3000，不再处理")
        coreData.save_to_not_analyzed(coreData.NOT_IN_T3000_KEY, issue_key)
        raise TicketProgress("当前处理用户不是T3000，不再处理")

    if any(keyword.lower() in summary.lower() for keyword in jiraConfig.keywords):
        if not component_current:
            Log.info(f"非NEU 且没有模块信息，转回给测试")
            raise TicketTestError(f"没有模块信息")

        Log.info(f"非NEU SDK项目，直接转给模块Lead处理")
        coreData.save_to_not_analyzed(coreData.NOT_ANALYZED_KEY, issue_key)
        raise TicketError("")

    if "issuelinks" in fields and fields.get("issuelinks"):
        Log.info(f"是Clone的票，不处理")
        raise TicketError("")

    if path.lower() == 'null':
        if not component_current:
            Log.info(f"日志路径为null，且模块为空，转回给测试")
            raise TicketTestError(f"日志路径为null，且模块为空")

        coreData.save_to_not_analyzed(coreData.NO_LOG_KEY, issue_key)
        Log.info(f"无日志，请模块Lead直接处理")
        raise TicketError(f"无日志，请模块Lead直接处理")

    now = time.time()
    if (core_data.status == coreData.Status.WATING_BERT.code or 
        core_data.status == coreData.Status.WATING_LLM.code or 
        core_data.status == coreData.Status.WATING_TOOL.code) and (now - core_data.created_at < 1800):
        Log.info(f"正在处理，不处理重复消息")
        raise TicketProgress("正在处理，不处理重复消息")

    if path == '-' or not path:
        core_data.status = coreData.Status.PENDING.code
        coreData.save_core_data(issue_key, core_data)
        Log.info(f"日志路径为-，等待日志上传")
        raise TicketProgress("等待日志上传")

def getNeedBertStatus(issueKey, syJira):
    value = syJira.getReqByCustomer(issueKey)
    if value and (value == "CHERY" or value == "GDC-Base"):
        return False
    
    return True

async def getMCPConnection(issue_key, component) -> mcpClient.MCPClient:
    mcpServers = settings.get_jira_modules()
    available_servers = [server.name for server in mcpServers if server.isEnabled]
    core_data = coreData.get_core_data(issue_key)
    if component not in available_servers:
        Log.info(f"{component} 没有注册，只分配模块")
        core_data.status = coreData.Status.DONE_BERT.code
        coreData.save_core_data(issue_key, core_data)
        raise TicketError(f"T3000已分配模块，请模块Lead处理")

    isEnabled, mcpServer = next(((server.isEnabled, server.url) for server in mcpServers if server.name == component), (False, ""))
    Log.info(f"{mcpServer} 启用状态：{isEnabled}")
    client = mcpClient.MCPClient("mcpone")
    if not await mcpClient.connect(client, str(mcpServer)):
        Log.info(f"{mcpServer}mcpClient.connect 失败")
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = f"无法连接到MCP server，请检查！地址：{mcpServer}"
        coreData.save_core_data(issue_key, core_data)
        raise TicketError(f"{component} 无法连接到MCP server，请检查！地址：{mcpServer}")

    return client

async def getInfoFromTicket(localSavePath, description, path, syJira, issue_key):
    logcat_files, dlt_files, crash_files = [], [], []
    attached_log = False
    os.makedirs(localSavePath, exist_ok=True)
    isDownloaded = False
    core_data = coreData.get_core_data(issue_key)
    if path.lower() == 'attached':
        attached_log = syJira.download_attachment(issue_key, localSavePath)
        isDownloaded = True
    else:
        paths = extract_paths(path)
        if not paths:
            Log.error(f"没有找到日志路径")
            core_data.status = coreData.Status.EXCEPTION.code
            core_data.exception_string = f"没有找到日志路径"
            coreData.save_core_data(issue_key, core_data)
            raise TicketError(f"没有找到日志路径")

        Log.info(f"获取路径 = {paths}")

        first_path = paths[0]
        try:
            isDownloaded = await smbcopyer.copy_file_via_smb(
                server_ip=first_path['ip'],
                share_name=first_path['share_name'],
                remote_base_path=first_path['path'],
                local_base_path=localSavePath
            )
        except Exception as e:
            Log.error(f"SMB文件复制失败: {e}")
            core_data.status = coreData.Status.EXCEPTION.code
            core_data.exception_string = f"SMB文件复制失败: {e}"
            coreData.save_core_data(issue_key, core_data)
            raise TicketError(f"SMB文件复制失败: {str(e)}")
    
    logcat_files, dlt_files, crash_files = findlog.find_logcat_files(localSavePath, isDownloaded)
    if not logcat_files and not dlt_files and not attached_log:
        Log.error(f"解压后没有找到有效日志文件，请手动检查压缩包是否有正确日志")
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = f"解压后没有找到有效日志文件，请手动检查压缩包是否有正确日志"
        coreData.save_core_data(issue_key, core_data)
        raise TicketError(f"解压后没有找到有效日志文件，请手动检查压缩包是否有正确日志")

    time = extract_and_format_time(description)
    return time, logcat_files, dlt_files, crash_files

async def getInfoFromComments(tool_name, fields, tools, localSavePath):
    comments = fields.get("comment").get("comments")
    time = ''
    tool_name = tool_name
    logcat_files, dlt_files, crash_files = [], [], []

    if not comments:
        return time, tool_name, logcat_files, dlt_files, crash_files

    try:
        last_comment = comments[-1]
        author = last_comment.get("author")
        if not author:
            return time, tool_name, logcat_files, dlt_files, crash_files

        name = author.get("name")
        if name == "Naiser-T3000":
            return time, tool_name, logcat_files, dlt_files, crash_files

        body = last_comment.get("body")
        for tool in tools:
            if tool.name in body:
                tool_name = tool.name
                break
        time = extract_and_format_time(body)
        comment_paths = extract_paths(body)
        if comment_paths:
            for path in comment_paths:
                isDownloaded = await smbcopyer.copy_file_via_smb(
                    server_ip=path['ip'],
                    share_name=path['share_name'],
                    remote_base_path=path['path'],
                    local_base_path=localSavePath
                )
            logcat_files, dlt_files, crash_files = findlog.find_logcat_files(localSavePath, isDownloaded)
    except (AttributeError, KeyError, TypeError) as e:
        Log.error(f"Error processing comments for issue: {str(e)}")
        return time, tool_name, logcat_files, dlt_files, crash_files

    return time, tool_name, logcat_files, dlt_files, crash_files

def getComponent(issue_key, summary, description, current_component, syJira):
    summary = remove_brackets_and_content(summary)
    core_data = coreData.get_core_data(issue_key)
    componentsList = ["BL_Activation", "BL_DBU", "BL_DI_POI_SDS", "BL_Guidance", "HMI", "BL_MapViewer", "BL_Positioning","BL_RouteCalculation", "BL_System", "BL_TI"]
    if core_data.isBert:
        if current_component not in componentsList:
            Log.error(f"T3000已经分析过模块，目前模块为手动指定，且不在T3000的分析范围，请模块lead分")
            raise TicketError(f"T3000已经分析过模块，目前模块为手动指定，且不在T3000的分析范围，请模块lead分析")
        return current_component
    try:
        core_data.bertStart = time.time()
        core_data.status = coreData.Status.WATING_BERT.code
        coreData.save_core_data(issue_key, core_data)
        component_bert = getComponentFromBertEx(summary, description)
        core_data.bertEnd = time.time()
        core_data.isBert = True
        core_data.bertComponent = component_bert
        coreData.save_core_data(issue_key, core_data)
        component = getComponentReal(component_bert)
        syJira.changeIssueComponents(issue_key, [component])
        Log.info(f"从bert获取模块 = {component}")
    except Exception as e:
        Log.info(f"bert error = {str(e)}")
        core_data.bertEnd = time.time()
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = str(e)
        coreData.save_core_data(issue_key, core_data)
        raise TicketError(f"bert服务没有识别出模块，请手动添加组件，{str(e)}")

    return component
def getComponentReal(res):
    real = {}
    real["Activation"] = "BL_Activation"
    real["DBU"] = "BL_DBU"
    real["DI_POS_SDS"] = "BL_DI_POI_SDS"
    real["Guidance"] = "BL_Guidance"
    real["HMI"] = "HMI"
    real["MapViewer"] = "BL_MapViewer"
    real["Positioning"] = "BL_Positioning"
    real["Route Calculation"] = "BL_RouteCalculation"
    real["System"] = "BL_System"
    real["TI"] = "BL_TI"
    return real.get(res, res)

def getComponentFromBertEx(summary, description):
    setting_url = settings.get_bert_settings()
    proxies = {
    "http": None,
    "https": None,
    }

    form_data = {
        'summary': summary,
        'description': description,
    }
    response = requests.post(setting_url.url, proxies=proxies, data=form_data)

    Log.info(response.content)
    return strip(response.content.decode())

def build_prompt(issue_key, summary, time, version):
    return f"""
# 你是一名优秀的软件工程师，擅长解决各类bug。
## 你的任务如下：
根据Bug描述解析问题，必要时使用tools提供的工具
## 用户的输入如下：
bug描述:{summary}
bugID:{issue_key}
问题发生时间:{time}
apk_version:{version}
dlt日志地址:1.dlt
logcat日志地址：1.txt
crash日志地址：1.txt
        """.strip()

async def analyzeIssue(issue_key, client, summary, description, fields, path, syJira):
    summary = remove_brackets_and_content(summary)
    ollamaSettings = settings.get_ollama_settings()
    model = ollamaSettings.model if ollamaSettings.model else "qwen3:30b-a3b"
    monitorSetting = settings.get_llm_monitoring_settings()
    localSavePath = f'{monitorSetting.analyzedLogPath}/{issue_key}'
    version = syJira.getProductVersion(issue_key)
    core_data = coreData.get_core_data(issue_key)
    time_in_ticket, logcat_files, dlt_files, crash_files = await getInfoFromTicket(localSavePath, description, path, syJira, issue_key)
    response = ''
    syJira.transitionsIssue(issue_key, to_status="To Analysis")
    if core_data.toolName:
        time_, tool_name_, logcat_files_, dlt_files_, crash_files_ = await getInfoFromComments(core_data.toolName, fields, client.tools.tools, localSavePath)
        Log.info(f"上一次调用tool = {tool_name_}")
        tool = next((t for t in client.tools.tools if t.name == tool_name_), None)
        if tool:
            arguments = {}
            for key in tool.inputSchema['properties']:
                if 'android' in key:
                    arguments[key] = logcat_files_ if logcat_files_ else logcat_files
                elif 'dlt' in key:
                    arguments[key] = dlt_files_ if dlt_files_ else dlt_files
                elif 'crash' in key:
                    arguments[key] = crash_files_ if crash_files_ else crash_files
                elif 'time' in key:
                    arguments[key] = time_ if time_ else time_in_ticket
                elif 'id' in key:
                    arguments[key] = issue_key
                elif 'summary' in key:
                    arguments[key] = summary
                elif 'version' in key:
                    arguments[key] = version
                else:
                    arguments[key] = None
            response = await mcpClient.call(client, tool.name, arguments)
    if not response:
        Log.info(f"{issue_key} -> 调用模型{model},分析问题")
        async def func(name, arguments:dict):
            for key in arguments.keys():
                if 'android' in key:
                    arguments[key] = logcat_files if logcat_files else []
                if 'dlt' in key:
                    arguments[key] = dlt_files if dlt_files else []
                if 'crash' in key:
                    arguments[key] = crash_files if crash_files else []
            res = await mcpClient.call(client, name, arguments)
            return res
        response = await Ollama.chat_with_tools(issue_key=issue_key, prompt=build_prompt(issue_key, summary, time_in_ticket, version), modelname=model, tools=client.tools, function=func)
    return response
