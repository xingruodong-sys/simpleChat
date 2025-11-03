import redis as r  # 导入redis 模块
import os

host = os.getenv('REDIS_HOST', 'redis')
port = os.getenv('REDIS_PORT_NAISPILOT', 6379)
password = os.getenv('REDIS_PASSWD', '')

pool = r.ConnectionPool(host=host, port=port, decode_responses=True)
redis = r.Redis(host=host, port=port, decode_responses=True, password=password)

#数据库表
SETTING_ACTIVE_FO_HASH = 'SETTING_ACTIVE_FO_HASH'
SETTING_LLM_MODEL = 'SETTING_LLM_MODEL'
FO_PROJECT_LIST = 'FO_PROJECT_LIST'
PROJECT_ISSUE_ANALYZED = 'PROJECT_ISSUE_ANALYZED'
PROMPT_HASH = 'PROMPT_HASH'
COMPONENTS_CHANGE_BY_FO_SET = 'COMPONENTS_CHANGE_BY_FO_SET'
COMPONENTS_CHANGE_BY_DEV_SET = 'COMPONENTS_CHANGE_BY_DEV_SET'
USER_GIVEN_ISSUE_ANALYZED = 'USER_GIVEN_ISSUE_ANALYZED'
SPECIMEN_STANDARD_HASH = 'SPECIMEN_STANDARD_HASH'
SPECIMEN_COMMON_STANDARD_HASH = 'SPECIMEN_COMMON_STANDARD_HASH'
SETTING_LLM_MODEL_FOR_SUMMARY = 'SETTING_LLM_MODEL_FOR_SUMMARY'
COMPONENTS_CHANGE_BY_FO_SET_IN_GIVEN_ISSUE = 'COMPONENTS_CHANGE_BY_FO_SET_IN_GIVEN_ISSUE'
COMPONENTS_CHANGE_BY_DEV_SET_IN_GIVEN_ISSUE = 'COMPONENTS_CHANGE_BY_DEV_SET_IN_GIVEN_ISSUE'

COMPONENTS_MAP_HASH = 'COMPONENTS_MAP_HASH'
COMPONENTS_HMI_HASH = 'COMPONENTS_HMI_HASH'
COMPONENTS_SEARCH_HASH = 'COMPONENTS_SEARCH_HASH'
COMPONENTS_GUIDANCE_HASH = 'COMPONENTS_GUIDANCE_HASH'
COMPONENTS_DBU_POS_HASH = 'COMPONENTS_DBU_POS_HASH'
COMPONENTS_ACTIVITION_HASH = 'COMPONENTS_ACTIVITION_HASH'
COMPONENTS_ACTIVITION_DBU_HASH = 'COMPONENTS_ACTIVITION_DBU_HASH'
COMPONENTS_SYSTEM_HASH = 'COMPONENTS_SYSTEM_HASH'
COMPONENTS_ROUTE_HASH = 'COMPONENTS_ROUTE_HASH'
COMPONENTS_TI_HASH = 'COMPONENTS_TI_HASH'
COMPONENTS_OTHER_HASH = 'COMPONENTS_OTHER_HASH'
COMPONENTS_HMI_VR_HASH = 'COMPONENTS_HMI_VR_HASH'

#PROJECT_ISSUE_ANALYZED key
SUMMARY = 'summary'
CONTENT = 'content'
ANALYZEMODULE = 'module from llm'
REALMODULE = 'module'
COMMITMODULE = 'commit module by tester'
PROMPT = 'prompt'
MODEL = 'model'
RESULT = 'result'
ISSUE = 'issue'
USER = 'user'
STARTTIME = 'starttime'
FINISHTIME = 'finishtime'
MATCH = 'match'
RESOLVER = 'RESOLVER'
ISSUETYPE = 'ISSUETYPE'

#PROMPT_HASH key
PROMPT_USER_GATEGORY = 'PROMPT_USER_GATEGORY'
PROMPT_SYSTEM_GATEGORY = 'PROMPT_SYSTEM_GATEGORY'
PROMPT_USER_GATEGORY_FOR_SUMMARY = 'PROMPT_USER_GATEGORY_FOR_SUMMARY'
PROMPT_SYSTEM_GATEGORY_FOR_SUMMARY = 'PROMPT_SYSTEM_GATEGORY_FOR_SUMMARY'

#HH_TO_SY_JIRA_HASH
HH_TO_SY_JIRA_HASH = 'HH_TO_SY_JIRA_HASH'

