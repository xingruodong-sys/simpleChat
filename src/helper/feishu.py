import base64
import hashlib
import hmac
from datetime import datetime
import requests
from src.utils import settings

# 飞书应用配置（替换为你自己的信息）
APP_ID = "cli_a73410e83ab5501c"
APP_SECRET = "B80rrYZPwPqwEJFsZkK6jgSwEs8oRbLM"
FO_TABLE_ID = 'tblC9L5in91RBiUU'
PROJECT_TABLE_ID = 'tblIBnlY5TYAQWLS'
DOC_ID = 'Bc8fb5JtTax5cOsLWW3cLJXvnUg'

feishu_document_content = []

def gen_sign(secret):
    timestamp = int(datetime.now().timestamp())
    # 拼接时间戳以及签名校验
    string_to_sign = '{}\n{}'.format(timestamp, secret)

    # 使用 HMAC-SHA256 进行加密
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()

    # 对结果进行 base64 编码
    sign = base64.b64encode(hmac_code).decode('utf-8')

    return sign

def send_message(message, url, username, password, secret, notify=False, title=""):
    timestamp = int(datetime.now().timestamp())
    sign = gen_sign(secret)
    if not notify:
        params = {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "interactive",
            "card": {
                "elements": [
                    {
                        "tag": "markdown",
                        "content": message,
                    }
                ],
                "header": {
                    "template": "warning",
                    "title": {
                        "content": title,
                    }
                }
            }
        }
    else:
        params = {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "post",  # ✅ 改为 post 类型
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,  # 可选标题
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": message + " "
                                },
                                {
                                    "tag": "at",
                                    "user_id": "all"
                                }
                            ]
                        ]
                    }
                }
            }
        }
    
    proxies = {
        'https': f'http://{username}:{password}@proxy.neusoft.com:8080/'
    }
    resp = requests.post(url, json=params, proxies=proxies)
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") and result.get("code") != 0:
        print(f"feishu发送失败：{result['msg']}")
        return

