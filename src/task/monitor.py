#!/usr/bin/env python3
# coding:utf-8

from datetime import datetime, timedelta
from src.helper import feishu, JiraSy
from src.utils import settings, findlog, coreData
from src.db import crud
from src.db.database import standalone_session
import asyncio
import requests

async def delete_task(monitorSettings: settings.LlmMonitoringSettings):
    logPath = monitorSettings.analyzedLogPath
    maxLogNumber = monitorSettings.analyzedLogMaxNumber
    findlog.delete_oldest_folder(logPath, maxLogNumber)

# ======================================================================================
# Monitoring Logic
# ======================================================================================

async def check_stuck_tasks(setting: settings.LlmMonitoringSettings):
    try:
        jiraConfig = settings.get_jira_settings()
        syJira = JiraSy.JiraImp(jira_server=str(jiraConfig.url), username=jiraConfig.username, password=jiraConfig.password)
        stuck_pending_timeout = timedelta(minutes=setting.pendingTimeout)
        stuck_bert_timeout = timedelta(minutes=setting.bertTimeout)
        stuck_llm_timeout = timedelta(minutes=setting.llmTimeout)
        stuck_tool_timeout = timedelta(minutes=setting.toolTimeout)
        url = str(setting.webhookUrl)
        secret = setting.apiKey

        forwardUrl = str(setting.forwardUrl)
        proxyName = setting.proxyName
        proxyPasswd = setting.proxyPasswd

        active_tasks = crud.get_active_core_data()

        if not active_tasks:
            return

        pendingList = []
        bertingList = []
        llmList = []
        toolList = []

        for task in active_tasks:
            if syJira.getCurrentAssignee(task.id) != jiraConfig.username:
                continue

            # 1. Check for tasks stuck in PENDING status
            if task.status == coreData.Status.PENDING.value and datetime.fromtimestamp(task.created_at) < datetime.now() - stuck_pending_timeout:
                pendingList.append(task.id)
                reporter = syJira.getReporter(task.id)
                syJira.addComment(task.id, "检查到Link to attachments字段还没有有效日志路径，请确认是否漏传。")
                syJira.transitionsIssue(task.id, "To Repro")
                syJira.assigneeIssue(task.id, reporter)

            # 2. Check for tasks stuck in BERT analysis
            if task.bert_start > 0 and task.bert_end == 0 and datetime.fromtimestamp(task.bert_start) < datetime.now() - stuck_bert_timeout:
                bertingList.append(task.id)

            # 3. Check for tasks stuck in LLM analysis
            if task.llm_start > 0 and task.llm_end == 0 and datetime.fromtimestamp(task.llm_start) < datetime.now() - stuck_llm_timeout:
                llmList.append(task.id)

            # 4. Check for tasks stuck in Tool analysis
            if task.analyze_start > 0 and task.analyze_end == 0 and datetime.fromtimestamp(task.analyze_start) < datetime.now() - stuck_tool_timeout:
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

        now = datetime.now()    
        if now.minute == 0 or now.minute == 30:
            message = f"""
            等待上传日志任务数：{len(pendingList)}
            bert分析任务数：{len(bertingList)}
            LLM分析任务数：{len(llmList)}
            MCP分析任务数：{len(toolList)}
            """
            build_feishu_message(message, url, secret, notify=False, title="Jira monitor",forwardUrl=forwardUrl, name=proxyName, passwd=proxyPasswd)
    finally:
        db.close()

def build_feishu_message(message, url, secret, notify=False, title="Jira monitor", forwardUrl="", name="", passwd=""):
    try:
        if not forwardUrl:
            feishu.send_message(message, url, secret, notify=notify, title=title)
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
            print(response.status_code)
    except Exception as e:
        print(f"send feishu error {str(e)}")
            

# ======================================================================================
# Main Loop
# ======================================================================================

async def check_stuck_tasks_main():
    """Main function to run the monitoring loop."""
    print("Starting the monitoring service...")
    while True:
        cycle_seconds = 60
        try:
            with standalone_session() as db:
                setting = settings.get_llm_monitoring_settings()
                if setting and setting.monitoringCycle:
                    cycle_seconds = setting.monitoringCycle * 60
                check_stuck_tasks(setting)
                delete_task(setting)

        except Exception as e:
            print(f"ERROR: An exception occurred during the monitoring cycle: {e}")
        await asyncio.sleep(cycle_seconds)

