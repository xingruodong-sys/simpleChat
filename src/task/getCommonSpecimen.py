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
        'BL_DI_POI_SDS':searchMember,
        'HMI':HMIMember,
        'BL_System':systemMember,
        'BL_MapViewer':mapMember,
        'BL_DBU':DBUPosMember,
        'BL_Activation':activationMember,
        'BL_Guidance':guidanceMember,
        'BL_RouteCalculation':routeMember,
        # 'BL_TI':trafficMember
    }
    
    Log.info(f"current_component = {current_component}")
    if current_component == 'BL_TI':
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
                        if current_component != 'BL_Activation':
                            component = member
                        else:
                            component = 'BL_Activation'
                    if name == 'fangf' or name == 'qiuye':
                        component = current_component
                    break
            break

    if 'BL_Activation' == component and current_component == 'BL_DBU':
        component = 'Activation_DBU'

    if 'HMI' == component and current_component == 'HMI_Platform_VR':
        component = 'HMI_Platform_VR'
    
    if current_component == "Performance":
        component = "Performance"

    Log.info (f'component={component}, name={name}')
    return component, name

def bert_resource():
    componentDict = {
        'BL_DI_POI_SDS' : BL_COMPONENTS_SEARCH_HASH,
        'HMI' : BL_COMPONENTS_HMI_HASH,
        'BL_System' : BL_COMPONENTS_SYSTEM_HASH,
        'BL_MapViewer' : BL_COMPONENTS_MAP_HASH,
        'BL_DBU' : BL_COMPONENTS_DBU_POS_HASH,
        'Positioning' : BL_COMPONENTS_DBU_POS_HASH,
        'BL_Activation' : BL_COMPONENTS_ACTIVITION_HASH,
        'BL_Guidance' : BL_COMPONENTS_GUIDANCE_HASH,
        'BL_RouteCalculation' : BL_COMPONENTS_ROUTE_HASH,
        'BL_TI': BL_COMPONENTS_TI_HASH,
        'Activation_DBU': BL_COMPONENTS_ACTIVITION_DBU_HASH,
        'HMI_Platform_VR': BL_COMPONENTS_HMI_VR_HASH,
        'Performance': BL_COMPONENTS_PERFORMANCE_HASH,
    }

    try:
        dejira = JiraSy.JiraImp("https://naisjira.neusoft.com", "xingrd", "1qaz!QAZ1qaz")
        for i in range(100000, 0, -1):
            issue_key = "NMASDK-" + str(i)
            history = dejira.getIssueHistory(issue_key)
            if not history:
                continue
            type = history.get('issuetype')
            if type is None:
                continue
            if type.name != "Product bug":
                continue
            comments = history.get('comments')
            if not comments:
                continue
            current_components = history.get('current_components')
            if not current_components:
                continue

            current_components = current_components[0]
            component, user = getTheFirstComponent(comments, current_components)
            dictObj = {
                COMMITMODULE: current_components,
                REALMODULE: component,
                SUMMARY: history['summary'],
                USER: user,
            }
            if component in componentDict.keys():
                redis.hset(componentDict[component], issue_key, json.dumps(dictObj))
            else:
                redis.hset(COMPONENTS_OTHER_HASH, issue_key, json.dumps(dictObj))

    except Exception as e:
        print(f"Error: {e}")
