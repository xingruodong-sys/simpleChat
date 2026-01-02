from src.utils.coreData import get_all_core_data, get_core_data_sub, save_core_data_sub, get_core_data_berted, get_core_data_sub_by_main_id
from src.helper import JiraSy
from src.db.database import DatabaseManager
from src.db import models
from src.helper.Redis import *
import json
import requests
from datetime import datetime
import csv

jira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
url = f"postgresql://postgres:neuadminpostgreroot@10.10.89.223:15432/naispilot"

"""
统计过往数据中DBU，堆栈，激活三个模块Bug:
1. 从票创建到第一次有效解析的时长（需要给出时间差）
2. 计算AI介入后，从Bug创建到AI给出第一个comment的时长（需要给出时间差）
3. 现在AI介入后，AI登录comment后的下面一个该组组员登录的有效解析comment的时间对比bug登录时间的时间差，如果下一个登录有效解析comment的人不是这组的组员，那么以AI登录comment时间为准，计算解析时间差
"""

raw = redis.get("ANALYZE_COST_INFO")
if raw is None:
    # 初始化默认值
    dictitem = {
        'total_count': 0,
        'total_time': 0.0  # 或 int，取决于 time_diff 类型
    }
    redis.set("ANALYZE_COST_INFO", json.dumps(dictitem))

def first_member_analyze():
    db_mgr = DatabaseManager(url)
    with db_mgr.standalone_session() as db:
        datas = get_all_core_data(db)
        if not datas:
            return None
        results = []
        for data in datas:
            if data.bert_component in ["DBU", "System", "Activation"]:
                print(data.id)
                print(data.bert_component)
                value = jira.getIssueHistory(data.id)
                comments = value.get('comments')
                comments.sort(key=lambda x:x[2])
                an_start = 0
                for comment in comments:
                    if 'Naiser-T3000' == comment[0]:
                        if 'code:java' in comment or len(comment[1]) > 50:
                            an_start = comment[2]
                            break
                        else:
                            if llm_is_an(comment[1]):
                                an_start = comment[2]
                                break
                if an_start != 0:
                    results.append({
                            'id': data.id,
                            'created_at': value.get('created_at'),
                            'an_start': an_start
                        })
        print(results)
    return None

def hmi_tag_change():
    db_mgr = DatabaseManager(url)
    with db_mgr.standalone_session() as db:
        datas = db.query(models.CoreDataSub).filter((models.CoreDataSub.component_of_tool == 'HMI') & (models.CoreDataSub.tool_llm_tag == '')).filter(models.CoreDataSub.exception_string == '').all()
        if not datas:
            return None
        for data in datas:
            value = jira.getIssueHistory(data.main_id)
            comments = value.get('comments')
            if comments is None:
                continue
            comments.sort(key=lambda x:x[2])
            an_start = 0
            for comment in comments:
                if 'Naiser-T3000' == comment[0]:
                    if comment[1] == 'T3000已分配模块，请模块Lead处理' or 'BLUtilityController' in comment[1]:
                        continue
                    print(f'{data.main_id}:{comment[1]}')
                    sub = get_core_data_sub(db=db, key=data.id)
                    if comment[1] == 'Tag表中没有对应Tag,请HMI补充Tag表' or comment[1] == 'Tag表中没有对应Tag,不在解析范围':
                        sub.tool_llm_tag = 'no_tag'
                        save_core_data_sub(data=sub, db=db)
                    elif comment[1] == '时间格式错误' or comment[1] == '缺少操作时间':
                        sub.tool_llm_tag = 'no_time'
                        save_core_data_sub(data=sub, db=db)
                    elif comment[1] == '缺少android log' or '下载Android日志文件失败' in comment[1]:
                        sub.tool_llm_tag = 'no_android_log'
                        save_core_data_sub(data=sub, db=db)
                    elif 'Error executing tool analyze_hmi_log' in comment[1] or 'executing tool analyze_activation_log' in comment[1]:
                        sub.tool_llm_tag = 'exception'
                        save_core_data_sub(data=sub, db=db)
                    elif 'search' in comment[1] or 'NMACategoryController' in comment[1] or 'poiDetailSearch' in comment[1]:
                        sub.tool_llm_tag = 'Search'
                        save_core_data_sub(data=sub, db=db)
                    elif 'GUIDANCE_TURN_INFO_UPDATE' in comment[1] or 'GUIDANCE_DEST_INFO_UPDATE' in comment[1]:
                        sub.tool_llm_tag = 'Guidance'
                        save_core_data_sub(data=sub, db=db)
                    elif 'NeusoftTtsManager' in comment[1] or 'SystemAdapterNMA' in comment[1]:
                        sub.tool_llm_tag = 'System'
                        save_core_data_sub(data=sub, db=db)
                    elif 'AI解析: 未分析出有效结论，请HMI人工重新进行分析。' in comment[1] or 'UI' in comment[1]:
                        sub.tool_llm_tag = 'UI'
                        save_core_data_sub(data=sub, db=db)
                    # else:
                    #     sub.tool_llm_tag = 'error'
                    #     save_core_data_sub(data=sub, db=db)
                        
    return None

