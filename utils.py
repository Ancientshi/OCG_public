import copy
import openai
import requests
from aiohttp import ClientSession
import os
import sys
import requests
import json
import concurrent.futures
import time
import random
import concurrent.futures
import logging
import re
from transformers import LongformerTokenizer
from rank_bm25 import BM25Okapi
import numpy as np
from config import *
import torch
from copy import deepcopy
#bge_reranker = BGE_Reranker()

# 指定设备
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志级别
# 创建 FileHandler 以将日志输出到文件中
file_handler = logging.FileHandler(gpt_log_path)  # 指定日志文件位置
file_handler.setLevel(logging.INFO)
# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
# 将 handler 添加到 logger 中
logger.addHandler(file_handler)


# 设置缓存目录
os.environ["TRANSFORMERS_CACHE"] = cache_dir
os.environ['OPENAI_API_KEY'] = openai_api_key
os.environ["SILICONFLOW_API_KEY"] = silicon_flow_key
os.environ["ERK_API_KEY"] = erk_key


def GPT_QA_not_stream(prompt, model_name="gpt-4o-mini", t=0.0, historical_qa=None):
    url = "https://api.openai.com/v1/chat/completions"
    openai.api_key = os.environ["OPENAI_API_KEY"]
    
    if len(prompt)>120000*3:
        prompt=prompt[:120000*3]
    
    
    messages = []
    if historical_qa is not None:
        messages = historical_qa   
    messages.append({"role": "user", "content": prompt})
    
    if model_name=='gpt-4o-mini':
        max_tokens=16384
    else:
        max_tokens=4096
        
    client = openai.OpenAI()
    

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=t,
            n=1,
            service_tier='default',
            max_tokens=max_tokens,
            stream=False
        )
    except Exception as e:
        logger.error(f'Error: {str(e)}, Currently Unavailable.', exc_info=True)
        return f'Error: {str(e)}, Currently Unavailable.'
    
    return response.choices[0].message.content



def SiliconFlow_QA_not_stream(prompt,model_name="deepseek-ai/DeepSeek-R1", t=0.0,historical_qa=None):
    url = "https://api.siliconflow.cn/v1/chat/completions"
    
    api_key=os.environ["SILICONFLOW_API_KEY"]
    if len(prompt)>64000*3:
        prompt=prompt[:64000*3]
    
    messages = []
    if historical_qa is not None:
        messages = historical_qa
    messages.append({"role": "user", "content": prompt})
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": model_name,
        "messages": messages,
        "n": 1,
        "stream": False,
        "max_tokens": 4096,
        #温度
        "temperature": t,
        #累计概率
        "top_p": 0.8,
        #考虑的词
        "top_k": 50
    }
                
    response = requests.post(url, json=data, headers=headers, stream=False)
    if response.status_code == 200:
        dict_chunk = json.loads(response.text)  # 解析 JSON
        content=dict_chunk['choices'][0]['message']['content']
        return content
    else:
        return f"Error from SiliconFlow API: {response.text}"
        

def SiliconFlow_QA(prompt,model_name="deepseek-ai/DeepSeek-R1", t=0.0, historical_qa=None):
    url = 'https://api.siliconflow.cn/v1'
    api_key=os.environ["SILICONFLOW_API_KEY"]
    if len(prompt)>10000*3:
        prompt=prompt[:10000*3]

    messages = []
    if historical_qa is not None:
        messages = historical_qa   
    messages.append({"role": "user", "content": prompt})
        
    client = openai.OpenAI(
        base_url=url,
        api_key=api_key
    )
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=t,
            #累计概率
            top_p=0.8,
            # #考虑的词
            # top_k=50,
            n=1,
            max_tokens=4096,
            stream=True
        )
        for chunk in response:
            delta=chunk.choices[0].delta
            if delta is not None:
                delta=dict(delta)
                content=delta.get('content','')
                reasoning_content=delta.get('reasoning_content','')
                yield content,reasoning_content
            
    except Exception as e:
        logger.error(f'Error: {str(e)}, Currently Unavailable.', exc_info=True)
        #打印错误信息
        print(f'Error: {str(e)}, Currently Unavailable.')
        yield f'Error: {str(e)}, Currently Unavailable.',None

