
from fastapi import APIRouter, Request, status, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from src.helper import JiraSy, Ollama, Log, feishu
from src.utils import smbcopyer, findlog, settings, coreData
from src.utils.config import settings as config
from src.utils.text_utils import *
from src.db.database import get_db
from Mcp.client import mcpClient
from typing import Optional, List, Dict
from pydantic import BaseModel
import requests
import os
import traceback
import json
import time

class TicketProgressChangeNull(Exception): pass
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
    db: Session = Depends(get_db)
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
                    await handle_issue_update(payload, db)
        else:
            Log.info(f"{payload.issue.get("key")}, {webhook_event}, no change log, ")
    else:
        Log.info(f"Unhandled event type: {webhook_event}")

    return JSONResponse(
        content={"status": "success", "message": "Webhook received"},
        status_code=status.HTTP_200_OK
    )

async def handle_issue_update(payload: JiraWebhookData, db: Session):
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
        jiraConfig = settings.get_jira_settings(db)
        syJira = JiraSy.JiraImp(jira_server=str(jiraConfig.url), username=jiraConfig.username, password=jiraConfig.password)
        customer = syJira.getReqByCustomer(issue_key)
        ComponentsLead = syJira.getProjectComponentsLead(project=jiraConfig.project)
        interfaceMan = ComponentsLead.get(component_current) if component_current else ""
        path = syJira.getLogPath(issue_key)

        preCheck(issue_key, jiraConfig, component_current, path, summary, description, fields, db)
        if getNeedBertStatus(issueKey=issue_key, syJira=syJira):
            component_bert = getComponent(issue_key, summary, description, component_current, syJira, db)
            interfaceMan = ComponentsLead.get(component_bert) if component_bert else ""
            component_current = component_bert

        fo = feishu.getFunctionOwnerByComponent(component_current,customer)
        Log.info(f"{fo} -> get Function Owner by component: {component_current}, customer: {customer}")
        syJira.setCustomFieldValueByName(issue_key, config.JIRA_CUSTOM_FIELD_FUNCTION_OWNER, fo)

        Log.info(f"{issue_key} interfaceMan: {interfaceMan}")
        core_data_sub = coreData.CoreDataSub()
        core_data_sub.main_id = issue_key
        core_data_sub = coreData.save_core_data_sub(core_data_sub, db)
        client = await getMCPConnection(issue_key, component_current, core_data_sub, db)
        response = await analyzeIssue(issue_key, client, summary, description, fields, path, syJira, core_data_sub, db)
        Log.info(f"{issue_key} -> 解析完成，更新JIRA")
        resDict = json.loads(response)
        comment = resDict['Comment']
        if await syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
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

        if resDict.get("LLM_Model") and resDict['LLM_Model'] != None:
            core_data_sub.tool_llm_name = resDict['LLM_Model']

        if resDict.get("Tokens") and resDict['Tokens'] != None:
            core_data_sub.tool_llm_tokens = resDict['Tokens']

        if resDict.get("TagName") and resDict['TagName'] != None:
            core_data_sub.tool_llm_tag = resDict['TagName']

        core_data = coreData.get_core_data_main(issue_key, db)
        core_data.status = coreData.Status.DONE.code
        coreData.save_core_data_main(issue_key, core_data, db)
        core_data_sub.status = coreData.Status.DONE.code
        coreData.save_core_data_sub(core_data_sub, db)

    except TicketProgressChangeNull as e:
        Log.info(f"{issue_key} TicketProgressChangeNull: interfaceMan = {interfaceMan}")
        if await syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
            syJira.addComment(issue_key, str(e))
            syJira.assigneeIssue(issue_key, interfaceMan)
            paths = extract_paths(description)
            if paths:
                path = paths[0].get('full_path')
                syJira.setCustomFieldValue(issue_key, config.JIRA_CUSTOM_FIELD_LINK_TO_PATH, path)
    except TicketTestError as e:
        Log.info(f"{issue_key} TicketTestError: {str(e)}")
        if await syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
            syJira.addComment(issue_key, str(e))
            syJira.transitionsIssue(issue_key, to_status="To Repro")
            syJira.assigneeIssue(issue_key, from_user)
    except TicketError as e:
        Log.info(f"{issue_key} Ticket: interfaceMan = {interfaceMan}")
        if await syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
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
        if syJira and await syJira.getCurrentAssignee(issue_key) == jiraConfig.username:
            syJira.addComment(issue_key, str(error))
            syJira.assigneeIssue(issue_key, interfaceMan)
        core_data = coreData.get_core_data_main(issue_key, db)
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = str(e)
        coreData.save_core_data_main(issue_key, core_data, db)
        if core_data_sub:
            core_data_sub.status = coreData.Status.EXCEPTION.code
            core_data_sub.exception_string = str(e)
            coreData.save_core_data_sub(core_data_sub, db)
        Log.info(error)

