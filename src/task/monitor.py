#!/usr/bin/env python3
# coding:utf-8

from datetime import datetime, timedelta
from src.helper import feishu, JiraSy
from src.utils import settings, findlog, coreData
from src.db.database import standalone_session
from src.utils.config import settings as config
import asyncio
import requests

def delete_task(monitorSettings: settings.LlmMonitoringSettings):
    logPath = monitorSettings.analyzedLogPath
    maxLogNumber = monitorSettings.analyzedLogMaxNumber
    findlog.delete_oldest_folder(logPath, maxLogNumber)

# ======================================================================================
# Monitoring Logic
# ======================================================================================

async def check_stuck_tasks(setting: settings.LlmMonitoringSettings, jiraConfig: settings.JiraSettings, db):
    try:
        syJira = JiraSy.JiraImp(jira_server=str(jiraConfig.url), username=jiraConfig.username, password=jiraConfig.password)
        stuck_pending_timeout = timedelta(minutes=setting.pendingTimeout)
        stuck_bert_timeout = timedelta(minutes=setting.bertTimeout)
        stuck_llm_timeout = timedelta(minutes=setting.llmTimeout)
        stuck_tool_timeout = timedelta(minutes=setting.toolTimeout)
        url = str(setting.webhookUrl)
        secret = setting.apiKey
        active_tasks = coreData.get_active_core_data(db=db)

        forwardUrl = str(setting.forwardUrl)
        proxyName = setting.proxyName
        proxyPasswd = setting.proxyPasswd

        if not active_tasks:
            return

        pendingList = []
        bertingList = []
        llmList = []
        toolList = []
        issues = []

        jql = f'assignee = {jiraConfig.username} AND project = {jiraConfig.project} AND  issuetype="Product bug"  AND  resolution = unresolved ORDER BY priority DESC, created ASC'
        issues = syJira.getIssuesByJql(jql)

        for task in active_tasks:
            if await syJira.getCurrentAssignee(task.id) != jiraConfig.username:
                continue

            if task.id in issues:
                issues.remove(task.id)

            # 1. Check for tasks stuck in PENDING status
            if task.status == coreData.Status.PENDING.value and datetime.fromtimestamp(task.created_at) < datetime.now() - stuck_pending_timeout:
                text = """检测到本件任务长时间未上传日志，系统已自动将任务退回至“待重现”状态，请确认是否正常处理。日志字段规则如下：
'-'  表示等待日志上传
'null' 表示无日志
'有效路径' 表示已上传日志
                """
                pendingList.append(task.id)
                reporter = syJira.getReporter(task.id)
                syJira.addComment(task.id, text)
                syJira.transitionsIssue(task.id, "To Repro")
                syJira.assigneeIssue(task.id, reporter)

            # 2. Check for tasks stuck in BERT analysis
            if task.bert_start > 0 and task.bert_end == 0 and datetime.fromtimestamp(task.bert_start) < datetime.now() - stuck_bert_timeout:
                bertingList.append(task.id)

            sub_task = coreData.get_latest_core_data_sub_by_main_id_ex(db=db, main_id=task.id)
            if not sub_task:
                continue

            # 3. Check for tasks stuck in LLM analysis
            if sub_task.llm_start > 0 and sub_task.llm_end == 0 and datetime.fromtimestamp(sub_task.llm_start) < datetime.now() - stuck_llm_timeout:
                llmList.append(task.id)

            # 4. Check for tasks stuck in Tool analysis
            if sub_task.analyze_start > 0 and sub_task.analyze_end == 0 and datetime.fromtimestamp(sub_task.analyze_start) < datetime.now() - stuck_tool_timeout:
                toolList.append(task.id)
        
        if pendingList:
            message = f"JIRA ID：{','.join(pendingList)}，等待上传日志已超时"
            build_feishu_message(message, url, secret, notify=True, title="LLM monitor", forwardUrl=forwardUrl, name=proxyName, passwd=proxyPasswd)
        
        if bertingList:
            message = f"JIRA ID：{','.join(bertingList)}，bert分析已超时"
            build_feishu_message(message, url, secret, notify=True, title="LLM monitor", forwardUrl=forwardUrl, name=proxyName, passwd=proxyPasswd)

        if llmList:
            message = f"JIRA ID：{','.join(llmList)}，AI选择工具已超时"
            build_feishu_message(message, url, secret, notify=True, title="LLM monitor", forwardUrl=forwardUrl, name=proxyName, passwd=proxyPasswd)

        if toolList:
            message = f"JIRA ID：{','.join(toolList)}，MCP分析已超时"
            build_feishu_message(message, url, secret, notify=True, title="LLM monitor", forwardUrl=forwardUrl, name=proxyName, passwd=proxyPasswd)

        if issues:
            message = f"JIRA ID：{','.join(issues)}，没有收到WebHook"
            build_feishu_message(message, url, secret, notify=True, title="Jira monitor", forwardUrl=forwardUrl, name=proxyName, passwd=proxyPasswd)

        now = datetime.now()    
        if now.minute == 0 or now.minute == 30:
            message = f"""
            等待上传日志任务数：{len(pendingList)}
            bert分析任务数：{len(bertingList)}
            LLM分析任务数：{len(llmList)}
            MCP分析任务数：{len(toolList)}
            """
            build_feishu_message(message, url, secret, notify=False, title="Jira monitor",forwardUrl=forwardUrl, name=proxyName, passwd=proxyPasswd)
    except Exception as e:
        print(f"An error occurred in check_stuck_tasks: {e}")

def build_feishu_message(message, url, secret, notify=False, title="Jira monitor", forwardUrl="", name="", passwd=""):
    try:
        if not forwardUrl:
            feishu.send_message(message, url, name, passwd, secret, notify=notify, title=title)
        else:
            data = {
                "secret": secret,
                "url": url,
                "message": message,
                "proxy_name":name,
                "proxy_passwd":passwd,
                "notify": notify,
                "title":title,
            }
            response = requests.post(forwardUrl, json=data)
            response.raise_for_status()
    except Exception as e:
        print(f"send feishu error {str(e)}")
            

# ======================================================================================
# Main Loop
# ======================================================================================

last_bert_correct_run = None

async def main(arg):
    """Main function to run the monitoring loop."""
    global last_bert_correct_run
    print("Starting the monitoring service...")
    while True:
        cycle_seconds = 60
        try:
            with standalone_session() as db:
                setting = settings.get_llm_monitoring_settings(db=db)
                jiraConfig = settings.get_jira_settings(db=db)
                if setting and setting.monitoringCycle:
                    cycle_seconds = setting.monitoringCycle * 60
                await check_stuck_tasks(setting, jiraConfig, db)
                delete_task(setting)

                # Weekly task at Sunday 24:00 (Monday 00:00)
                now = datetime.now()
                if now.weekday() == 0 and now.hour == 0 and (last_bert_correct_run is None or last_bert_correct_run.date() != now.date()):
                    from src.task.bert_correct import collect_bert_stats, import_bert_weekly_stats
                    print(f"Running weekly task: collect_bert_stats at {now}")
                    try:
                        collect_bert_stats(db)
                        import_bert_weekly_stats(db)
                        last_bert_correct_run = now
                    except Exception as e:
                        print(f"Error running weekly task collect_bert_stats: {e}")
    
        except Exception as e:
            print(f"ERROR: An exception occurred during the monitoring cycle: {e}")
        await asyncio.sleep(cycle_seconds)