def ERK_QA(prompt,model_name="deepseek-r1-250120", t=0.6, historical_qa=None):
    url = 'https://ark.cn-beijing.volces.com/api/v3'
    api_key=os.environ["ERK_API_KEY"]
    if len(prompt)>64000*3:
        prompt=prompt[:64000*3]

    messages = []
    if historical_qa is not None:
        messages = historical_qa   
    messages.append({"role": "user", "content": prompt})
        
    client = openai.OpenAI(
        base_url=url,
        api_key=api_key
    )
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=t,
            #累计概率
            top_p=0.8,
            # #考虑的词
            # top_k=50,
            n=1,
            max_tokens=4096,
            stream=True
        )
        for chunk in response:
            delta=chunk.choices[0].delta
            if delta is not None:
                delta=dict(delta)
                content=delta.get('content','')
                reasoning_content=delta.get('reasoning_content','')
                yield content,reasoning_content
            
    except Exception as e:
        logger.error(f'Error: {str(e)}, Currently Unavailable.', exc_info=True)
        return f'Error: {str(e)}, Currently Unavailable.'

    
def GPT_QA_reasoning(prompt, model_name="o3-mini", t=0.0, historical_qa=None):
    url = "https://api.openai.com/v1/chat/completions"
    openai.api_key = os.environ["OPENAI_API_KEY"]
    
    if len(prompt)>120000*3:
        prompt=prompt[:120000*3]
    
    
    messages = []
    if historical_qa is not None:
        messages = historical_qa   
    messages.append({"role": "user", "content": prompt})
    
    max_completion_tokens=4096
        
    client = openai.OpenAI()
    

    try:
        response = client.chat.completions.create(
            model=model_name,
            reasoning_effort="medium",
            messages=messages,
            n=1,
            service_tier='default',
            max_completion_tokens=max_completion_tokens,
            stream=True
        )
    except Exception as e:
        logger.error(f'Error: {str(e)}, Currently Unavailable.', exc_info=True)
        return f'Error: {str(e)}, Currently Unavailable.'
    

    for chunk in response:
        delta=chunk.choices[0].delta
        if delta is not None:
            delta=dict(delta)
            content=delta.get('content','')
            reasoning_content=delta.get('reasoning_content',None)
            yield content,reasoning_content
                    
    
def GPT_QA(prompt, model_name="gpt-4o-mini", t=0.0, historical_qa=None):
    url = "https://api.openai.com/v1/chat/completions"
    openai.api_key = os.environ["OPENAI_API_KEY"]
    
    if len(prompt)>120000*3:
        prompt=prompt[:120000*3]
    
    
    messages = []
    if historical_qa is not None:
        messages = historical_qa   
    messages.append({"role": "user", "content": prompt})
    
    if model_name=='gpt-4o-mini':
        max_tokens=16384
    else:
        max_tokens=4096
        
    client = openai.OpenAI()
    

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=t,
            n=1,
            service_tier='default',
            max_tokens=max_tokens,
            stream=True
        )
    except Exception as e:
        logger.error(f'Error: {str(e)}, Currently Unavailable.', exc_info=True)
        return f'Error: {str(e)}, Currently Unavailable.'
    

    for chunk in response:
        delta=chunk.choices[0].delta
        if delta is not None:
            delta=dict(delta)
            content=delta.get('content','')
            yield content
                    
 


def GPT_read_file(doc_file):
    doc_content = ''
    with open(doc_file, 'r') as f:
        doc_content = f.read()
    
    #prompt template path
    prompt_template_path = os.path.join(proj_path, "prompt/summarize.txt")
    with open(prompt_template_path, 'r') as f:
        prompt_template = f.read()
    prompt= prompt_template.replace("{{document_content}}", doc_content)
    
    response_content=GPT_QA_not_stream(prompt, model_name="gpt-4o-mini", t=0.0)
    return response_content

def read_db_embeddings(db_file_path):
    #读取point, summary, content的embeddings
    point_documents_embeddings_tensor=torch.load(db_file_path.replace('.jsonl','_point.pt'))
    summary_documents_embeddings_tensor=torch.load(db_file_path.replace('.jsonl','_summary.pt'))
    content_documents_embeddings_tensor=torch.load(db_file_path.replace('.jsonl','_content.pt'))
    return point_documents_embeddings_tensor,summary_documents_embeddings_tensor,content_documents_embeddings_tensor


