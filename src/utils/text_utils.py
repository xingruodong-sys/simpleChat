import re
from datetime import datetime
from typing import List, Dict


def extract_paths(text) -> List[Dict[str, str]]:
    pattern = r'\\\\[^\\\r\n]+\\[^\\\r\n]+(?:\\[^\r\n\\]+[^\\\s\r\n])*(?:\\[^\r\n\\]*[^\\\s\r\n])?(?=[\s.,;:]|$)'
    matches = re.findall(pattern, text)

    results = []
    for path in matches:
        parts = path.split('\\')
        if len(parts) >= 4:
            ip = parts[2]
            share_name = parts[3] if len(parts) > 3 else ''
            path_parts = parts[4:] if len(parts) > 4 else []
            path_str = '\\'.join(path_parts)
            results.append({
                'full_path': path,
                'ip': ip,
                'share_name': share_name,
                'path': path_str
            })
    # 返回匹配结果
    return results

def extract_and_format_time(text):
    patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})[^\d]*(\d{1,2})[:：](\d{1,2})[:：](\d{1,2})',    # 年-月-日 时:分:秒
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})[^\d]*(\d{1,2})[:：](\d{1,2})',                  # 年-月-日 时:分
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})[^\d]*(\d{1,2})[:：](\d{1,2})[:：](\d{1,2})',  # 月-日-年 时:分:秒
        r'(\d{1,2})[:：](\d{1,2})[:：](\d{1,2})',                                           # 时:分:秒
        r'(\d{1,2})[-/](\d{1,2})[^\d]*(\d{1,2})[:：](\d{1,2})[:：](\d{1,2})',               # 月-日 时:分:秒
        r'(\d{1,2})[:：](\d{1,2})',                                                         # 分:秒
    ]
    month = '32'
    day = '32'
    hour = '25'
    minute = '60'
    second = '60'
    year = '1970'
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 6:
                    if len(groups[0]) == 4:
                        year, month, day, hour, minute, second = groups
                    else:
                        month, day, year, hour, minute, second = groups
                elif len(groups) == 3:
                    hour, minute, second = groups
                elif len(groups) == 5:
                    if len(groups[0]) == 4:
                        year, month, day, hour, minute = groups
                    else:
                        month, day, hour, minute, second = groups
                elif len(groups) == 2:
                    hour, minute = groups

                if year:
                    year = f"{int(year):04d}"
                if month:
                    month = f"{int(month):02d}"
                if day:
                    day = f"{int(day):02d}"
                if hour:
                    hour = f"{int(hour):02d}"
                if minute:
                    minute = f"{int(minute):02d}"
                if second:
                    second = f"{int(second):02d}"
                
                return f"{year}-{month}-{day} {hour}:{minute}:{second}"
            except (ValueError, IndexError):
                continue
    return "None"

def strip_description(text):
    pattern = re.compile(
        r'(【重现步骤】.*?)(?=【实际结果】)(【实际结果】.*?)(?=【预期结果】)(【预期结果】.*?)(?=【|$)',
        re.DOTALL
    )

    match = pattern.search(text)
    res = ''
    if match:
        res = ''.join(match.groups()).strip()
    else:
        print("未匹配到字段")
    print(res)
    return res

def remove_brackets_and_content(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'【.*?】', '', text)
    text = re.sub(r'^[^\w\s]*(\d{1,2}[:：]\d{1,2})\s*', '', text)
    text = re.sub(r'^[^\w]*', '', text.strip())
    return text

def strip(text):
    matches = re.findall(r'"([^"]*)"', text)
    for content in matches:
        return content
