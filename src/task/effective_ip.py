

# 统计过往数据中DBU，堆栈，激活三个模块Bug:
# 1. 从票创建到第一次有效解析的时长（需要给出时间差）
# 2. 计算AI介入后，从Bug创建到AI给出第一个comment的时长（需要给出时间差）
# 3. 现在AI介入后，AI登录comment后的下面一个该组组员登录的有效解析comment的时间对比bug登录时间的时间差，如果下一个登录有效解析comment的人不是这组的组员，那么以AI登录comment时间为准，计算解析时间差


from src.utils.coreData import get_active_core_data, get_all_core_data
from src.helper import JiraSy

jira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
def get_time_difference_from_ticket_to_first_parse():
    datas = get_all_core_data()
    if not datas:
        return None
    for data in datas:
        if data.bertComponent in ["DBU", "System", "Activation"]:
            jira.getIssueContent(data.id)
            return comment.created_at - data.created_at
    return None

def get_time_difference_from_ticket_to_ai_comment(issue_key):
    data = get_all_core_data(issue_key)
    if not data:
        return None
    
    for comment in data.comments:
        if comment.is_ai_comment:
            return comment.created_at - data.created_at
    return None

