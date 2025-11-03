from Mcp.server.jira import api
from src.helper import Ollama, Log
import os

system_prompt = """
你是一个代码助手,结合给定的代码文件，总结每个函数函数功能，所包含的日志，给出结构化输出。
"""

def read_cpp_files(directory):
    """
    遍历给定目录下的所有.cpp文件并读取其内容
    
    :param directory: 要遍历的目录路径
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.cpp'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"文件: {file_path}")
                        print("内容:")
                        print(content)
                        print("-" * 50)  # 分隔线
                except Exception as e:
                    print(f"读取文件 {file_path} 时出错: {e}")

if __name__ == "__main__":
    path = '/home/lix/Code/Gitlab/earth/nmasdk-bl/mgr/bl/src'
    if os.path.isdir(path):
        read_cpp_files(path)
    else:
        print("提供的路径不是一个有效的目录")


# model = 'gemma3:27b'
# result = Ollama.chat(system_prompt=system_prompt, prompt=prompt, modelname=model, key=None, data=None)
# print(result)
