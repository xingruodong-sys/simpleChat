import base64
import hashlib
import hmac
from datetime import datetime
import requests
from src.utils import settings


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
