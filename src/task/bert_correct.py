"""
1. 开发comment中添加了日志说明，这种判断填日志说明那个时间点的component跟AI分的component是否一致，一致的话，则认为AI分对了
2. bug状态变更成reject、resovle，close，integration其中一种，变成integration的bug看下component跟AI分的一不一样，一样则认为分对了，其他状态的都认为分对了
"""

from src.utils.coreData import get_core_data_for_bert_correct, save_core_data_main, get_core_data_main, CoreDataMain, get_core_data_berted
from routers.webhooks import getComponentReal
from src.helper import JiraSy
from src.db.database import DatabaseManager
from src.helper.Redis import *
from src.db import models
from datetime import datetime, timedelta
from src.task.team import team
import json
import csv
import os
import time
from collections import defaultdict
from src.task.effective_ip import llm_is_an

jira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
url = f"postgresql://postgres:neuadminpostgreroot@10.10.89.223:15432/naispilot"

BERT_CORRECT_TABLE = "bert_correct_table"
BERT_CORRECT_WEEKLY_STATS = "BERT_CORRECT_WEEKLY_STATS"

def parse_jira_timestamp(time_str):
    """
    Parses Jira timestamp string to float timestamp.
    Supported formats:
    - 2024-01-01T12:00:00.000+0800
    - 2024-01-01T12:00:00.000+08:00
    """
    if not time_str:
        return 0
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f", 
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.timestamp()
        except ValueError:
            continue
    
    return 0

def check_component_correct(bert_component, analyze_component):
    bert_correct = True
    if "HMI" in analyze_component:
        if bert_component == "HMI":
            bert_correct = True
        else:
            bert_correct = False
    elif "Map" in analyze_component:
        if bert_component == "MapViewer" or bert_component == "DBU" or bert_component == "TI" or bert_component == "Positioning":
            bert_correct = True
        else:
            bert_correct = False
    elif "Route" in analyze_component:
        if bert_component == "Guidance" or bert_component == "Route Calculation":
            bert_correct = True
        else:
            bert_correct = False
    elif "Search" in analyze_component:
        if bert_component == "DI_POS_SDS":
            bert_correct = True
        else:
            bert_correct = False
    elif "System" in analyze_component:
        if bert_component == "System" or bert_component == "Activation":
            bert_correct = True
        else:
            bert_correct = False
    else:
        bert_correct = True
    return bert_correct

def analyze_ticket(data, db):
    """
    Analyzes a single ticket to determine if it's finalized, its correctness, and finalization time.
    Uses Redis cache to avoid repeated Jira calls.
    Returns: (finalized_at_ts, is_correct) or None if not finalized.
    """
    # Check Redis cache first
    cached_data_str = redis.hget(BERT_CORRECT_TABLE, data.id)
    cached_data = {}
    if cached_data_str:
        try:
            cached_data = json.loads(cached_data_str)
            if "finalized_at" in cached_data:
                # Cache hit with timestamp
                return cached_data.get("finalized_at"), cached_data.get("correct")
        except json.JSONDecodeError:
            pass

    # Not cached or missing timestamp, fetch from Jira
    value = jira.getIssueHistory(data.id)
    if not value:
        return None

    comments = value.get('comments')
    if not comments:
        comments = [] # Handle empty comments safely
    
    comments.sort(key=lambda x:x[2])
    
    an_start = ""
    author = ""
    # Check for manual analysis comment
    for comment in comments:
        if 'Naiser-T3000' != comment[0]:
            if '日志说明' in comment[1]:
                an_start = comment[2] # String timestamp
                author = comment[0]
                break
    
    bert_correct = True
    is_finalized = False
    analyze_component = ""
    finalized_at = 0

    if an_start:
        is_finalized = True
        finalized_at = parse_jira_timestamp(an_start)
        component = team.get(author)
        analyze_component = component
        bert_correct = check_component_correct(data.bert_component, analyze_component)
        
        dictObj = {
            "id": data.id,
            "bert component": data.bert_component,
            "analyze component": analyze_component,
            "correct": bert_correct,
            "manually analyze": True,
            "finalized_at": finalized_at
        }
        redis.hset(BERT_CORRECT_TABLE, data.id, json.dumps(dictObj))
    
    else:
        # Check for status changes
        changes = value.get('changes')
        if not changes:
            return None
        current_components = value.get('current_components')
        if not current_components:
            return None
        
        component = current_components[0]
        analyze_component = component
        found_final_status = False
        
        # Iterate changes to find when it entered the target state
        status_change_time = 0
        
        for change in changes:
            field = change.get('field')
            if field == 'status':
                status = change.get('to_value')
                # JiraSy returns 'date' for change timestamp
                change_time_str = change.get('date') 
                
                if status in ['Rejected', 'Resolved', 'Closed', 'Integration', 'Verification']:
                    found_final_status = True
                    # Parse timestamp
                    ts = parse_jira_timestamp(change_time_str)
                    if ts > 0:
                        status_change_time = ts
                    
                    if component != getComponentReal(data.bert_component) and component not in ['', 'PM', 'UI Design', 'UE Design'] and 'CL' not in component and 'FO' not in component and 'OC' not in component:
                        bert_correct = False
                        break
        
        if found_final_status:
            is_finalized = True
            if status_change_time == 0:
                 # Fallback if time not found
                 status_change_time = time.time()
            
            finalized_at = status_change_time
            
            dictObj = {
                "id": data.id,
                "bert component": data.bert_component,
                "analyze component": analyze_component,
                "correct": bert_correct,
                "manually analyze": False,
                "finalized_at": finalized_at
            }
            redis.hset(BERT_CORRECT_TABLE, data.id, json.dumps(dictObj))

    if is_finalized:
        # Update DB if needed
        # We only update if status changed in DB
        if data.bert_correct == 0:
             if bert_correct:
                 data.bert_correct = 2
             else:
                 data.bert_correct = 1
             save_core_data_main(data.id, CoreDataMain.model_validate(data), db)
             
        return finalized_at, bert_correct

    return None