def read_knowledge_points_from_db(db_file_path='Knowledge/database.jsonl'):
    '''
    从数据库中读取知识点
    doc_file 是一个jsonl文件，每一行是一个json对象，包含了一个文档的内容
    '''
    knowledge_points = []
    with open(db_file_path, 'r') as f:
        for i, line in enumerate(f):
            knowledge_points.append(json.loads(line))
    return knowledge_points

def handle_knowledge_points_string(source,knowledge_points_string):
    '''
    source 是doc_file 的路径
    knowledge_points_string 是gpt生成的知识点字符串，是jsonl的字符串形式
    '''
    #需要一行一行读取，每一行是个json
    knowledge_points = []
    for line in knowledge_points_string.split('\n'):
        knowledge_point=json.loads(line)
        #加一个timestamp的key
        knowledge_point['timestamp']=time.time()
        knowledge_points.append(knowledge_point)
        #加一个source的key
        knowledge_point['source']=source
    return knowledge_points



def filter_content_bm25(page_content, query, threshold=3,maxlength = 10000):
    if threshold==0:
        return page_content
    
    toker = LongformerTokenizer.from_pretrained("allenai/longformer-base-4096")
    
    # 分割文本为句子
    sentences = page_content.split("\n\n")
    #去掉空
    sentences = [sentence for sentence in sentences if sentence.strip()]
    
    # 分词
    tokenized_sentences = [toker.encode(sentence.lower()) for sentence in sentences]
    tokenized_query = toker.encode(query.lower())

    # 初始化BM25
    bm25 = BM25Okapi(tokenized_sentences)

    # 为每个句子计算BM25得分
    scores = bm25.get_scores(tokenized_query)
    
    # #绘制分数分布图
    # import matplotlib.pyplot as plt
    # plt.hist(scores, bins=100)
    # plt.savefig('score_distribution.png')


    percentile_score = np.percentile(scores, 80)
    threshold=max(percentile_score,threshold)
    relevant_sentences = [sentences[i] for i in range(len(sentences)) if scores[i] >= threshold and len(sentences[i])>5]
    
    #重组句子
    page_content = '\n\n'.join(relevant_sentences)
    
    #取前maxlength个单词
    words_list=page_content.split(' ')
    words_count = len(words_list)
    maxlength=min(maxlength-300,words_count)
    page_content = ' '.join(words_list[:maxlength])


    return page_content



def db_2_embeddings(db_file_path):
    existing_knowledge_points = read_knowledge_points_from_db(db_file_path)
    point_documents_embeddings_tensor,summary_documents_embeddings_tensor,content_documents_embeddings_tensor=knowledge_points_2_embeddings(existing_knowledge_points)
    #存储在db_file_path 同级目录下
    torch.save(point_documents_embeddings_tensor, db_file_path.replace('.jsonl','_point.pt'))
    torch.save(summary_documents_embeddings_tensor, db_file_path.replace('.jsonl','_summary.pt'))
    torch.save(content_documents_embeddings_tensor, db_file_path.replace('.jsonl','_content.pt'))
    #各自打印前2行
    print('The first 2 rows of point_documents_embeddings_tensor:')
    print(point_documents_embeddings_tensor[:2])
    print('The first 2 rows of summary_documents_embeddings_tensor:')
    print(summary_documents_embeddings_tensor[:2])
    print('The first 2 rows of content_documents_embeddings_tensor:')
    print(content_documents_embeddings_tensor[:2])
    print(f'Knowledge Database transfered to embeddings successfully!')

    
    