def preCheck(issue_key, jiraConfig, component_current, path, summary, description, fields, db):
    current_assignee = fields.get('assignee').get('name')
    core_data = coreData.get_core_data_main(issue_key, db)
    if core_data.id == "":
        core_data.id = issue_key
        core_data.created_at = time.time()
        core_data.status = coreData.Status.NEW.code

    coreData.save_core_data_main(issue_key, core_data, db)

    if current_assignee != jiraConfig.username:
        Log.info(f"{issue_key} 当前处理用户不是T3000，不再处理")
        core_data.status = coreData.Status.NOT_ANALYZE_TRANSFER.code
        coreData.save_core_data_main(issue_key, core_data, db)
        raise TicketProgress("当前处理用户不是T3000，不再处理")

    if any(keyword.lower() in summary.lower() for keyword in jiraConfig.keywords) or \
       any(keyword.lower() in description.lower() for keyword in jiraConfig.keywords):
        Log.info(f"{issue_key} 非NEU SDK项目，直接转给模块Lead处理")
        core_data.status = coreData.Status.NOT_ANALYZE_NOT_SDK_PROJECT.code
        coreData.save_core_data_main(issue_key, core_data, db)
        if not component_current:
            Log.info(f"{issue_key} 非NEU 且没有模块信息，转回给测试")
            raise TicketTestError(f"没有模块信息")
        raise TicketError("")

    if 'Performance' in component_current:
        Log.info(f"{issue_key} 是Performance的票，不处理")
        core_data.status = coreData.Status.NOT_ANALYZE_PERFORMANCE.code
        coreData.save_core_data_main(issue_key, core_data, db)
        raise TicketProgressChangeNull("")

    if "subticket" in summary.lower() or "clone" in summary.lower():
        Log.info(f"{issue_key} 是Clone的票，不处理")
        core_data.status = coreData.Status.NOT_ANALYZE_CLONE.code
        coreData.save_core_data_main(issue_key, core_data, db)
        raise TicketError("")

    if path.lower() == 'null':
        if not component_current:
            Log.info(f"{issue_key} 日志路径为null，且模块为空，转回给测试")
            raise TicketTestError(f"日志路径为null，且模块为空")

        core_data.status = coreData.Status.NOT_ANALYZE_LOG_NULL.code
        coreData.save_core_data_main(issue_key, core_data, db)
        Log.info(f"{issue_key} 无日志，请模块Lead直接处理")
        raise TicketProgressChangeNull(f"无日志，请模块Lead直接处理")

    now = time.time()
    if (core_data.status == coreData.Status.WATING_BERT.code or 
        core_data.status == coreData.Status.WATING_LLM.code or 
        core_data.status == coreData.Status.WATING_TOOL.code) and (now - core_data.created_at < 1800):
        Log.info(f"{issue_key} 正在处理，不处理重复消息")
        raise TicketProgress("正在处理，不处理重复消息")

    if path == '-' or not path:
        core_data.status = coreData.Status.PENDING.code
        coreData.save_core_data_main(issue_key, core_data, db)
        Log.info(f"{issue_key}日志路径为-，等待日志上传")
        raise TicketProgress("等待日志上传")

def getNeedBertStatus(issueKey, syJira:JiraSy.JiraImp):
    value = syJira.getReqByCustomer(issueKey)
    if value and (value == "CHERY" or value == "GDC-Base"):
        return False
    
    return True

