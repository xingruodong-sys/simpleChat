from src.helper import JiraSy
from src.helper.Redis import *
import time
from pathlib import Path
import shutil

def blocking_task():
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
    temp_dir = Path("./trace/tmp").resolve()
    def createIssue(keys):
        data = []
        for key in keys:
            if redis.hexists(HH_TO_SY_JIRA_HASH, key):
                sykey = redis.hget(HH_TO_SY_JIRA_HASH, key)
                data.append([key, sykey, 'Exist'])
                continue
            content = dejira.getIssueContentExt(key)
            if content['type'] != 'Product bug':
                data.append([key, 'none', 'not bug'])
                continue
            path = dejira.getLogPath(key)
            temp_dir.mkdir(parents=True, exist_ok=True)
            dejira.download_attachment(issue_key=key, destination_path=temp_dir)
            new_issue_key = dejira.createIssue("AINMASDK", content["summary"], content["description"], 'Product bug', path, content['components'])
            if new_issue_key:
                dejira.upload_attachment(new_issue_key, temp_dir)
                dejira.assigneeIssue(new_issue_key, "Naiser-T3000")
                redis.hset(HH_TO_SY_JIRA_HASH, key, new_issue_key)
                data.append([key, new_issue_key, 'Created'])
                shutil.rmtree(temp_dir)
        return data
    
    while True:
        for user in redis.lrange(WATCHING_MATES_LIST, 0, -1):
            jql = f'assignee = {user} AND project = "Neusoft Map Auto Navi SDK" AND  issuetype="Product bug"  AND  resolution = unresolved ORDER BY priority DESC, created ASC'
            issues = dejira.getIssuesByJql(jql)
            keys = []
            if user == 'qiuye':
                keys = []
                for issue in issues:
                    content = dejira.getIssueContentExt(issue)
                    if 'DBU' in content['components']:
                        keys.append(issue)
            else:
                keys = issues

            data = createIssue(keys)
        time.sleep(5)

async def main(arg):
    blocking_task()