def knowledge_points_2_embeddings(knowledge_points):
    '''
    希望返回3个tensor矩阵，其中行对应于knowledge_points中的每个元素，第一个矩阵叫做point_embeddings，第二个叫做summary_embeddings，第三个叫做content_embeddings. 其中point_embeddings 每一行是一个(1,5) 的tensor，对应"point": "数据库的意义;计算机内存;数据存储" 这里用分号区分的知识点，不足的补0;
    '''
    point_list=[]
    summary_list=[]
    content_list=[]
    for knowledge_point in knowledge_points:
        point=knowledge_point.get('point','')
        #不足在后面补'None'
        if point.count(';')<4:
            point+=';None'*(4-point.count(';'))
        point_list.append(point)

        summary=knowledge_point.get('summary','')
        summary_list.append(summary)

        content=knowledge_point.get('content','')
        content_list.append(content)
    
    #point_documents 根据分号切分，每个作为一个元素
    point_documents = [item for point in point_list for item in point.split(';')]
    summary_documents=[summary for summary in summary_list]
    content_documents=[content for content in content_list]
    
    point_documents_embeddings=easyrec.get_embedding(point_documents)
    summary_documents_embeddings=easyrec.get_embedding(summary_documents)
    content_documents_embeddings=easyrec.get_embedding(content_documents)
    
    #point_documents_embeddings 再转为tensor 然后reshape成(len(point_list),5,-1)
    point_documents_embeddings_tensor=torch.tensor(point_documents_embeddings).reshape(len(point_list),5,-1)
    summary_documents_embeddings_tensor=torch.tensor(summary_documents_embeddings)
    content_documents_embeddings_tensor=torch.tensor(content_documents_embeddings)
    
    #然后返回这三个tensor
    return point_documents_embeddings_tensor,summary_documents_embeddings_tensor,content_documents_embeddings_tensor
     
    
    

  
def save_knowledge_points_to_db(db_file_path, incremental_knowledge_points):
    '''
    knowledge_points 应该是一个列表，每个元素是一个字典，包含了一个文档的内容
    '''
    existing_knowledge_points = read_knowledge_points_from_db(db_file_path)
    #合并，根据source去重，如果source相同，timestamp 应该有unique的值, 保留最新的
    existing_source_set=set()
    for knowledge_point in existing_knowledge_points:
        existing_source_set.add(knowledge_point['source'])
    
    incremental_source_set=set()
    for knowledge_point in incremental_knowledge_points:
        incremental_source_set.add(knowledge_point['source'])
        
    #找出existing_source_set中与incremental_source_set的交集
    intersection_source_set=existing_source_set.intersection(incremental_source_set)
    
    #从existing_knowledge_points中删除source在intersection_source_set中的元素
    existing_knowledge_points = [x for x in existing_knowledge_points if x['source'] not in intersection_source_set]
    
    #将incremental_knowledge_points中的元素加入到existing_knowledge_points中
    existing_knowledge_points.extend(incremental_knowledge_points)
    
    # 写回文件，使用utf-8编码来确保中文字符不被转义
    with open(db_file_path, 'w', encoding='utf-8') as f:
        for knowledge_point in existing_knowledge_points:
            f.write(json.dumps(knowledge_point, ensure_ascii=False) + '\n')
    return existing_knowledge_points

def FrontWrapper_Header(text_content,type='mindmap'):
    if type=='mindmap':
        json_data = {
            "header": {"content": text_content, "type": "mindmap"},
            "content": None,
            "reasoningContent": None,
            "additionalContent": None,
            "note": None
        }
    else:
        pass
    return json_data
    
    
def FrontWrapper_Body(text_content,reasoning_content=None):
    '''
    封装成大模型问答前端的格式。流式处理
    {
        type: 'source',   # 'rec'| 'source' | 'qrCode',
        actionList:[None], # 专门给rec用的， 用来引导用户下一步
        title:'参考资料:', #参考资料: 
        link: 'https://www.baidu.com' # 链接
    }
    '''
    json_data = {
        "header": None,
        "content": text_content,
        "reasoningContent": reasoning_content,
        "additionalContent": None,
        "note": None
    }
    return json_data
    
def FrontWrapper_Tail(qrCode=None,source=None):
    json_data = {
        "header": None,
        "content": None,
        "reasoningContent": None,
        "additionalContent": {
            "qrCode": qrCode,
            "source": source,
            "rec": []
        },
        "note": None
    }
    return json_data

def FrontWrapper_Note(text_content):
    # dict_data=json.loads(text_content)
    # #确保dict_data里面有begin, end, type, content这四个key; 如果没有，dict_data设置为None
    # if 'begin' not in dict_data:
    #     dict_data['begin']=None
    # if 'end' not in dict_data:
    #     dict_data['end']=None
    # if 'type' not in dict_data:
    #     dict_data['type']=None
    # if 'content' not in dict_data:
    #     dict_data['content']=None
    json_data = {
        "header": None,
        "content": None,
        "reasoningContent": None,
        "additionalContent": None,
        "note": text_content
    }
    return json_data

