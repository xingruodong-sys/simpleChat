from src.helper import Ollama, Log
import os

system_prompt = """
你是C++代码助手,你的任务是整理出代码中的函数，按照以下json格式，填写出json中的字段，每有一个函数输出一个json

“method nmae” 填写函数名
"method function" 根据你读取到的这个函数的代码，判断这个函数的主要功能，填到这里
“logs” 有固定的函数输出，LogDebugStream，LogInfoStream等
"exceptions" 是try catch部分，写出catch是否有打印，列出来

{
    "method name": "",
    "method function": "",
    "logs": [],
    "parameters": [
    {
        "name": "",
        "type": "",
        "description": ""
    },
    {
        "name": "",
        "type": "",
        "description": ""
    }
    ],
    "return_type": "",
    "exceptions": []
    "file_name": ""
},

如果你不能按照json输出，请不要给出输出。
"""

def read_cpp_files(directory):
    i = 0
    """
    遍历给定目录下的所有.cpp文件并读取其内容
    
    :param directory: 要遍历的目录路径
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.cpp'):
                file_path = os.path.join(root, file)
                try:
                    content = f'文件名:\n{file}\代码如下:\n'
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chunk = []
                        for line in f:
                            chunk.append(line)
                            if len(chunk) >= 10 and line == '}\n':
                                content += ''.join(chunk)
                                print(f"文件: {file_path}")
                                print("内容:")
                                print("-" * 50)  # 分隔线
                                model = 'qwen2.5-coder:32b'
                                result = Ollama.chat(system_prompt=system_prompt, prompt=content, modelname=model, key=None, data=None)
                                with open(f'./{file}.json', 'a', encoding='utf-8') as w:
                                    w.write(result)
                                chunk = []
                                content = ''
                except Exception as e:
                    print(f"读取文件 {file_path} 时出错: {e}")

def main():
    path = '/home/lix/Code/Gitlab/earth/nmasdk-bl/mgr/bl/src/map'
    if os.path.isdir(path):
        read_cpp_files(path)
    else:
        print("提供的路径不是一个有效的目录")