def get_week_start(ts):
    """Returns the timestamp of the Monday 00:00:00 of the week containing ts."""
    dt = datetime.fromtimestamp(ts)
    # weekday: Mon=0, Sun=6
    start = dt - timedelta(days=dt.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp()

def collect_bert_stats(db, backfill=False):
    """
    Collects BERT accuracy stats grouped by week.
    If backfill=True, it re-evaluates all 'berted' tickets.
    """
    # Get all tickets that have been processed by BERT
    datas = get_core_data_berted(db)
    if not datas:
        return

    # Bucket: week_start_ts -> {'correct': 0, 'error': 0}
    weekly_buckets = defaultdict(lambda: {'correct': 0, 'error': 0})

    for data in datas:
        result = analyze_ticket(data, db)
        if result:
            ts, is_correct = result
            if ts > 0:
                week_start = get_week_start(ts)
                if is_correct:
                    weekly_buckets[week_start]['correct'] += 1
                else:
                    weekly_buckets[week_start]['error'] += 1

    # Convert buckets to sorted list of stats
    sorted_weeks = sorted(weekly_buckets.keys())
    
    stats_history = []
    cumulative_correct = 0
    cumulative_error = 0

    for week_start in sorted_weeks:
        week_stats = weekly_buckets[week_start]
        correct = week_stats['correct']
        error = week_stats['error']
        total = correct + error
        rate = correct / total if total > 0 else 0
        
        cumulative_correct += correct
        cumulative_error += error
        cum_total = cumulative_correct + cumulative_error
        cum_rate = cumulative_correct / cum_total if cum_total > 0 else 0
        
        # Calculate week end (Sunday 24:00 which is next Monday 00:00)
        week_end = week_start + 7 * 24 * 3600
        
        stat_obj = {
            "week_start": week_start,
            "week_end": week_end,
            "week_start_str": datetime.fromtimestamp(week_start).strftime("%Y-%m-%d"),
            "week_end_str": datetime.fromtimestamp(week_end).strftime("%Y-%m-%d"),
            "weekly_correct": correct,
            "weekly_error": error,
            "weekly_rate": rate,
            "cumulative_correct": cumulative_correct,
            "cumulative_error": cumulative_error,
            "cumulative_rate": cum_rate
        }
        stats_history.append(stat_obj)

    # Save to Redis
    # We overwrite the list to ensure consistency and order
    redis.delete(BERT_CORRECT_WEEKLY_STATS)
    for stat in stats_history:
        redis.rpush(BERT_CORRECT_WEEKLY_STATS, json.dumps(stat))

    print(f"Collected stats for {len(stats_history)} weeks.")


# ==============================================================================
# IMPORT FUNCTION
# ==============================================================================

def import_bert_weekly_stats(db):
    try:
        data = redis.lrange(BERT_CORRECT_WEEKLY_STATS, 0, -1)
        
        if not data:
            print("No data found in Redis for weekly stats.")
            return
        db.query(models.StatisticsBertWeeklyHistory).delete()
        count = 0
        for item_json in data:
            try:
                obj = json.loads(item_json)
                
                db_obj = models.StatisticsBertWeeklyHistory(
                    week_start=float(obj.get("week_start", 0)),
                    week_end=float(obj.get("week_end", 0)),
                    week_start_str=str(obj.get("week_start_str", "")),
                    week_end_str=str(obj.get("week_end_str", "")),
                    weekly_correct=int(obj.get("weekly_correct", 0)),
                    weekly_error=int(obj.get("weekly_error", 0)),
                    weekly_rate=float(obj.get("weekly_rate", 0)),
                    cumulative_correct=int(obj.get("cumulative_correct", 0)),
                    cumulative_error=int(obj.get("cumulative_error", 0)),
                    cumulative_rate=float(obj.get("cumulative_rate", 0))
                )
                db.add(db_obj)
                count += 1
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON: {item_json}")
            except Exception as e:
                print(f"Error processing item: {e}")
        
        db.commit()
        print(f"Successfully imported {count} records to StatisticsBertWeeklyHistory.")
    except Exception as e:
        print(str(e))

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
                # 将结果存入 Redis
                redis.hset('BERT_COMMENTS_TABLE', issue_key, json.dumps(row, ensure_ascii=False))
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
    # Determine mode based on arg or default to weekly/backfill
    # If this is called from scheduled task, it might be no args or specific arg
    # For now, we just run the collection. 
    # Since the requirement says "one time task... then weekly", 
    # and the code handles both (by iterating all and updating Redis cache),
    # we can just call it.
    
    db_mgr = DatabaseManager(url)
    with db_mgr.standalone_session() as db:
        # collect_bert_stats(db)
        import_bert_weekly_stats(db)
    # given_comment_3valid()