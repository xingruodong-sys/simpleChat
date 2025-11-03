from Mcp.server.jira import api
from src.helper.Redis import *
from src.helper import Ollama, Log
import time
import re
import json


def getComponent(module:str):
    mod = module.lower()
    com = []
    data1 = {
        'map' : ['MapViewer'],
        'guidance' : ['Guidance', 'GuidanceViewer'],
        'route' : ['EV', 'Route Calculating'],
        'search': ['DI_POI_SDS'],
        'traffic': ['TI'],
        'dbu': ['DBU'],
        'position': ['Demo Mode', 'Positioning'],
        'system': ['Activation', 'System', 'Voice Recognition'],
        'hmi': ['HMI', 'Style'],
    }
    if mod in data1.keys():
        com = data1[mod]
    return com

def extract_json_from_text(text):
    """
    从文本中提取JSON部分
    
    Args:
        text (str): 包含JSON的文本
        
    Returns:
        dict: 提取的JSON对象，如果没有找到则为None
    """
    # 尝试寻找JSON格式的字符串 (通常在```json和```之间)
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(json_pattern, text)
    
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("找到JSON格式文本，但解析失败")
            return None
    
    # 尝试在文本中寻找任何JSON对象 (从第一个{到匹配的})
    json_pattern = r'(\{[\s\S]*\})'
    matches = re.findall(json_pattern, text)
    
    for potential_json in matches:
        try:
            # 验证这是有效的JSON
            parsed_json = json.loads(potential_json)
            return parsed_json
        except json.JSONDecodeError:
            continue
    
    print("未找到有效的JSON")
    return None

def analyzeIssueModule(issue):
    return module

# Example usage
if __name__ == "__main__":
    # Test with a sample issue key
    try:
        total = 0
        match = 0
        for i in range(40000, 50000):
            total = total + 1
            issue_key = "NMASDK-" + str(i)
            stime = time.time()
            content = api.getIssueContent(issue_key)
            prompt = getPrompt() + '\n' + content
            system_prompt = getSystemPrompt()
            model = getModel()
            result = Ollama.chat(system_prompt=system_prompt, prompt=prompt, modelname=model, key=None, data=None)
            resultDict = extract_json_from_text(result)
            module = ''

            if resultDict is not None:
                if resultDict['module'] is not None:
                    module = resultDict['module']
            ftime = time.time()
            dictObj = {}
            dictObj[CONTENT] = content
            dictObj[ANALYZEMODULE] = module
            dictObj[REALMODULE] = ''
            dictObj[PROMPT] = prompt
            dictObj[MODEL] = model
            dictObj[RESULT] = result
            dictObj[ISSUE] = issue_key
            dictObj[MATCH] = False
            dictObj[STARTTIME] = stime
            dictObj[FINISHTIME] = ftime
            
            history = api.getIssueHistory(issue_key)
            Log.info(f'module = {module}')
            Log.info(f'module = {getComponent(module)}')
            if history['current_components']:
                dictObj[REALMODULE] = history['current_components'][0]
                if history['current_components'][0] in getComponent(module):
                    match = match + 1
                    dictObj[MATCH] = True

            jstr = json.dumps(dictObj)
            redis.hset(USER_GIVEN_ISSUE_ANALYZED, issue_key, jstr)
            # Print the formatted results
            if "error" in history:
                Log.error(f"{issue_key} Error: {history['error']}")
                continue

            # Log.info(f"{issue_key} - {history['summary']}")
            # Log.info(f"{issue_key} - {history['current_status']}")
            Log.info(f"{issue_key} - {', '.join(history['current_components'])}")
            
            for change in history['changes']:
                Log.info(f"[{change['date']}] {change['author']} changed {change['field']}: {change['from_value']} → {change['to_value']}")

                if change['field'] == 'Component':
                    if change['author'] != history['reporter']:
                        if change['author'] in api.getProjectComponentsLead():
                            redis.sadd(COMPONENTS_CHANGE_BY_FO_SET, issue_key)
                        else:
                            redis.sadd(COMPONENTS_CHANGE_BY_DEV_SET, issue_key)
                        continue
            time.sleep(1)
        Log.info(f"总共分析了{total}个问题，有{match}个分析正确，正确率{match / total}")
    except Exception as e:
        print(f"Error: {e}")