async def getMCPConnection(issue_key, component, core_data_sub:coreData.CoreDataSub, db) -> mcpClient.MCPClient:
    mcpServers = settings.get_jira_modules(db)
    available_servers = [server.name for server in mcpServers if server.isEnabled]
    core_data = coreData.get_core_data_main(issue_key, db)
    if component not in available_servers:
        Log.info(f"{issue_key} {component} 没有注册，只分配模块")
        core_data.status = coreData.Status.DONE_BERT.code
        coreData.save_core_data_main(issue_key, core_data, db)
        raise TicketError(f"T3000已分配模块，请模块Lead处理")

    isEnabled, mcpServer = next(((server.isEnabled, server.url) for server in mcpServers if server.name == component), (False, ""))
    Log.info(f"{issue_key} {mcpServer} 启用状态：{isEnabled}")
    client = mcpClient.MCPClient("mcpone")
    core_data.status = coreData.Status.MCP_CONNECTING.code
    coreData.save_core_data_main(issue_key, core_data, db)
    core_data_sub.status = coreData.Status.MCP_CONNECTING.code
    core_data_sub.component_of_tool = component
    coreData.save_core_data_sub(core_data_sub, db)
    if not await mcpClient.connect(client, str(mcpServer)):
        Log.info(f"{issue_key} {mcpServer}mcpClient.connect 失败")
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = f"无法连接到MCP server，请检查！地址：{mcpServer}"
        coreData.save_core_data_main(issue_key, core_data, db)
        core_data_sub.status = coreData.Status.EXCEPTION.code
        core_data_sub.exception_string = f"无法连接到MCP server，请检查！地址：{mcpServer}"
        coreData.save_core_data_sub(core_data_sub, db)
        raise TicketError(f"{component} 无法连接到MCP server，请检查！地址：{mcpServer}")

    return client

async def getInfoFromTicket(localSavePath, description, path, syJira, issue_key, core_data_sub:coreData.CoreDataSub, db):
    logcat_files, dlt_files, crash_files, anr_files = [], [], [], []
    attached_log = False
    os.makedirs(localSavePath, exist_ok=True)
    isDownloaded = False
    core_data = coreData.get_core_data_main(issue_key, db)
    if path.lower() == 'attached':
        attached_log = syJira.download_attachment(issue_key, localSavePath)
        isDownloaded = True
    else:
        paths = extract_paths(path)
        if not paths:
            Log.error(f"{issue_key} 没有找到日志路径")
            core_data.status = coreData.Status.EXCEPTION.code
            core_data.exception_string = f"没有找到日志路径"
            coreData.save_core_data_main(issue_key, core_data, db)
            core_data_sub.status = coreData.Status.EXCEPTION.code
            core_data_sub.exception_string = f"没有找到日志路径"
            coreData.save_core_data_sub(core_data_sub, db)
            raise TicketError(f"没有找到日志路径")

        Log.info(f"{issue_key} 获取路径 = {paths}")

        first_path = paths[0]
        try:
            isDownloaded = await smbcopyer.copy_file_via_smb(
                server_ip=first_path['ip'],
                share_name=first_path['share_name'],
                remote_base_path=first_path['path'],
                local_base_path=localSavePath,
                db=db,
            )
        except Exception as e:
            Log.error(f"{issue_key} SMB文件同步失败: {e}")
            core_data.status = coreData.Status.EXCEPTION.code
            core_data.exception_string = f"SMB文件同步失败: {e}"
            coreData.save_core_data_main(issue_key, core_data, db)
            core_data_sub.status = coreData.Status.EXCEPTION.code
            core_data_sub.exception_string = f"SMB文件同步失败: {str(e)}"
            coreData.save_core_data_sub(core_data_sub, db)
            raise TicketError(f"SMB文件同步失败: {str(e)}")
    
    logcat_files, dlt_files, crash_files, anr_files = findlog.find_logcat_files(localSavePath, isDownloaded)
    if not logcat_files and not dlt_files and not attached_log:
        Log.error(f"{issue_key} 解压后没有找到有效日志文件，请手动检查压缩包是否有正确日志")
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = f"解压后没有找到有效日志文件，请手动检查压缩包是否有正确日志"
        coreData.save_core_data_main(issue_key, core_data, db)
        core_data_sub.status = coreData.Status.EXCEPTION.code
        core_data_sub.exception_string = f"解压后没有找到有效日志文件，请手动检查压缩包是否有正确日志"
        coreData.save_core_data_sub(core_data_sub, db)
        raise TicketError(f"解压后没有找到有效日志文件，请手动检查压缩包是否有正确日志")

    time = extract_and_format_time(description)
    return time, logcat_files, dlt_files, crash_files, anr_files

