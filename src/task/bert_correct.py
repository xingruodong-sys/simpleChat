"""
1. 开发comment中添加了日志说明，这种判断填日志说明那个时间点的component跟AI分的component是否一致，一致的话，则认为AI分对了
2. bug状态变更成reject、resovle，close，integration其中一种，变成integration的bug看下component跟AI分的一不一样，一样则认为分对了，其他状态的都认为分对了
"""

from src.utils.coreData import get_core_data_for_bert_correct, save_core_data_main, get_core_data_main
from routers.webhooks import getComponentReal
from src.helper import JiraSy
from src.db.database import DatabaseManager
from src.helper import Redis
from datetime import datetime
from src.task.team import team
import json
import requests
import csv
import os
from src.task.effective_ip import llm_is_an

jira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
url = f"postgresql://postgres:neuadminpostgreroot@10.146.12.34:30432/naispilot"

def first_member_analyze():
    db_mgr = DatabaseManager(url)
    with db_mgr.standalone_session() as db:
        datas = get_core_data_for_bert_correct(db)
        if not datas:
            return None
        results = []
        filename = "output.csv"
        file_exists = os.path.isfile(filename)
        with open(filename, mode='a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "bert component", "analyze component", "correct"])
            
            if not file_exists:
                writer.writeheader()  # 只在首次写入时加表头

            filename2 = "output2.csv"
            file_exists2 = os.path.isfile(filename2)
            with open(filename2, mode='a', encoding='utf-8', newline='') as f:
                writer2 = csv.DictWriter(f, fieldnames=["id", "bert component", "current component", "correct"])
                
                if not file_exists2:
                    writer2.writeheader()  # 只在首次写入时加表头
                for data in datas:
                    if not data.bert_component:
                        continue
                    value = jira.getIssueHistory(data.id)
                    if not value:
                        continue
                    comments = value.get('comments')
                    comments.sort(key=lambda x:x[2])
                    an_start = 0
                    for comment in comments:
                        if 'Naiser-T3000' != comment[0]:
                            if '日志说明' in comment[1]:
                                an_start = comment[2]
                                break
                    bert_correct = True
                    if an_start != 0:
                        component = "NO CHANGE"
                        changes = value.get('changes')
                        for change in changes:
                            author = change.get('author')
                            field = change.get('field')
                            if author != 'Naiser-T3000' and field == 'Component':
                                date =change.get('date')
                                if time_cmp(an_start, date):
                                    component = change.get('to_value')
                                    bert_correct = False
                                    break
                        results.append({
                            "id": data.id,
                            "bert component": data.bert_component,
                            "analyze component": component,
                            "correct": bert_correct
                        })
                        row = {
                            "id": data.id,
                            "bert component": data.bert_component,
                            "analyze component": component,
                            "correct": bert_correct
                        }
                        writer.writerow(row)

                    else:
                        changes = value.get('changes')
                        component = ""
                        for change in changes:
                            author = change.get('author')
                            field = change.get('field')
                            if field == 'status':
                                status = change.get('to_value')
                                if status in ['Rejected', 'Resolved', 'Closed', 'Integration']:
                                    if component != getComponentReal(data.bert_component) and component != '':
                                        bert_correct = False
                                        break
                            
                            if field == 'Component':
                                if change.get('to_value') != 'None':
                                    component = change.get('to_value')
                        
                                # data.bert_correct = 1
                                # save_core_data_main(data.id, data)
                        results.append({
                            "id": data.id,
                            "bert component": data.bert_component,
                            "current component": component,
                            "correct": bert_correct
                        })
                        row2 = {
                            "id": data.id,
                            "bert component": data.bert_component,
                            "current component": component,
                            "correct": bert_correct
                        }
                        writer2.writerow(row2)
        # print(results)
    return None

def first_member_analyze_ex():
    db_mgr = DatabaseManager(url)
    with db_mgr.standalone_session() as db:
        datas = get_core_data_for_bert_correct(db)
        if not datas:
            return None
        results = []
        filename = "output.csv"
        file_exists = os.path.isfile(filename)
        with open(filename, mode='a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "bert component", "analyze component", "correct"])
            
            if not file_exists:
                writer.writeheader()  # 只在首次写入时加表头

            filename2 = "output2.csv"
            file_exists2 = os.path.isfile(filename2)
            with open(filename2, mode='a', encoding='utf-8', newline='') as f:
                writer2 = csv.DictWriter(f, fieldnames=["id", "bert component", "current component", "correct"])
                
                if not file_exists2:
                    writer2.writeheader()  # 只在首次写入时加表头
                for data in datas:
                    if not data.bert_component:
                        continue
                    value = jira.getIssueHistory(data.id)
                    if not value:
                        continue
                    comments = value.get('comments')
                    comments.sort(key=lambda x:x[2])
                    an_start = 0
                    author = ""
                    for comment in comments:
                        if 'Naiser-T3000' != comment[0]:
                            if '日志说明' in comment[1]:
                                an_start = comment[2]
                                author = comment[0]
                                break
                    bert_correct = True
                    if an_start != 0:
                        continue
                        component = team.get(author)
                        if "HMI" in component:
                            if data.bert_component == "HMI":
                                bert_correct = True
                            else:
                                bert_correct = False
                        elif "Map" in component:
                            if data.bert_component == "MapViewer" or data.bert_component == "DBU" or data.bert_component == "TI" or data.bert_component == "Positioning":
                                bert_correct = True
                            else:
                                bert_correct = False
                        elif "Route" in component:
                            if data.bert_component == "Guidance" or data.bert_component == "Route Calculation":
                                bert_correct = True
                            else:
                                bert_correct = False
                        elif "Search" in component:
                            if data.bert_component == "DI_POS_SDS":
                                bert_correct = True
                            else:
                                bert_correct = False
                        elif "System" in component:
                            if data.bert_component == "System" or data.bert_component == "Activation":
                                bert_correct = True
                            else:
                                bert_correct = False
                        else:
                            bert_correct = True
                        results.append({
                            "id": data.id,
                            "bert component": data.bert_component,
                            "analyze component": component,
                            "correct": bert_correct
                        })
                        row = {
                            "id": data.id,
                            "bert component": data.bert_component,
                            "analyze component": component,
                            "correct": bert_correct
                        }
                        writer.writerow(row)

                    else:
                        changes = value.get('changes')
                        component = ""
                        for change in changes:
                            author = change.get('author')
                            field = change.get('field')
                            if field == 'status':
                                status = change.get('to_value')
                                if status in ['Rejected', 'Resolved', 'Closed', 'Integration']:
                                    if component != getComponentReal(data.bert_component) and component != '':
                                        bert_correct = False
                                        break
                            
                            if field == 'Component':
                                if change.get('to_value') != 'None':
                                    component = change.get('to_value')
                        
                                # data.bert_correct = 1
                                # save_core_data_main(data.id, data)
                        results.append({
                            "id": data.id,
                            "bert component": data.bert_component,
                            "current component": component,
                            "correct": bert_correct
                        })
                        row2 = {
                            "id": data.id,
                            "bert component": data.bert_component,
                            "current component": component,
                            "correct": bert_correct
                        }
                        writer2.writerow(row2)
        # print(results)
    return None

def first_give_comment():
    # db_mgr = DatabaseManager(url)
    # with db_mgr.standalone_session() as db:
    filename = "output.csv"
    file_exists = os.path.isfile(filename)
    Hmi = 0
    Map = 0
    Guidance = 0
    Route = 0
    Dbu = 0
    Search = 0
    Activation = 0
    System = 0
    Pos = 0
    Ti = 0
    ticket_close_count = 0
    with open(filename, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["TicketID", "component", "Summary", "Comments"])
        if not file_exists:
            writer.writeheader()

        for i in range(91446, 1, -1):
            if Hmi > 19 and Map > 19 and Guidance > 19 and Route > 19 and Dbu > 19 and Search > 19 and Activation > 9 and System > 9 and Pos > 9 and Ti > 4:
                break

            issue_key = "NMASDK-" + str(i)
            history = jira.getIssueHistory(issue_key)
            # try:
            #     core_data = get_core_data_main(issue_key, db)
            # except Exception as e:
            #     print(f'{issue_key} get core data failed')
            #     continue

            if history is None:
                continue
            if 'Product bug' != history['issuetype'].name:
                continue
            if 'subticket' in history['summary'].lower():
                continue        
            if 'clone' in history['summary'].lower():
                continue
            comments = history['comments']
            if comments is None:
                continue
            status = history['current_status']
            if status not in ['Rejected', 'Resolved', 'Closed'] and ticket_close_count < 100:
                ticket_close_count += 1
                continue

            # if core_data.bert_component:
            #     component = getComponentReal(core_data.bert_component)
            # else:
            component =  None
            changes = history['changes']
            for change in changes:
                field = change.get('field')                        
                if field == 'Component':
                    component = change.get('to_value')
                    # if component in ['HMI', 'BL_MapViewer', 'BL_Guidance', 'BL_RouteCalculation', 'BL_DBU', 'BL_DI_POI_SDS', 'BL_Activation', 'BL_System', 'BL_Positioning', 'BL_TI']:
                    if component in ['BL_Activation']:
                        break
            # if component not in ['HMI', 'BL_MapViewer', 'BL_Guidance', 'BL_RouteCalculation', 'BL_DBU', 'BL_DI_POI_SDS', 'BL_Activation', 'BL_System', 'BL_Positioning', 'BL_TI']:
            if component not in ['BL_Activation']:
                continue

            if 'HMI' == component and Hmi > 19:
                continue
            if 'BL_MapViewer' == component and Map > 19:
                continue
            if 'BL_Guidance' == component and Guidance > 19:
                continue
            if 'BL_RouteCalculation' == component and Route > 19:
                continue
            if 'BL_DBU' == component and Dbu > 19:
                continue
            if 'BL_DI_POI_SDS' == component and Search > 19:
                continue
            if 'BL_Activation' == component and Activation > 9:
                continue
            if 'BL_System' == component and System > 9:
                continue
            if 'BL_Positioning' == component and Pos > 9:
                continue
            if 'BL_TI' == component and Ti > 4:
                continue

            comments.sort(key=lambda x:x[2])
            an_start = 0
            author = ""
            comment_count = 0
            dictObjList = []
            for comment in comments:
                an_start = comment[2]
                comm = comment[1]
                author = comment[0]
                if author == 'Naiser-T3000':
                    continue
                if 'code:java' in comm or '日志说明' in comm or len(comm) > 200:
                    comment_count += 1
                    dictObj = {
                            'Time': an_start,
                            'Author': author,
                            'team': 'todo',
                            'comment': comm
                        }
                    dictObjList.append(dictObj)
                else:
                    if llm_is_an(comm):
                        comment_count += 1
                        dictObj = {
                                'Time': an_start,
                                'Author': author,
                                'team': 'todo',
                                'comment': comm
                            }
                        dictObjList.append(dictObj)
                    # else:
                    #     print(f"{issue_key}:{author}:{an_start} llm not analyze {comm}")
            if comment_count > 1:
                jstr = json.dumps(dictObjList, ensure_ascii=False, indent=2)
                row = {
                    "TicketID": issue_key,
                    "component": component,
                    "Summary": history['summary'],
                    "Comments": jstr
                }
                writer.writerow(row)
                if 'HMI' == component:
                    Hmi += 1
                if 'BL_MapViewer'  == component:
                    Map += 1
                if 'BL_Guidance' == component:
                    Guidance += 1
                if 'BL_RouteCalculation' == component:
                    Route += 1
                if 'BL_DBU' == component:
                    Dbu += 1
                if 'BL_DI_POI_SDS' == component:
                    Search += 1
                if 'BL_Activation' == component:
                    Activation += 1
                if 'BL_System' == component:
                    System += 1
                if 'BL_Positioning' == component:
                    Pos += 1
                if 'BL_TI' == component:
                    Ti += 1

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

def time_cmp(start_time_str, change_time_str):
    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    start = datetime.strptime(start_time_str, fmt)
    change = datetime.strptime(change_time_str, fmt)
    # diff = True if change > start else False
    diff = False if change > start else True
    return diff

def to_hms(total_seconds):
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {'h':hours, 'm':minutes, 's':seconds}


def main(arg):
    # first_member_analyze_ex()
    first_give_comment()
