from src.helper.Redis import *
from src.helper import Log, JiraSy
import pandas as pd
import json
import re


"""
帮我在./src/task/getSpecimen.py中添加一个方法,将/home/damon/Downloads/AI划分模块样本数据_HMI_20260107新追加.csv 文档中的Ticket ID列的所有项,添加到Redis的一个list中
"""


def add_ticket_ids_to_redis(csv_path='/home/damon/Downloads/2222.csv'):
    try:
        df = pd.read_csv(csv_path)
        if 'Ticket ID' not in df.columns:
            Log.logger.error("Column 'Ticket ID' not found in the CSV file.")
            return
        ticket_ids = df['Ticket ID'].dropna().tolist()  # Drop NaN values
        for tid in ticket_ids:
            redis.lpush('TICKET_IDS_LIST', str(tid))  # Add to the left of the list
        Log.logger.info(f"Added {len(ticket_ids)} ticket IDs to Redis list 'TICKET_IDS_LIST'.")
    except Exception as e:
        Log.logger.error(f"Error adding ticket IDs to Redis: {str(e)}")


def getTheFirstComponent(comments, current_component):
    centerMember = [
        'meng-xin',
        'liu.minghui',
        'li.b_li',
        'wang-yanqi',
    ]
    searchMember = [
        'zhangl-zhang',
        'guan-shh',
        'sunxj',
        'mefl',
        'lv.xing',
    ]
    settingMember = [
        'zhao.shj',
        'mgao',
        'wangmengchen',
        'liu-jh',
        'jiang.yc',
    ]
    guidanceMember = [
        'qubing',
        'jin.wch',
        'xingyu.wang',
        'fengyanjun',
        'wang.shulei',
    ]
    routeMember = [
        'zhao.di',
        'zhongjianfeng',
        'bao.zhh',
        'dong.jingyi',
    ]

    componentList = {
        'search':searchMember,
        'center':centerMember,
        'setting':settingMember,
        'guidance':guidanceMember,
        'route':routeMember,
    }
    for comment in comments:
        name = comment[0]
        body = comment[1]
        all_members = routeMember + guidanceMember + settingMember + searchMember + centerMember
        if name in all_members:
            for comp in componentList.keys():
                if name in componentList[comp]:
                    component = comp
                    return component, name
    return "Other", "Unknown"

def HMI_resource():
    componentDict = {
        'center':'HMI_center_table',
        'search':'HMI_search_table',
        'setting':'HMI_setting_table',
        'guidance':'HMI_guidance_table',
        'route':'HMI_route_table',
    }

    try:
        dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
        tickets = redis.lrange('TICKET_IDS_LIST', 0, -1)
        for i in tickets:
            if not i.startswith("NMASDK-"):
                issue_key = "NMASDK-" + str(i)
            else:
                issue_key = str(i)
            history = dejira.getIssueHistory(issue_key)
            if not history:
                continue
            type = history.get('issuetype')
            if type is None:
                continue
            if type.name != "Product bug":
                continue
            comments = history.get('comments')
            if not comments:
                continue
            current_components = history.get('current_components')
            if not current_components:
                continue

            current_components = current_components[0]
            component, user = getTheFirstComponent(comments, current_components)
            print(component, user, issue_key)
            dictObj = {
                COMMITMODULE: current_components,
                REALMODULE: component,
                SUMMARY: history['summary'],
                USER: user,
            }
            
            if component in componentDict.keys():
                redis.hset(componentDict[component], issue_key, json.dumps(dictObj))
            else:
                redis.hset('HMI_other_table', issue_key, json.dumps(dictObj))

    except Exception as e:
        print(f"Error: {e}")