def from_create_to_first_analyze(start, end):
    for i in range(start, end):
        issue = "NMASDK-" + str(i)
        
        data = jira.getIssueHistory(issue)
        type = data.get('issuetype')
        if type is None:
            continue
        if type.name != "Product bug":
            continue
        comments = data.get('comments')
        if comments is None:
            continue
        comments.sort(key=lambda x:x[2])
        an_start = 0
        author = ""
        for comment in comments:
            if 'code:java' in comment or len(comment[1]) > 200:
                an_start = comment[2]
                break
            else:
                if llm_is_an(comment[1]):
                    an_start = comment[2]
                    author = comment[0]
                    if time_diff(data.get('create_at'), an_start) < 180: # tester add analyze comment
                        continue
                    break
        if an_start != 0:
            dictObj = {
                'id': issue,
                'created_at': data.get('created_at'),
                'an_start': an_start,
                'author': author,
                'time_diff': time_diff(data.get('created_at'), an_start),
            }
            redis.hset("FIRST_ANALYZE_HASH", issue, json.dumps(dictObj))
            dictitem = json.loads(redis.get("ANALYZE_COST_INFO"))
            dictitem['total_count'] += 1
            dictitem['total_time'] += dictObj['time_diff']
            redis.set("ANALYZE_COST_INFO", json.dumps(dictitem))
    return None

def llm_is_an(comment, model='qwen3:30b-a3b'):
    res = {}
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"""** 角色与任务：**
            你的核心任务是判断用户输入的文本是否为对一个问题的分析
            ** 注意 **
            - 请只给出判断True or False，不要有多余的输出。
            ** 用户输入如下： **
            用户输入：{comment}
            /no_think"""
            },
        ]
        url = "http://10.146.37.2:11434/api/chat"
        proxies = {
            "http": None,
            "https": None,
        }
        form_data = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": 0,
            "top_p": 1,
            "top_k": 0,
        }
        res = requests.post(url=url, proxies=proxies, data=json.dumps(form_data), stream=True)
        res = res.json()
        res = res["message"]["content"].split("</think>")[-1].strip()
        res = True if res == 'True' else False
        return 
    except Exception as e:
        print(e)
        return None

def time_diff(start_time_str, end_time_str):
    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    start = datetime.strptime(start_time_str, fmt)
    end = datetime.strptime(end_time_str, fmt)
    diff = end - start
    total_seconds = int(diff.total_seconds())
    total_seconds = abs(total_seconds)
    return total_seconds

def to_hms(total_seconds):
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {'h':hours, 'm':minutes, 's':seconds}

def to_fmt(ts):
    from datetime import datetime, timezone
    dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
    formatted = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    return formatted

"""
所有Bert过的Bug，AI第一次解析的时间
所有Bert过的Bug，人第一次解析的时间
所有AI选过有效tool的Bug，AI第一次解析的时间，
所有AI选过有效tool的Bug，人第一次解析的时间，
"""

