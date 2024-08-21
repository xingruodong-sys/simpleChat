# encoding: utf-8
# from langchain_community.llms.ollama import Ollama

# llm = Ollama(model="gemma2:2b")
# print(llm.invoke('为什么天空是蓝色的'))


import ollama
 
# 流式输出
def api_generate(text:str):
  print(f'提问：{text}')
 
  stream = ollama.generate(
    stream=True,
    model='gemma2:2b',
    prompt=text,
    )
 
  print('-'*20)
  for chunk in stream:
    if not chunk['done']:
      print(chunk['response'], end='', flush=True)
    else:
      print('\n')
      print('-----------------------------------------')
      print(f'总耗时：{chunk["total_duration"]}')
      print('-----------------------------------------')
 
 
if __name__ == '__main__':
  # 流式输出
  api_generate(text='天空为什么是蓝色的？')
 