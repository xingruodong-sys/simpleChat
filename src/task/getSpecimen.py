from Mcp.server.jira import api
from src.helper.Redis import *
from src.helper import Ollama, Log
import time

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

    # Test with a sample issue key
    try:
        for i in range(60000, 1, -1):
            issue_key = "NMASDK-" + str(i)
            history = api.getIssueHistory(issue_key)
            # Print the formatted results
            if "error" in history:
                Log.error(f"{issue_key} Error: {history['error']}")
                continue

            # Log.info(f"{issue_key} - {history['summary']}")
            # Log.info(f"{issue_key} - {history['current_status']}")
            Log.info(f"{issue_key} - {', '.join(history['current_components'])}")
            for change in history['changes']:
                if change['field'] == 'status':
                    Log.info(f"[{change['date']}] {change['author']} changed {change['field']}: {change['from_value']} → {change['to_value']}")
                    if change['from_value'] == 'Implementation' and change['to_value'] == 'Integration':
                        if change['author'] in authorList:
                            if history['current_components']:
                                component = history['current_components'][0]
                                redis.hset(SPECIMEN_STANDARD_HASH, issue_key, component)
                            if redis.hlen(SPECIMEN_STANDARD_HASH) <= 2000:
                                continue
                            else:
                                break
            time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
