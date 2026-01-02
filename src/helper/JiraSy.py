from jira import JIRA, JIRAError
from urllib3.exceptions import InsecureRequestWarning
import warnings
import requests
from requests.auth import HTTPBasicAuth
import urllib3
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
import os
from src.utils.config import settings as config
from src.helper import Log
import asyncio

warnings.simplefilter('ignore', InsecureRequestWarning)
urllib3.disable_warnings()

class JiraImp:
    def __init__(self, jira_server, username, password):
        self.jira_server = jira_server
        self.username = username
        self.password = password
        try:
            self.jira = JIRA(server=jira_server, basic_auth=(username, password), options={'verify': False}, timeout=config.JIRA_TIMEOUT, max_retries=config.JIRA_MAX_RETRIES)
        except JIRAError as e:
            Log.error('jira 初始化错误：' + str(e.status_code))

    def createIssue(self, project:str, summary:str, description:str, issuetype:str, path:str, components) -> str:
        try:
            issue_dict = {
                "project": {"key": project},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issuetype},
                config.JIRA_CUSTOM_FIELD_LINK_TO_PATH: path,
                config.JIRA_CUSTOM_FIELD_PRODUCT_VERSION: {"id":"119514"},
                "customfield_11324": {"id":"40529"},
                "customfield_10160": {"id":"10390"},
                "components": [{'name': comp if comp in ['BL_Activation', 'BL_DBU', 'BL_DI_POI_SDS', 'BL_Guidance', 'BL_MapViewer', 'BL_Positioning', 'BL_RouteCalculation', 'BL_System', 'BL_TI', 'HMI'] else 'HMI'} for comp in components]
            }
            new_issue = self.jira.create_issue(fields=issue_dict)
            return new_issue.key
        except Exception as e:
            Log.error('jira createIssue 错误：' + str(e))
            return ""

    def assigneeIssue(self, issueKey:str, user:str):
        try:
            issue = self.jira.issue(issueKey)
            issue.update(assignee={'name': user})
        except Exception as e:
            Log.error('jira 添加 assignee 错误：' + str(e))
    
    def updateFunctionOwner(self, issueKey:str, user:str):
      try:
         issue = self.jira.issue(issueKey)
         issue.update(fields={'customfield_14311': user})
      except Exception as e:
         Log.error('jira 添加 FO 错误：' + str(e))
   
    def changeIssueComponents(self, issueKey:str, components:list):
        try:
            issue = self.jira.issue(issueKey)
            issue.update(fields={'components': [{'name': comp} for comp in components]})
        except Exception as e:
            Log.error('jira 更新组件错误：' + str(e))

    def addComment(self, issueKey:str, comment:str) -> None:
        if comment:
            self.jira.add_comment(issueKey, comment)

    def getIssueContent(self, issueKey:str, withContent:bool = False) -> str:
        issue = self.jira.issue(issueKey)
        content = 'Summary:\n' + issue.fields.summary + '\n'
        content = content + 'description:\n' + issue.fields.description + '\n'
        if withContent:
            content = content + 'comments:\n'
            for com in issue.fields.comment.comments:
                content = content + com.body

        return content

    def getIssueContentExt(self, issueKey:str) -> str:
        issue = self.jira.issue(issueKey)
        content = {
            'summary': issue.fields.summary,
            'description': issue.fields.description if issue.fields.description else "None",
            'type': issue.fields.issuetype.name,
            "components": [c.name for c in issue.fields.components] if hasattr(issue.fields, 'components') else [],
            'comments': [],
        }

        for com in issue.fields.comment.comments:
            content['comments'].append({'name':com.author.displayName, 'body':com.body, 'created': com.created})

        return content

    def getProjectComponentsLead(self, project) -> set:
        # 构造 API 请求
        api_url = f"{self.jira_server}/rest/api/2/project/{project}/components"

        # 发送请求
        response = requests.get(api_url, auth=HTTPBasicAuth(self.username, self.password),verify=False)

        leads = {}
        # 检查响应
        if response.status_code == 200:
            components = response.json()
            for component in components:
                component_name = component["name"]
                component_lead = component.get("lead", {}).get("name", "No Lead")
                leads[component_name] = component_lead
        else:
            print(f"Failed to retrieve components. Status code: {response.status_code}")
        return leads

    def getIssuesByJql(self, jql:str) -> list:
        result = []
        start_at = 0
        block_size = 100
        while True:
            block = self.jira.search_issues(
                jql_str=jql,
                startAt=start_at,
                maxResults=block_size
            )
            if not block:
                break

            start_at += block_size
            for item in block:
                result.append(item.key)
        return result

    def getIssueHistory(self, issue_key):
        try:
            # Get the issue with its changelog
            issue = self.jira.issue(issue_key, expand='changelog')
            
            comments = []
            for com in issue.fields.comment.comments:
                comments.append([com.author.name, com.body, com.updated])
                # comments[com.author.name] = com.body

            # Initialize the history results
            history_results = {
                "issue_key": issue_key,
                "summary": issue.fields.summary,
                "current_status": issue.fields.status.name,
                "current_components": [c.name for c in issue.fields.components] if hasattr(issue.fields, 'components') else [],
                "reporter": issue.fields.reporter.name if hasattr(issue.fields.reporter, 'name') else "Unknown",
                "changes": [],
                'comments': comments,
                'issuetype': issue.fields.issuetype,
                'created_at': issue.fields.created
            }
            
            # Process the changelog histories
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
                for history in issue.changelog.histories:
                    author =  history.author.name #history.author.displayName if hasattr(history.author, 'displayName') else
                    # created_date = datetime.strptime(history.created.split('.')[0], "%Y-%m-%dT%H:%M:%S") if '.' in history.created else datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S%z")
                    created_date = history.created
                    for item in history.items:
                        # Extract specific events - focusing on component changes
                        if item.field == 'Component' or item.field == 'components':
                            history_results["changes"].append({
                                "date": created_date,
                                "author": author,
                                "field": item.field,
                                "from_value": item.fromString if hasattr(item, 'fromString') and item.fromString else "None",
                                "to_value": item.toString if hasattr(item, 'toString') and item.toString else "None",
                            })
                        # Add other important changes like status, assignee, etc.
                        elif item.field in ['status', 'assignee', 'priority', 'summary', 'description']:
                            history_results["changes"].append({
                                "date": created_date,
                                "author": author, 
                                "field": item.field,
                                "from_value": item.fromString if hasattr(item, 'fromString') and item.fromString else "None",
                                "to_value": item.toString if hasattr(item, 'toString') and item.toString else "None",
                            })
            
            return history_results
    
        except Exception as e:
            print(f"Error retrieving issue history: {e}")
            return None

    def upload_attachment(self, issue_key, file_path):
        try:
            issue = self.jira.issue(issue_key)
            for root, _, files in os.walk(file_path):
                for file_name in files:
                    file = Path(root) / file_name
                    self.jira.add_attachment(issue=issue, attachment=str(file))
        except Exception as e:
            Log.error(f"Error uploading attachment to JIRA: {str(e)}")

    def download_attachment(self, issue_key, destination_path):
        try:
            issue = self.jira.issue(issue_key)
            if issue.fields.attachment:
                for attachment in issue.fields.attachment:
                    with open(os.path.join(destination_path, attachment.filename), 'wb') as f:
                        f.write(attachment.get())
                return True
            else:
                return False
        except Exception as e:
            Log.error(f"Error downloading attachment from JIRA: {str(e)}")
            return False

    def transitionsIssue(self, issueKey: str, to_status: str):
        try:
            self.jira.transition_issue(issueKey, to_status)
        except Exception as e:
            return

    def getProductVersion(self, issueKey) -> str:
        version = self.getCustomFieldValue(issueKey, config.JIRA_CUSTOM_FIELD_PRODUCT_VERSION)
        return str(version) if version else ""

    def getLogPath(self, issueKey:str) -> str:
        path = self.getCustomFieldValue(issueKey, config.JIRA_CUSTOM_FIELD_LINK_TO_PATH)
        return str(path) if path else ""
   
    def getReqByCustomer(self, issueKey:str) -> str:
        property_val = self.getCustomFieldValue(issueKey, config.JIRA_CUSTOM_FIELD_REQ_BY_CUSTOMER)
        if not property_val:
            return ""

        if isinstance(property_val, list):
            return str(property_val[0]) if property_val else ""

        if isinstance(property_val, dict):
            return str(property_val.get("value", ""))

        return str(property_val)

    def getCustomFieldValue(self, issue_key: str, field_id: str) -> Optional[Any]:
        if not issue_key or not field_id:
            return None

        try:
            issue = self.jira.issue(issue_key)
            field_value = getattr(issue.fields, field_id, None)
            return field_value
        except Exception as e:
            Log.error(str(e))
            return None

    def setCustomFieldValue(self, issue_key: str, field_id: str, value):
        url = f"{self.jira_server}/rest/api/2/issue/{issue_key}"
        payload = {
            "fields": {
                field_id: value
            }
        }

        auth = HTTPBasicAuth(self.username, self.password)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.put(url, json=payload, headers=headers, auth=auth)
        Log.error(f"更新：{response.status_code}\n{response.text}")


    def setCustomFieldValueByName(self, issue_key: str, field_id: str, value):
        url = f"{self.jira_server}/rest/api/2/issue/{issue_key}"
        payload = {
            "fields": {
                field_id:{
                    "name":value
                } 
            }
        }

        auth = HTTPBasicAuth(self.username, self.password)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.put(url, json=payload, headers=headers, auth=auth)
        Log.error(f"更新：{response.status_code}\n{response.text}")

    def getReporter(self, issueKey:str):
        issue = self.jira.issue(issueKey)
        return issue.fields.reporter.name

    async def getCurrentAssignee(self, issueKey:str):
        try:
            issue = self.jira.issue(issueKey)
            return issue.fields.assignee.name
        except Exception as e:
            if "Issue Does Not Exist" in str(e):
                await asyncio.sleep(3)
                try:
                    issue = self.jira.issue(issueKey)
                    return issue.fields.assignee.name
                except Exception as e:
                    Log.error(str(e))
                    return None