async def getInfoFromComments(tool_name, fields, tools, localSavePath, db):
    comments = fields.get("comment").get("comments")
    time = ''
    tool_name = tool_name
    logcat_files, dlt_files, crash_files, anr_files = [], [], [], []

    if not comments:
        return time, tool_name, logcat_files, dlt_files, crash_files, anr_files

    try:
        last_comment = comments[-1]
        author = last_comment.get("author")
        if not author:
            return time, tool_name, logcat_files, dlt_files, crash_files, anr_files

        name = author.get("name")
        if name == "Naiser-T3000":
            return time, tool_name, logcat_files, dlt_files, crash_files, anr_files

        body = last_comment.get("body")
        for tool in tools:
            if tool.name in body:
                tool_name = tool.name
                Log.info(f"tool from comment = {tool.name}")
                break
        time = extract_and_format_time(body)
        comment_paths = extract_paths(body)
        if comment_paths:
            for path in comment_paths:
                isDownloaded = await smbcopyer.copy_file_via_smb(
                    server_ip=path['ip'],
                    share_name=path['share_name'],
                    remote_base_path=path['path'],
                    local_base_path=localSavePath,
                    db=db,
                )
            logcat_files, dlt_files, crash_files, anr_files = findlog.find_logcat_files(localSavePath, isDownloaded)
    except Exception as e:
        raise TicketError(f"SMB文件同步失败: {str(e)}")

    return time, tool_name, logcat_files, dlt_files, crash_files, anr_files

def getComponent(issue_key, summary, description, current_component, syJira, db):
    summary = remove_brackets_and_content(summary)
    core_data = coreData.get_core_data_main(issue_key, db)
    componentsList = ["BL_Activation", "BL_DBU", "BL_DI_POI_SDS", "BL_Guidance", "HMI", "BL_MapViewer", "BL_Positioning","BL_RouteCalculation", "BL_System", "BL_TI"]
    if core_data.is_bert:
        if current_component not in componentsList:
            Log.error(f"{issue_key} T3000已经分析过模块，目前模块为手动指定，且不在T3000的分析范围，请模块lead分")
            raise TicketError(f"T3000已经分析过模块，目前模块为手动指定，且不在T3000的分析范围，请模块lead分析")
        return current_component
    try:
        core_data.bert_start = time.time()
        core_data.status = coreData.Status.WATING_BERT.code
        coreData.save_core_data_main(issue_key, core_data, db)
        component_bert = getComponentFromBertEx(summary, description, db)
        core_data.bert_end = time.time()
        core_data.is_bert = True
        core_data.bert_component = component_bert
        coreData.save_core_data_main(issue_key, core_data, db)
        component = getComponentReal(component_bert)
        syJira.changeIssueComponents(issue_key, [component])
        Log.info(f"{issue_key} 从bert获取模块 = {component}")
    except Exception as e:
        Log.info(f"{issue_key} bert error = {str(e)}")
        core_data.bert_end = time.time()
        core_data.status = coreData.Status.EXCEPTION.code
        core_data.exception_string = str(e)
        coreData.save_core_data_main(issue_key, core_data, db)
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

def getComponentFromBertEx(summary, description, db):
    setting_url = settings.get_bert_settings(db)
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

def build_prompt(issue_key, summary, time, version, car_type):
    return f"""
# 你是一名优秀的软件工程师，擅长解决各类bug。
## 你的任务如下：
根据Bug描述解析问题，必要时使用tools提供的工具
## 用户的输入如下：
bug描述:{summary}
bugID:{issue_key}
问题发生时间:{time}
apk_version:{version}
车型:{car_type}
dlt日志地址:1.dlt
logcat日志地址：1.txt
crash日志地址：1.txt
anr日志地址：1.txt
        """.strip()