def ai_first_analyze():
    filename = "output.csv"
    file_exists = os.path.isfile(filename)
    db_mgr = DatabaseManager(url)
    with db_mgr.standalone_session() as db:
        datas = get_core_data_berted(db)
        if not datas:
            return None
        # with open(filename, mode='a', encoding='utf-8', newline='') as f:
        #     writer = csv.DictWriter(f, fieldnames=["TicketID", 
        #                                            "created_at", 
        #                                            "bert_component", 
        #                                            "ai_first_ana_start", 
        #                                            "create_at_to_ai_ana", 
        #                                            "manually_first_ana_start", 
        #                                            "create_at_to_manually_ana", 
        #                                            "integration", 
        #                                            "create_at_to_integration", 
        #                                            "reject", 
        #                                            "create_at_to_reject", 
        #                                            "resovled", 
        #                                            "resovled_at_to_reject", 
        #                                            "tool_name", 
        #                                            "hmi_tag"])
        #     if not file_exists:
        #         writer.writeheader()
        for data in datas:
            value = jira.getIssueHistory(data.id)
            if not value:
                continue
            comments = value.get('comments')
            if comments is None:
                continue
            comments.sort(key=lambda x:x[2])
            manually_an_start = 0
            ai_an_start = 0
            for comment in comments:
                author = comment[0]
                an_start = comment[2]
                comment = comment[1]
                if 'Naiser-T3000' == author:
                    if ai_an_start == 0:
                        if 'code:java' in comment or '日志说明' in comment or len(comment) > 100:
                            ai_an_start = an_start
                        else:
                            if 'AI模型归类为非工具类问题' in comment:
                                continue
                            if llm_is_an(comment):
                                ai_an_start = an_start
                else:
                    if manually_an_start == 0:
                        if 'code:java' in comment or len(comment) > 100:
                            manually_an_start = an_start
                        else:
                            if llm_is_an(comment):
                                manually_an_start = an_start
            tool_anas = get_core_data_sub_by_main_id(db=db, main_id=data.id)
            tool_name = ""
            hmi_tag = ''
            for tool in tool_anas:
                if tool.tool_name not in ['analyze_Other', 'analyze_searchOther', 'getSystemOtherInfo']:
                    tool_name = tool.tool_name
                    hmi_tag = tool.tool_llm_tag
                if tool_name:
                    break

            changes = value.get('changes')
            to_rejected_date = ''
            to_resolved_date = ''
            to_integration_date = ''
            for change in changes:
                field = change.get('field')
                if field == 'status':
                    status = change.get('to_value')
                    if status == 'Rejected':
                        to_rejected_date = change.get('date')
                    if status == 'Resolved':
                        to_resolved_date = change.get('date')
                    if status == 'Integration':
                        to_integration_date = change.get('date')
                        break

            created_at = to_fmt(data.created_at)
            row = {
                "TicketID": data.id,
                "created_at": to_fmt(data.created_at),
                "bert_component": data.bert_component,
                "ai_first_ana_start": ai_an_start,
                "create_at_to_ai_ana": time_diff(created_at, ai_an_start) if ai_an_start else 0,
                "manually_first_ana_start": manually_an_start,
                "create_at_to_manually_ana": time_diff(created_at, manually_an_start) if manually_an_start else 0,
                "integration": to_integration_date,
                "create_at_to_integration": time_diff(created_at, to_integration_date) if to_integration_date else 0,
                "reject": to_rejected_date,
                "create_at_to_reject": time_diff(created_at, to_rejected_date) if to_rejected_date else 0,
                "resovled": to_resolved_date, 
                "create_at_to_resovled": time_diff(created_at, to_resolved_date) if to_resolved_date else 0,
                "tool_name": tool_name,
                "hmi_tag": hmi_tag
            }
            redis.hset("analyze_effective_table", data.id, json.dumps(row))
            # writer.writerow(row)
            # print(row)
    return None

"""
你是软件架构师，在维护一个项目。
项目是一个前端采用streamlit，后端使用fastapi前后端分离项目。页面代码在/pages路径下。

你的任务：
项目需要展示目前运行的一些数据，在src/task/effective_ip的ai_first_analyze函数中，进行了统计。
添加一个页面，用于展示这些数据，页面风格与其他保持一致。

"""