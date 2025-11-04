from src.helper import Log, JiraSy
from src.helper.Redis import *
import json

def getTheFirstComponent(comments, current_component):
    devMember = [
        'meng-xin',
        'lizuoming',
        'meng.ff',
        'gelan',
        'duchp',
        'li.b_li',
        'ly.liuyang.neu',
        'guodch',
        'lu-my',
        'hua-y',
        'dongzhd',
        'zhao.xinhai',
        'dong-q',
        'zheng-j',
        'wangjin.neu',
        'fengcp',
        'gao-dy',
        'wuqingbo',
        'ma-wb',
        'li-sq',
        'weijh',
        'liu.g',
        'wang_jm',
        'yushaobo',
        'xuejing',
        'yanghaoyi',
        'guan-shh',
        'lv.xing',
        'zhao.shj',
        'mgao',
        'zhongjianfeng',
        'zhangl-zhang',
        'wangmengchen',
        'mefl',
        'liu.minghui',
        'jianghd',
        'wang.shulei',
        'zhao.di',
        'dinglp',
        'qinjd',
        'fengyanjun',
        'bao.zhh',
        'xingyu.wang',
        'qubing',
        'feng.yj',
        'liu.yingna',
        'sunxj',
        'wang_zhipeng',
        'jiang.yc',
        'dong.jingyi',
        'duan-zhh',
        'liu-jh',
        'mazhch',
        'xingrd',
        'dong.jiyang',
        'yang-yq',
        'zhangyimian',
        'fangf',
        'qiuye',
        'tiandq',
        'xuyanjie',
        'zenglp',
        'ma.wl',
        'shenyd',
    ]

    searchMember = [
        'wang_jm',
        'yushaobo',
        'xuejing',
    ]
    HMIMember = [
        'yanghaoyi',
        'wang_zhipeng',
        'lv.xing',
        'wang.shulei',
        'dong.jingyi',
        'dinglp',
        'zhangl-zhang',
        'fengyanjun',
        'liu.minghui',
        'zhao.di',
        'qinjd',
        'zhao.shj',
        'liu-jh',
        'mgao',
        'jiang.yc',
        'wangmengchen',
        'guan-shh',
        'xingyu.wang',
        'duan-zhh',
        'sunxj',
        'bao.zhh',
        'mefl',
        'qubing',
        'zhongjianfeng',
        'wang-yanqi',
        'li.b_li',
        'meng-xin',
        'zhao.xinhai',
    ]
    systemMember = [
        'mazhch',
        'xingrd',
        'dong.jiyang',
    ]
    mapMember = [
        'yang-yq',
        'zhangyimian',
    ]
    DBUPosMember = [
        'fangf',
        'qiuye',
    ]
    activationMember = [
        'tiandq'
    ]
    guidanceMember = [
        'xuyanjie',
        'zenglp',
    ]
    routeMember = [
        'ma.wl',
        'shenyd',
    ]
    # trafficMember = {}

    MemberList = {
        'DI_POS_SDS':searchMember,
        'HMI':HMIMember,
        'System':systemMember,
        'MapViewer':mapMember,
        'DBU':DBUPosMember,
        'Activation':activationMember,
        'Guidance':guidanceMember,
        'Route Calculation':routeMember,
        # 'TI':trafficMember
    }
    
    Log.info(f"current_component = {current_component}")
    if current_component == 'TI':
        for comment in comments:
            name = comment[0]
            body = comment[1]
            if '地点' in body and '时间' in body and 'UTC' in body:
                return current_component, name

    name = ''
    component = ''
    for comment in comments:
        name = comment[0]
        body = comment[1]
        if name in devMember:
            for member in MemberList.keys():
                if name in MemberList[member]:
                    component = member
                    Log.info(f"comment = {name}, add = {body}")
                    if name == 'mazhch':
                        if current_component != 'Activation':
                            component = member
                        else:
                            component = 'Activation'
                    if name == 'fangf' or name == 'qiuye':
                        component = current_component
                    break
            break

    if 'Activation' == component and current_component == 'DBU':
        component = 'Activation_DBU'

    Log.info (f'component={component}, name={name}')
    return component, name


if __name__ == "__main__":
    componentDict = {
        'DI_POS_SDS' : COMPONENTS_SEARCH_HASH,
        'HMI' : COMPONENTS_HMI_HASH,
        'System' : COMPONENTS_SYSTEM_HASH,
        'MapViewer' : COMPONENTS_MAP_HASH,
        'DBU' : COMPONENTS_DBU_POS_HASH,
        'Positioning' : COMPONENTS_DBU_POS_HASH,
        'Activation' : COMPONENTS_ACTIVITION_HASH,
        'Guidance' : COMPONENTS_GUIDANCE_HASH,
        'Route Calculation' : COMPONENTS_ROUTE_HASH,
        'TI': COMPONENTS_TI_HASH,
        'Activation_DBU': COMPONENTS_ACTIVITION_DBU_HASH,
        'HMI_VR': COMPONENTS_HMI_VR_HASH
    }

    # Test with a sample issue key
    try:
        dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ")
        jql = "project = NMASDK AND component = 'Voice Recognition'"
        keys = dejira.getIssuesByJql(jql)
        datas = []
        # for issue_key in keys:
        #     history = Jira.getIssueHistory(issue_key)
        #     # Print the formatted results
        #     if "error" in history:
        #         Log.error(f"{issue_key} Error: {history['error']}")
        #         continue
        #     if 'Product bug' != history['issuetype']:
        #         Log.info(f"{issue_key} : {history['issuetype']} is not a bug")
        #         continue

        #     comments = history['comments']
        #     current_components = ''
        #     if history['current_components']:
        #         current_components = history['current_components'][0]
        #     component, user = getTheFirstComponent(comments, current_components)

        #     datas.append({
        #         "issue_key": issue_key,
        #         "component": component
        #     })
        # with open("component.csv", "w", newline="", encoding="utf-8") as f:
        #     if datas:  # 确保数据不为空
        #         writer = csv.DictWriter(f, fieldnames=["issue_key", "component"])
        #         writer.writeheader()  # 写表头
        #         writer.writerows(datas)
        # for i in range(70000, 0, -1):
        for issue_key in keys:
            # issue_key = "NMASDK-" + str(i)
            history = JiraSy.getIssueHistory(issue_key)
            # Print the formatted results
            if "error" in history:
                Log.error(f"{issue_key} Error: {history['error']}")
                continue
            if 'Product bug' != history['issuetype']:
                Log.info(f"{issue_key} : {history['issuetype']} is not a bug")
                continue

            Log.info(f"{issue_key} - {history['summary']}")
            # Log.info(f"{issue_key} - {history['current_status']}")
            Log.info(f"{issue_key} - {', '.join(history['current_components'])}")

            comments = history['comments']
            current_components = ''
            if history['current_components']:
                current_components = history['current_components'][0]
            component, user = getTheFirstComponent(comments, current_components)
            if component == "HMI":
                component = "HMI_VR"
            else:
                continue

            dictObj = {}
            dictObj[COMMITMODULE] = current_components
            dictObj[REALMODULE] = component
            dictObj[SUMMARY] = history['summary']
            dictObj[USER] = user
            dictObj[ISSUETYPE] = history['issuetype']
            jstr = json.dumps(dictObj)
            if component in componentDict.keys():
                redis.hset(componentDict[component], issue_key, jstr)
            else:
                redis.hset(COMPONENTS_OTHER_HASH, issue_key, jstr)

    except Exception as e:
        print(f"Error: {e}")
