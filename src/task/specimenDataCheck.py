from Mcp.server.jira import api
from src.helper.Redis import *
from src.helper import Ollama, Log
import time
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
        'Activation_DBU': COMPONENTS_ACTIVITION_DBU_HASH
    }

    # Test with a sample issue key
    try:
        for table in componentDict.keys():
            for issue_key in redis.hkeys(componentDict[table]):
                history = api.getIssueHistory(issue_key)
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
                jstr = redis.hget(componentDict[table], issue_key)
                dictitem = json.loads(jstr)
                if user != dictitem[USER]:
                    redis.hdel(componentDict[table], issue_key)

                    time.sleep(0.5)
    except Exception as e:
        print(f"Error: {e}")