#WATCHING_MATES_LIST
WATCHING_MATES_LIST = 'WATCHING_MATES_LIST'

#MCPSERVER key
MCP_SERVER_HASH = 'MCP_SERVER_HASH'

#COMPONENTS_LIST key
COMPONENTS_LIST = "COMPONENTS_LIST"

#ISSUE_ANALYZE_STATUS_HASH
ISSUE_ANALYZE_STATUS_HASH = "ISSUE_ANALYZE_STATUS_HASH"

#ISSUE_TOOL_HASH
ISSUE_TOOL_HASH = "ISSUE_TOOL_HASH"

#FUNCTION_INTERFACE_HASH key
FUNCTION_INTERFACE_HASH = 'FUNCTION_INTERFACE_HASH'

def getFunctionInterfaceForModule(mod: str) -> str:
    server = 'xingrd'
    if redis.hexists(FUNCTION_INTERFACE_HASH, mod):
        server = redis.hget(FUNCTION_INTERFACE_HASH, mod)
    return server

def setFunctionInterfaceForModule(mod: str, server: str) -> str:
    redis.hset(FUNCTION_INTERFACE_HASH, mod, server)
    
    return 'Succeeded to set MCP server.'

def getMcpServerForModule(mod: str) -> str:
    server = 'http://localhost:8005/mcp'
    if redis.hexists(MCP_SERVER_HASH, mod):
        server = redis.hget(MCP_SERVER_HASH, mod)
    return server

def setMcpServerForModule(mod: str, server: str) -> str:
    if not server.startswith('http://') and not server.startswith('https://'):
        return 'Failed to set MCP server, invalid URL format.'

    redis.hset(MCP_SERVER_HASH, mod, server)
    
    return 'Succeeded to set MCP server.'

def getWorkingList():
    list = set()
    for item in redis.hgetall(SETTING_ACTIVE_FO_HASH).keys():
        if redis.hget(SETTING_ACTIVE_FO_HASH, item) == 'True':
            list.add(item)
    return list

def getModel() -> str:
    model = redis.get(SETTING_LLM_MODEL)
    if model is None:
        model = "deepseek-r1:70b"
    return model

def getSystemPrompt() -> str:
    prompt = ''
    if redis.hexists(PROMPT_HASH, PROMPT_SYSTEM_GATEGORY):
        prompt = redis.hget(PROMPT_HASH, PROMPT_SYSTEM_GATEGORY)
    else:
        prompt = """
            你是一个导航应用专家，了解导航应用的各个功能子系统，以及子系统对应的功能。请利用你的知识给结构化的回答。
        """
    return prompt

def getPrompt() -> str:
    prompt = ''
    if redis.hexists(PROMPT_HASH, PROMPT_USER_GATEGORY):
        prompt = redis.hget(PROMPT_HASH, PROMPT_USER_GATEGORY)
    else:
        prompt = """
            我提取了一个Jira系统上的bug的Summary，description，comments。请结合你的知识给出结构性的回答：
            1. 这个bug属于哪个功能子系统
            2. 子系统的具体功能点
            3. 问题发生的时间点
            4. bug的日志路径
            请按照序号回答，如果没有相关信息，请回答None.
            """
    return prompt

def getSystemPromptForSummary() -> str:
    prompt = ''
    if redis.hexists(PROMPT_HASH, PROMPT_SYSTEM_GATEGORY_FOR_SUMMARY):
        prompt = redis.hget(PROMPT_HASH, PROMPT_SYSTEM_GATEGORY_FOR_SUMMARY)
    else:
        prompt = """
            你是一个导航应用专家，了解导航应用的各个功能子系统，以及子系统对应的功能。你需要总结导航系统已经解决的bug的解决办法。
        """
    return prompt

def getPromptForSummary() -> str:
    prompt = ''
    if redis.hexists(PROMPT_HASH, PROMPT_USER_GATEGORY_FOR_SUMMARY):
        prompt = redis.hget(PROMPT_HASH, PROMPT_USER_GATEGORY_FOR_SUMMARY)
    else:
        prompt = """
            以下5个Jira系统上的bug的Summary，description，comments。请结合你的知识给出结构性的回答：
            1. 请结合comments的描述，总结5个bug的分析结论
            2. 总结这一类问题的分析方法
            3. 如果标题描述有不同可以分类总结不同的分析方法
            comments中有一些不是分析的内容，请忽略相关的描述。
            comments中可能有一些日志输出，他们全是英文，可能是一些代码打出的日志。可以直接数据这部分数据。
            """
    return prompt
