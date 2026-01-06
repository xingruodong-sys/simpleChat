"""
1. 开发comment中添加了日志说明，这种判断填日志说明那个时间点的component跟AI分的component是否一致，一致的话，则认为AI分对了
2. bug状态变更成reject、resovle，close，integration其中一种，变成integration的bug看下component跟AI分的一不一样，一样则认为分对了，其他状态的都认为分对了
"""

from src.utils.coreData import get_core_data_for_bert_correct, save_core_data_main, get_core_data_main, CoreDataMain
from routers.webhooks import getComponentReal
from src.helper import JiraSy
from src.db.database import DatabaseManager
from src.helper.Redis import *
from datetime import datetime
from src.task.team import team
import json
import csv
import os
import time
from src.task.effective_ip import llm_is_an

jira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
url = f"postgresql://postgres:neuadminpostgreroot@10.10.89.223:15432/naispilot"

def first_member_analyze_ex(db):
    datas = get_core_data_for_bert_correct(db)
    if not datas:
        return None
    daily_correct = 0
    daily_error = 0
    for data in datas:
        if not data.bert_component:
            continue
        value = jira.getIssueHistory(data.id)
        if not value:
            continue
        comments = value.get('comments')
        if not comments:
            continue
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
        is_finalized = False
        component = ""
        analyze_component = ""

        if an_start != 0:
            is_finalized = True
            component = team.get(author)
            analyze_component = component
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
            dictObj = {
                "id": data.id,
                "bert component": data.bert_component,
                "analyze component": analyze_component,
                "correct": bert_correct,
                "manually analyze": True
            }
            redis.hset("bert_correct_table", data.id, json.dumps(dictObj))
        else:
            changes = value.get('changes')
            if not changes:
                continue
            current_components = value.get('current_components')
            if not current_components:
                continue
            component = current_components[0]
            analyze_component = component
            found_final_status = False
            for change in changes:
                author = change.get('author')
                field = change.get('field')
                if field == 'status':
                    status = change.get('to_value')
                    if status in ['Rejected', 'Resolved', 'Closed', 'Integration', 'Verification']:
                        found_final_status = True
                        if component != getComponentReal(data.bert_component) and component not in ['', 'PM', 'UI Design', 'UE Design'] and 'CL' not in component and 'FO' not in component and 'OC' not in component:
                            bert_correct = False
                            break
            if found_final_status:
                is_finalized = True
                dictObj = {
                    "id": data.id,
                    "bert component": data.bert_component,
                    "analyze component": analyze_component,
                    "correct": bert_correct,
                    "manually analyze": False
                }
                redis.hset("bert_correct_table", data.id, json.dumps(dictObj))

        if is_finalized:
            if bert_correct:
                daily_correct += 1
                data.bert_correct = 2
            else:
                daily_error += 1
                data.bert_correct = 1
            save_core_data_main(data.id, CoreDataMain.model_validate(data), db)
            ts = int(time.time())
            redis.rpush(f"daily_bert_rate:{ts}", data.id)

    ts = time.time()
    daily_total = daily_correct + daily_error
    daily_rate = daily_correct / daily_total if daily_total > 0 else 0

    history_key = "BERT_CORRECT_STATS_HISTORY"
    history = redis.lrange(history_key, -1, -1)
    last_cum_correct = 0
    last_cum_error = 0
    if history:
        try:
            last_stat = json.loads(history[0])
            last_cum_correct = last_stat.get('cumulative_correct', 0)
            last_cum_error = last_stat.get('cumulative_error', 0)
        except:
            pass
    
    cum_correct = last_cum_correct + daily_correct
    cum_error = last_cum_error + daily_error
    cum_total = cum_correct + cum_error
    cum_rate = cum_correct / cum_total if cum_total > 0 else 0
    
    stat_obj = {
        "timestamp": ts,
        "daily_correct": daily_correct,
        "daily_error": daily_error,
        "daily_rate": daily_rate,
        "cumulative_correct": cum_correct,
        "cumulative_error": cum_error,
        "cumulative_rate": cum_rate
    }
    redis.rpush(history_key, json.dumps(stat_obj))

    return None

def given_comment_3valid():
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
                    if component in ['HMI', 'BL_MapViewer', 'BL_Guidance', 'BL_RouteCalculation', 'BL_DBU', 'BL_DI_POI_SDS', 'BL_Activation', 'BL_System', 'BL_Positioning', 'BL_TI']:
                    # if component in ['BL_Activation']:
                        break
            if component not in ['HMI', 'BL_MapViewer', 'BL_Guidance', 'BL_RouteCalculation', 'BL_DBU', 'BL_DI_POI_SDS', 'BL_Activation', 'BL_System', 'BL_Positioning', 'BL_TI']:
            # if component not in ['BL_Activation']:
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
            if comment_count > 2:
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
    given_comment_3valid()