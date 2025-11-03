from Mcp.server.jira import api
from src.helper.Redis import *
from src.helper import Ollama, Log
import time
import json

if __name__ == "__main__":
    authorList = [
        'yang-yq',
        'xuyanjie',
        'ma.wl',
        'wang_jm',
        'yushaobo',
        'zhangyimian',
        'xuejing',
        'zenglp'
    ]

    componentTable = {
        'yang-yq': 'MapViewer',
        'xuyanjie': 'Guidance',
        'ma.wl': 'Route Calculation',
        'wang_jm': 'DI_POI_SDS',
        'yushaobo': 'DI_POI_SDS',
        'zhangyimian': 'MapViewer',
        'xuejing': 'DI_POI_SDS',
        'zenglp': 'Guidance'
    }

    # Test with a sample issue key
    try:
        for i in redis.hkeys(SPECIMEN_STANDARD_HASH):
            print(redis.hget(SPECIMEN_STANDARD_HASH,i))
            issue_key = i
            history = api.getIssueHistory(issue_key)
            # Print the formatted results
            if "error" in history:
                Log.error(f"{issue_key} Error: {history['error']}")
                continue

            # Log.info(f"{issue_key} - {history['summary']}")
            # Log.info(f"{issue_key} - {history['current_status']}")
            Log.info(f"{issue_key} - {', '.join(history['current_components'])}")
            dictObj = {}
            for change in history['changes']:
                if change['field'] == 'status':
                    Log.info(f"[{change['date']}] {change['author']} changed {change['field']}: {change['from_value']} → {change['to_value']}")
                    if change['from_value'] == 'Implementation' and change['to_value'] == 'Integration':
                        if change['author'] in authorList:
                            if history['current_components']:
                                component = history['current_components'][0]
                                dictObj[COMMITMODULE] = component
                                dictObj[REALMODULE] = componentTable[change['author']]
                                dictObj[RESOLVER] = change['author']
                                if component == componentTable[change['author']]:
                                    dictObj[MATCH] = True
                                else:
                                    dictObj[MATCH] = False
                                jstr = json.dumps(dictObj)
                                redis.hset(SPECIMEN_STANDARD_HASH, issue_key, jstr)
                                continue
            time.sleep(0.5)
    except Exception as e:
        print(f"Error: {e}")