async def analyzeIssue(issue_key, client, summary, description, fields, path, syJira, core_data_sub:coreData.CoreDataSub, db: Session):
    summary = remove_brackets_and_content(summary)
    ollamaSettings = settings.get_ollama_settings(db)
    model = ollamaSettings.model if ollamaSettings.model else "qwen3:30b-a3b"
    monitorSetting = settings.get_llm_monitoring_settings(db)
    localSavePath = f'{monitorSetting.analyzedLogPath}/{issue_key}'
    version = syJira.getProductVersion(issue_key)
    core_data = coreData.get_core_data_main(issue_key, db)
    core_data.status = coreData.Status.PREPARING_LOG.code
    coreData.save_core_data_main(issue_key, core_data, db)
    core_data_sub.status = coreData.Status.PREPARING_LOG.code
    coreData.save_core_data_sub(core_data_sub, db)
    time_in_ticket, logcat_files, dlt_files, crash_files, anr_files = await getInfoFromTicket(localSavePath, description, path, syJira, issue_key, core_data_sub, db)
    response = ''
    syJira.transitionsIssue(issue_key, to_status="To Analysis")
    car_type = syJira.getReqByCustomer(issue_key)
    last_analyze = coreData.get_latest_core_data_sub_by_main_id(db=db, main_id=issue_key)
    Log.info(f"{issue_key} 上一次调用tool = {last_analyze.tool_name if last_analyze else '无'},id = {last_analyze.id if last_analyze else '无'}")
    if last_analyze and last_analyze.tool_name:
        time_, tool_name_, logcat_files_, dlt_files_, crash_files_, anr_files_ = await getInfoFromComments(last_analyze.tool_name, fields, client.tools.tools, localSavePath, db)
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
                elif 'anr' in key:
                    arguments[key] = anr_files_ if anr_files_ else anr_files
                elif 'time' in key:
                    arguments[key] = time_ if time_ else time_in_ticket
                elif 'id' in key:
                    arguments[key] = issue_key
                elif 'summary' in key:
                    arguments[key] = summary
                elif 'version' in key:
                    arguments[key] = version
                elif 'car_type' in key:
                    arguments[key] = car_type
                else:
                    arguments[key] = None
            core_data.status = coreData.Status.WATING_TOOL.code
            coreData.save_core_data_main(issue_key, core_data, db)
            core_data_sub.status = coreData.Status.WATING_TOOL.code
            core_data_sub.analyze_start = time.time()
            core_data_sub.tool_name = tool.name
            coreData.save_core_data_sub(core_data_sub, db)
            response = await mcpClient.call(client, tool.name, arguments)
            core_data_sub.analyze_end = time.time()
            coreData.save_core_data_sub(core_data_sub, db)
    if not response:
        Log.info(f"{issue_key} -> 调用模型{model},分析问题")

        core_data.status = coreData.Status.WATING_LLM.code
        coreData.save_core_data_main(issue_key, core_data, db)
        core_data_sub.status = coreData.Status.WATING_LLM.code
        core_data_sub.llm_start = time.time()
        coreData.save_core_data_sub(core_data_sub, db)
        response = await Ollama.chat_with_tools(prompt=build_prompt(issue_key, summary, time_in_ticket, version, car_type), 
                                            modelname=model, 
                                            db=db,
                                            tools=client.tools)
        core_data_sub.llm_end = time.time()
        core_data_sub.llm_name = model
        core_data_sub.llm_success = True if response["done"] == "True" else False
        core_data_sub.llm_tokens = response["eval_count"]
        coreData.save_core_data_sub(core_data_sub, db)

        if response["message"].get('tool_calls'):
            tool_calls = response["message"]['tool_calls']
            for call in tool_calls:
                Log.info(f"{issue_key} tool: {call['function'].name}, arg: {call['function'].arguments}")
                fun = call['function'].name
                arguments = call['function'].arguments
                core_data_sub.tool_name = fun
                core_data_sub.analyze_start = time.time()
                core_data_sub.status = coreData.Status.WATING_TOOL.code
                coreData.save_core_data_sub(core_data_sub, db)
                core_data.status = coreData.Status.WATING_TOOL.code
                coreData.save_core_data_main(issue_key, core_data, db)
                for key in arguments.keys():
                    if 'android' in key:
                        arguments[key] = logcat_files if logcat_files else []
                    if 'dlt' in key:
                        arguments[key] = dlt_files if dlt_files else []
                    if 'crash' in key:
                        arguments[key] = crash_files if crash_files else []
                    if 'anr' in key:
                        arguments[key] = anr_files if anr_files else []
                response = await mcpClient.call(client, fun, arguments)
                core_data_sub.analyze_end = time.time()
                core_data_sub.is_analyzed = True
                coreData.save_core_data_sub(core_data_sub, db)
        else:
            src = {"Comment":response["message"]["content"]}
            response = json.dumps(src)
    return response
