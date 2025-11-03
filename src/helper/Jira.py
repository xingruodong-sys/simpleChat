from jira import JIRA, JIRAError
from urllib3.exceptions import InsecureRequestWarning
import warnings
import requests
from requests.auth import HTTPBasicAuth
import urllib3
from datetime import datetime
import json

jira_server = "https://naisjira.neusoft.com"
username = "xingrd"
password = "1qaz!QAZ"
linkToPath = 'customfield_12010'
project = "NMASDK"
warnings.simplefilter('ignore', InsecureRequestWarning)
urllib3.disable_warnings()

try:
    jira = JIRA(server=jira_server, basic_auth=(username, password), options={'verify': False})
except Exception as e:
    print('jira 初始化错误：')

def getLogPath(issueKey:str) -> str:
    issue = jira.issue(issueKey)
    path = issue.fields.__dict__[linkToPath]
    if path is not None:
        network_path = r'' + path
    else:
        network_path = r'' + issue.fields.description.split('\n')[-1]
    return network_path

def addComment(issueKey:str, comment:str) -> None:
    jira.add_comment(issueKey, comment)

def getIssueContent(issueKey:str, withContent:bool = False) -> str:
    """
    get the summary and description from Jira
    """
    issue = jira.issue(issueKey)
    content = 'Summary:\n' + issue.fields.summary + '\n'
    content = content + 'description:\n' + issue.fields.description + '\n'
    if withContent:
        content = content + 'comments:\n'
        for com in issue.fields.comment.comments:
            content = content + com.body

    return content

def getIssueContentExt(issueKey:str) -> str:
    """
    get the summary and description from Jira
    """
    issue = jira.issue(issueKey)
    content = {
        'summary': issue.fields.summary,
        'description': issue.fields.description,
        'type': issue.fields.issuetype.name,
        "components": [c.name for c in issue.fields.components] if hasattr(issue.fields, 'components') else [],
        'comments':[]
    }
    for com in issue.fields.comment.comments:
        content['comments'].append({'name':com.author.displayName, 'body':com.body, 'created': com.created})

    return content

def getProjectComponentsLead() -> set:
    # 构造 API 请求
    api_url = f"{jira_server}/rest/api/2/project/{project}/components"
    response = requests.get(api_url, auth=HTTPBasicAuth(username, password),verify=False)

    leads = set()
    # 检查响应
    if response.status_code == 200:
        components = response.json()
        for component in components:
            component_name = component["name"]
            component_lead = component.get("lead", {}).get("name", "No Lead")
            leads.add(component_lead)
    else:
        raise Exception(response.status_code)
    return leads

def getAllIssuesOfUser(user:str) -> set:
    jql = f'assignee = {user} AND project = "Neusoft Map Auto Navi SDK" AND  issuetype="Product bug"  AND  resolution = unresolved ORDER BY priority DESC, created ASC'
    result = []
    for item in jira.search_issues(jql):
        result.append(item.key)
    return result

def getIssueFirstAssignee(issueKey:str) -> str:
    issue = jira.issue(issueKey)
    return issue.fields.assignee.name

def getIssueHistory(issue_key):
    """
    Get the history of a JIRA issue with a focus on component changes
    
    Args:
        issue_key (str): The JIRA issue key (e.g., 'NMASDK-53278')
        
    Returns:
        dict: A dictionary containing organized history information
    """
    
    try:
        # Get the issue with its changelog
        issue = jira.issue(issue_key, expand='changelog')
        
        comments = []
        for com in issue.fields.comment.comments:
            comments.append([com.author.name, com.body])
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
            'issuetype': issue.fields.issuetype.name
        }
        
        # Process the changelog histories
        if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories'):
            for history in issue.changelog.histories:
                author =  history.author.name #history.author.displayName if hasattr(history.author, 'displayName') else
                created_date = datetime.strptime(history.created.split('.')[0], "%Y-%m-%dT%H:%M:%S") if '.' in history.created else datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S%z")
                
                for item in history.items:
                    # Extract specific events - focusing on component changes
                    if item.field == 'Component' or item.field == 'components':
                        history_results["changes"].append({
                            "date": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "author": author,
                            "field": item.field,
                            "from_value": item.fromString if hasattr(item, 'fromString') and item.fromString else "None",
                            "to_value": item.toString if hasattr(item, 'toString') and item.toString else "None",
                        })
                    # Add other important changes like status, assignee, etc.
                    elif item.field in ['status', 'assignee', 'priority', 'summary', 'description']:
                        history_results["changes"].append({
                            "date": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "author": author, 
                            "field": item.field,
                            "from_value": item.fromString if hasattr(item, 'fromString') and item.fromString else "None",
                            "to_value": item.toString if hasattr(item, 'toString') and item.toString else "None",
                        })
        
        return history_results
    
    except Exception as e:
        print(f"Error retrieving issue history: {e}")
        raise e

def login():
    url = "http://10.146.12.34:30092/auth/login"
    data = {
        "username": "xingrd@neusoft.com",
        "password": "mko0MKO)"
    }

    response = requests.post(url, data=json.dumps(data))

    print(response.status_code)
    print(response.json())  # 如果返回 JSON
    return response.json()['access_token']

def authStatus(token):
    url = "http://10.146.12.34:30092/auth/status"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    print(response.status_code)
    print(response.json())  # 如果返回 JSON

def welcome(token):
    url = "http://10.146.12.34:30092/permission/welcome"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"},)
    print(response.status_code)
    print(response.json())  # 如果返回 JSON

# Example usage
if __name__ == "__main__":
    authStatus(login())
