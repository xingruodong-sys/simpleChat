import chromadb
from chromadb.utils import embedding_functions
import os
from src.helper import Jira
from src.helper.Redis import *
import time
import re


host = os.getenv('CHROMA_DB_HOST', '10.10.90.4')
port = os.getenv('CHROMA_DB_PORT', 8000)
embed_model = os.getenv('EMBEDDINGS_MODEL_NAME', 'bge-m3:latest')
base_model = os.getenv('BASE_MODEL_HOST', 'http://10.146.12.2:11434')

openai_ef = embedding_functions.OllamaEmbeddingFunction(
    url=base_model,
    model_name=embed_model
)

class ChromaDBImpl:
    collection = None
    client = None

    def __init__(self, id):
        try:
            self.client = chromadb.HttpClient(host=host, port=port)
            self.collection = self.client.get_collection(id)
        except Exception as e:
            print(f"Error: {e}")

        if self.collection is None:
            self.collection = self.client.create_collection(name=id)

    def embed(self, source):
        try:
            self.students_embeddings = openai_ef(source)
        except Exception as e:
            print(f"Error: {e}")

    def add(self, documents, metadatas, ids):
        # 添加数据到集合
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=openai_ef(documents),
            ids=ids,
        )

    def query(self, source,title_type = None ):
        results = self.collection.query(
            query_texts=source,
            query_embeddings=openai_ef(source),
            n_results=5,
            where={"title_type": title_type} if title_type else None,
        )
        return results

def remove_brackets_and_content(text):
    # 匹配 [] 中的内容并移除
    text = re.sub(r'\[.*?\]', '', text)
    # 匹配 【】 中的内容并移除
    text = re.sub(r'【.*?】', '', text)
    text = re.sub(r'^[^\w\s]*(\d{1,2}[:：]\d{1,2})\s*', '', text)
    text = re.sub(r'^[^\w]*', '', text.strip())

    return text

def add_job(impl):
    try:
        for i in range(63614, 50000, -1):
            issue_key = "NMASDK-" + str(i)
            content = Jira.getIssueContentExt(issue_key)
            if content['type'] != 'Product bug':
                continue
            
            if content['description'] is None:
                content['description'] = 'None'

            documents = [
                content['summary'],
                content['description'],
            ]
            metadatas = [
                {issue_key: 'summary info'},
                {issue_key: 'description info'},
            ]
            ids=['summary', 'description']

            title_type = analyze_search_type(content['summary'])
            for comment in content['comments']:
                documents.append(f'comment by {comment['name']}:{comment['body']}')
                metadatas.append({issue_key:'comments', 'name':comment['name'],'title_type': title_type})
                ids.append(f'{issue_key}: comment by {comment['name']} at {comment['created']}')
            impl.add(documents, metadatas, ids)
            print(f"add issue_key={issue_key}")
            time.sleep(0.2)
        print("finish job")
    except Exception as e:
        print(f"Error: {e}")

def add_job_no_comments(impl):
    try:
        for i in range(65000, 55000, -1):
            issue_key = "NMASDK-" + str(i)
            content = Jira.getIssueContentExt(issue_key)
            if content['type'] != 'Product bug':
                continue
            
            if content['description'] is None:
                content['description'] = 'None'

            documents = [
                'summary:' + content['summary'] + '\n description:' + content['description'],
            ]
            metadatas = [
                {issue_key: 'summary and description info'},
            ]
            ids=[issue_key]
            impl.add(documents, metadatas, ids)
            print(f"add issue_key={issue_key}")
            time.sleep(0.2)
        print("finish job")
    except Exception as e:
        print(f"Error: {e}")

def add_job_no_comments_strip(impl):
    try:
        for i in range(65000, 50000, -1):
            issue_key = "NMASDK-" + str(i)
            content = Jira.getIssueContentExt(issue_key)
            if content['type'] != 'Product bug':
                continue
            
            if content['description'] is None:
                content['description'] = 'None'

            summary = remove_brackets_and_content(content['summary'])
            documents = [
                'summary:' + summary + '\n description:' + content['description'],
            ]
            metadatas = [
                {issue_key: 'summary and description info'},
            ]
            ids=[issue_key]
            impl.add(documents, metadatas, ids)
            print(f"add issue_key={issue_key}, summary={summary}")
            time.sleep(0.2)
        print("finish job")
    except Exception as e:
        print(f"Error: {e}")

def do_query(impl, key, strip=False):
    content1 = Jira.getIssueContentExt(key)
    source = 'summary:' + content1['summary'] + '\n description:' + content1['description']
    res = impl.query(source)
    ids = res['ids']
    dis = res['distances']
    print(ids)
    result = ''
    for issues in ids:
        for issue in issues:
            content = Jira.getIssueContentExt(issue)
            result = 'issue id : ' + issue + '\n' + 'summary:' + content['summary'] + '\n description:' + content['description'] + '\n comments: '
            for comment in content['comments']:
                result = result + f'comment by {comment['name']}:{comment['body']}' + '\n'
    return result, ids, dis

def do_query_strip(impl, key):
    content1 = Jira.getIssueContentExt(key)
    if content1['type'] != 'Product bug':
        return [], [], [], [], False
    source = 'summary:' + remove_brackets_and_content(content1['summary']) + '\n description:' + str(content1['description'])
    title_type = analyze_search_type(content1['summary'])
    res = impl.query(source,title_type)
    ids = res['ids']
    dis = res['distances']
    src = res['documents']

    return source, ids, dis, src, True


def analyze_search_type(title):
    """
    分析标题类型
    如果标题中包含 'Yandex' 或 '独联体'，则返回对应的类型，否则返回 'other'
    :param title: Jira issue title
    :return: title_type

    """
    title_mapping = {
        'Yandex': 'Yandex&独联体',
        '独联体': 'Yandex&独联体'
    }

    title_type = "other"
    for keyword, type_name in title_mapping.items():
        if keyword in title:
            title_type = type_name
            break
    return title_type

if __name__ == '__main__':
    # impl = ChromaDBImpl('jira')
    # impl = ChromaDBImpl('jira_no_comments')
    impl = ChromaDBImpl('jira_strip')
    # add_job(impl)
    # add_job_no_comments(impl)
    add_job_no_comments_strip(impl)
# print(results.keys())

# print(results)

# # Or for async usage:
# async def main():
#     client = await chromadb.AsyncHttpClient(host='localhost', port=8000)

# import chromadb

# client = chromadb.HttpClient(host="127.0.0.1",
#                                port=8000,
#                                settings=chromadb.Settings(
#                                   chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
#                                    chroma_client_auth_credentials="your_token"))

# import chromadb
# from chromadb.config import Settings

# # 创建持久化客户端，数据将保存在 "db/" 目录中
# client = chromadb.Client(Settings(
#     chroma_db_impl="duckdb+parquet",
#     persist_directory="db/"
# ))