def get_attachment_list(messages):
    '''
    {
    "messages": [
        {
        "id": 1,
        "author": "user",
        "content": {
            "content_type": "text",
            "parts": [
            "test"
            ]
        },
        "header": null,
        "additionalContent": null,
        "reasoningContent": null,
        "created_at": null,
        "meta_data": {
            "attachments": [
            {
                "id": "1efea9d7-c860-6e20-8e45-64e68432076c",
                "name": "New Microsoft Word Document.docx",
                "size": 16898,
                "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
            ]
        }
        }
    ],
    "question": "test",
    "metadata": {}
    }
    '''
    id_list_all=[]
    #只需要 author 为user
    for message in messages:
        if message['author']=='user':
            attachments = message.get('meta_data', {}).get('attachments', [])
            if attachments:
                id_list = [attachment.get('id') for attachment in attachments]
                id_list_all+=id_list
            else:
                pass
        else:
            pass
    return id_list_all
    

def format_user_material(messages):
    attachment_id_list=get_attachment_list(messages)
    print(attachment_id_list)
    success_flag, file_path_list = download_files(attachment_id_list)
    
    content_list=[]
    if success_flag:
        print("All files downloaded successfully.")
        for file_path in file_path_list:
            content=docling_read_file(file_path)
            content_list.append(content)
        if content_list:
            user_material_str=''
            for index,content in enumerate(content_list):
                user_material_str+=f'''The {index+1}-th user provided file content is: {content}\n\n'''.format(index=index+1,content=content)
            return user_material_str
        else:
            return 'Not Provided.'
    else:
        print("Error downloading files.")
        return 'Not Provided.'
        
def format_historical_qa(messages):
    '''
    '''
    #若messages的长度是0
    if len(messages)==0:
        return []
    else:
        messages=messages[:-1]
        
    historical_qa=[]
    for message in messages:
        role=message.get('author',None)
        parts=message.get('content','').get('parts',None)
        if role is not None and parts is not None:
            #重命名assistance为assistant, 如果role是assistance
            if role=='assistance':
                role='assistant'
            content=''.join(parts)
            historical_qa.append({'role':role,'content':content})
    return historical_qa


def replace_citation_indices(full_content, citations_set, existing_citation_number=0):
    
    # 定义替换函数，按索引从 citations_set 替换
    def replace_match(match):
        try:
            # 提取数字索引，减 1 对应 citations_set 的索引
            index = int(match.group(1)) - 1
            # 确保索引在 citations_set 的范围内
            if 0 <= index < len(citations_set):
                replaced_str = f" [\[{existing_citation_number+index+1}\]]({citations_set[index]})"
                return replaced_str
            else:
                # 如果索引超出范围，保持原样
                return match.group(0)
        except (ValueError, IndexError, AttributeError):
            # 如果解析出错，保持原样
            return match.group(0)
    
    # 用正则匹配 [数字] 格式
    full_content = re.sub(r'\[(\d+)\]', replace_match, full_content)
    return full_content



def candidate_items_list_merge(candidate_items_list_global):
    '''
    candidate_items_list 是一个列表，每个元素是一个列表，每个元素是一个字典，包含了一个文档的内容
    '''
    candidate_items_dict={}
    for candidate_list_local in candidate_items_list_global:
        #if candidate_list_local 是list
        if isinstance(candidate_list_local, list):
            for candidate_item in candidate_list_local:
                name=candidate_item['Name']
                if name not in candidate_items_dict:
                    candidate_items_dict[name]=candidate_item
                else:
                    new_Additional_Information=candidate_item['Additional Information']
                    original_Additional_Information=candidate_items_dict[name]['Additional Information']
                    new_Additional_Information= {} if new_Additional_Information=='NOT FOUND' else new_Additional_Information
                    original_Additional_Information= {} if original_Additional_Information=='NOT FOUND' else original_Additional_Information
                    merged_Additional_Information= {**original_Additional_Information, **new_Additional_Information}
                    
                    old_item=deepcopy(candidate_items_dict[name])
                    new_item=deepcopy(candidate_item)
                    old_item.update(new_item)
                    old_item['Additional Information']=merged_Additional_Information
                    
                    candidate_items_dict[name]=new_item
        else:
            pass

    candidate_items_list=list(candidate_items_dict.values())
    return candidate_items_list
     
      