def change_name_to_team():
    # 获取 name 到 team 的映射
    name_to_team = {}
    team_person_email_list = redis.lrange('TEAM_PERSON_EMAIL_LIST', 0, -1)
    print(f"Loaded {len(team_person_email_list)} entries from TEAM_PERSON_EMAIL_LIST")
    for entry in team_person_email_list:
        parts = entry.decode('utf-8').split(',') if isinstance(entry, bytes) else entry.split(',')
        if len(parts) >= 4:
            team = parts[0]
            name = parts[3]
            name_to_team[name] = team
            print(f"Mapped {name} -> {team}")
    print(f"name_to_team: {name_to_team}")

    items = [
        "NMASDK-70295",
        "NMASDK-73101",
        "NMASDK-82491",
        "NMASDK-109241",
        "NMASDK-107695",
        "NMASDK-104180",
        "NMASDK-104005",
        "NMASDK-99064",
        "NMASDK-98230",
        "NMASDK-97358",
        "NMASDK-96976",
        "NMASDK-96916",
        "NMASDK-96261",
        "NMASDK-92850",
        "NMASDK-90222",
        "NMASDK-89908",
        "NMASDK-89540",
        "NMASDK-89031",
        "NMASDK-88893",
        "NMASDK-87971",
    ]
    dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
    for item in items:
        issue_key = item
        history = dejira.getIssueHistory(item)
        if not history:
            continue
        type = history.get('issuetype')
        if type is None:
            continue
        if type.name != "Product bug":
            continue
        comments = history.get('comments')
        if not comments:
            continue
        
        dictObjList = []
        for comment in comments:
            name = comment[0]
            body = comment[1]
            an_start = comment[2] if len(comment) > 2 else 0
            author = name
            comm = body
            # 替换 [~name] 为对应的 team
            def replace_func(match):
                mentioned_name = match.group(1)
                print(f"Found mention: [~{mentioned_name}] in comment by {author}")
                if mentioned_name in name_to_team:
                    replacement = name_to_team[mentioned_name]
                    print(f"Replacing [~{mentioned_name}] with {replacement}")
                    return replacement
                else:
                    print(f"No mapping found for {mentioned_name}, keeping original")
                    return match.group(0)  # 如果找不到，保持原样
            original_comm = comm
            comm = re.sub(r'\[~([\w.-]+)\]', replace_func, comm)
            if comm != original_comm:
                print(f"Comment changed: {original_comm} -> {comm}")
            dictObj = {
                'Time': an_start,
                'Author': author,
                'team': 'todo',
                'comment': comm
            }
            dictObjList.append(dictObj)
        
        jstr = json.dumps(dictObjList, ensure_ascii=False, indent=2)
        component = history.get('current_components')[0] if history.get('current_components') else 'Unknown'
        row = {
            "TicketID": issue_key,
            "component": component,
            "Summary": history['summary'],
            "Comments": jstr
        }
        redis.hset('CHANGE_NAME_TO_TEAM_TABLE', issue_key, json.dumps(row, ensure_ascii=False))

"""
在./src/task/getSpecimen.py中添加一个方法,将/home/damon/Downloads/333.csv 文档中的 "二级团队"，"人员"，"Email"列的所有项,添加到Redis的一个list中
"""
def add_team_person_email_to_redis(csv_path='/home/damon/Downloads/333.csv'):
    try:
        df = pd.read_csv(csv_path)
        required_columns = ['二级团队', '人员', 'Email']
        for col in required_columns:
            if col not in df.columns:
                Log.logger.error(f"Column '{col}' not found in the CSV file.")
                return
        for index, row in df.iterrows():
            team = str(row['二级团队']).strip()
            person = str(row['人员']).strip()
            email = str(row['Email']).strip()
            name = email.split('@')[0]
            entry = f"{team},{person},{email},{name}"
            redis.lpush('TEAM_PERSON_EMAIL_LIST', entry)  # Add to the left of the list
        Log.logger.info(f"Added {len(df)} entries to Redis list 'TEAM_PERSON_EMAIL_LIST'.")
    except Exception as e:
        Log.logger.error(f"Error adding team, person, email to Redis: {str(e)}")