def get_tenant_access_token():
    proxies = {
        'https': f'http://qiuye:QiuJune.9.1@proxy.neusoft.com:8080/'
    }
    """获取飞书应用的租户访问令牌（tenant_access_token）"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    try:
        response = requests.post(url, headers=headers, json=data, proxies=proxies)
        response.raise_for_status()  # 抛出HTTP异常
        result = response.json()
        if result.get("code") == 0:
            return result["tenant_access_token"]
        else:
            raise Exception(f"获取token失败：{result.get('msg')}")
    except Exception as e:
        raise Exception(f"请求token接口异常：{str(e)}")

def get_bitable_content(token,doc_token,table_id):
    """获取飞书文档的原始内容"""
    proxies = {
        'https': f'http://qiuye:QiuJune.9.1@proxy.neusoft.com:8080/'
    }
    # 1. 获取文档元数据（确认文档类型）
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{doc_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        # 获取元数据
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        result = response.json()

        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"获取文档内容失败：{result.get('msg')}")
    except Exception as e:
        raise Exception(f"获取文档内容异常：{str(e)}")

def extract_fo_content(doc_content, target_key="text"):
    """
    解析飞书文档内容，提取指定类型的内容（默认提取所有文本）
    :param doc_content: 飞书文档原始内容（JSON格式）
    :param target_key: 要提取的内容类型（如text/heading等）
    :return: 提取的内容列表
    """
    content_list = []
    # 解析文档内容（飞书文档内容是JSON数组格式）
 
   #  print(f"extract_fo_content:loads{doc_content}")
    # 遍历items数组
    for item in doc_content.get('items', []):
        # 提取基础字段
        item_info = {
            'id': item.get('id'),
            'record_id': item.get('record_id'),
            'component': item.get('fields', {}).get('Component'),
            'jira_name': item.get('fields', {}).get('Jira显示名称'),
            'projects': item.get('fields', {}).get('Project', []),
            'person': item.get('fields', {}).get('人员'),
            'email': item.get('fields', {}).get('邮箱'),
            'parent_record_table_id': None  # 初始化父记录table_id
        }

        # 解析嵌套的父记录
      #   parent_records = item.get('fields', {}).get('父记录', [])
      #   if parent_records and len(parent_records) > 0:
      #       item_info['parent_record_table_id'] = parent_records[0].get('table_id')
        if item_info['component'] != None:
         content_list.append(item_info)
   #  print(f"extract_fo_content:content_list{content_list}")
    return content_list

def extract_project_content(doc_content, target_key="text"):
    """
    解析飞书文档内容，提取指定类型的内容（默认提取所有文本）
    :param doc_content: 飞书文档原始内容（JSON格式）
    :param target_key: 要提取的内容类型（如text/heading等）
    :return: 提取的内容列表
    """
    content_list = []
    # 解析文档内容（飞书文档内容是JSON数组格式）
 
    # 遍历items数组
    for item in doc_content.get('items', []):
        # 提取基础字段
        item_info = {
            'project': item.get('fields', {}).get('Project'),
            'req_customer': item.get('fields', {}).get('Req. by Customer'),
        }

        # 解析嵌套的父记录
      #   parent_records = item.get('fields', {}).get('父记录', [])
      #   if parent_records and len(parent_records) > 0:
      #       item_info['parent_record_table_id'] = parent_records[0].get('table_id')
        
        if item_info['project'] != None:
         content_list.append(item_info)

    return content_list

def insert_req_customer_to_fo_table(table1_records, table2_records, target_key="req_customer"):
   """
   批量处理：将表1的req_customer字段插入表2（按project匹配）
   支持单表2记录匹配多表1记录，用列表存储多个req_customer

   Args:
      table1_records (list): 表1的多条记录（字典列表）
      table2_records (list): 表2的多条记录（字典列表）
      target_key (str): 表2中存储req_customer的键名

   Returns:
      list: 处理后的表2所有记录（原数据不修改）
   """
   # 复制表2数据，避免修改原始列表和字典
   processed_table2 = []
   for table2_item in table2_records:
      # 深拷贝确保嵌套结构不被修改（浅拷贝仅复制第一层）
      table2_copy = table2_item.copy()
      # 提取当前表2记录的projects列表
      table2_projects = table2_copy.get('projects', [])

      # 收集所有匹配的req_customer
      matched_customers = []
      for table1_item in table1_records:
         table1_project = table1_item.get('project')
         table1_customer = table1_item.get('req_customer')

         # 匹配条件：project在列表中 + req_customer非空
         if table1_project in table2_projects and table1_customer is not None:
               matched_customers.append(table1_customer)

      # 插入匹配的req_customer（无匹配则不新增字段）
      if matched_customers:
         # 单条匹配则存字符串，多条则存列表（兼容两种场景）
         table2_copy[target_key] = matched_customers[0] if len(matched_customers) == 1 else matched_customers
         #print(f"表2记录[id={table2_copy['id']}]成功插入{target_key}：{table2_copy[target_key]}")
      else:
         print(f"表2记录[id={table2_copy['id']}]无匹配的project，未插入{target_key}")

      processed_table2.append(table2_copy)

   return processed_table2

def get_feish_document_content():
    result = []
    try:
        # 1. 获取访问令牌
        token = get_tenant_access_token()
        print("成功获取访问令牌")

        # 2. 获取文档原始内容
        fo_doc_content = get_bitable_content(token,DOC_ID,FO_TABLE_ID)
        # 3. 提取指定内容（这里提取所有文本内容）
        fo_content = extract_fo_content(fo_doc_content)

        # 4. 获取文档原始内容
        project_doc_content = get_bitable_content(token,DOC_ID,PROJECT_TABLE_ID)
        # 5. 提取指定内容（这里提取所有文本内容）
        project_content = extract_project_content(project_doc_content)

        # 6. 将两个表进行合并
        all_content = insert_req_customer_to_fo_table(project_content, fo_content)

        #print("提取的文档内容：")
        for idx, content in enumerate(all_content, 1):
            #print(f"{idx}. {content}")
            result.append(content)

    except Exception as e:
        print(f"程序执行失败：{str(e)}")
   
    return result

def getFunctionOwnerByComponent(component,req_customer):
    print(f"getFunctionOwnerByComponent:{component}, {req_customer}")
    global feishu_document_content
    fo = "Naiser-T3000"

    if not feishu_document_content:
      feishu_document_content = get_feish_document_content()

    for item in feishu_document_content:
         if item['component'] == component:
             for customer in item.get('req_customer', []):
                 if customer == req_customer:
                     fo = item['jira_name']
                     break

    return fo

def updateFeishuDocumentContent():
    print(f"updateFeishuDocumentContent")
    global feishu_document_content

    feishu_document_content = get_feish_document_content()

    print("提取的文档内容：")
    for idx, content in enumerate(feishu_document_content, 1):
      print(f"{idx}. {content}")

