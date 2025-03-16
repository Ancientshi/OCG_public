import json
import requests
import os
from QA import *
from utils import *
import logging
from AISearch import self_AI_search
from copy import deepcopy
from datetime import datetime
import re


def generate_response_rec(data):
    question = data.get('question', '')  
    model=data.get('model','')  
    time_stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_json={}
    log_json['question']=question
    log_json['model']=model
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
    
    #先生成personality traits 
    profile_content=ColdRead(query=deepcopy(question))
    log_json['profile']=profile_content
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
        
        
    
    #再生成ADT
    dict_data = FrontWrapper_Body(None,f'# Formulating Candidate Structure\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    adt_content = ADT_generation(question=deepcopy(question), personality_traits=profile_content)
    log_json['ADT']=adt_content
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
    
    dict_data = FrontWrapper_Body(None,adt_content+'\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    
    #再去网上搜索
    AI_search_content_full=''
    citations=[]
    
    subquestion_list = rewrite(question=deepcopy(question))
    print('subquestion_list',subquestion_list)
    log_json['subquestion']={}
    for subquestion in subquestion_list:
        log_json['subquestion'][subquestion]={'AI_search_content_list':[],'citations':[]}
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
    
    
    candidate_items_list_global=[]
    for subquestion in subquestion_list:
        log_json['subquestion'][subquestion]={'AI_search_content_list':[],'citations':[]}
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
            
        dict_data = FrontWrapper_Body(None,f'# Searching: *{subquestion}*\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
            
        
        local_external_knowledge_dict,local_set=self_AI_search(
            query=subquestion,pagenum=1,threshold=0.0,existed_citation_list=deepcopy(list(citations))
        )

        print(f">>> content的正文和title是：{local_external_knowledge_dict}")
        AI_search_content_list=[]
        
        AI_search_content=''
        for title,content in local_external_knowledge_dict.items():
            #shn: 处理检索杂质
            content = content_post_process(content)  # 对 content 进行后处理
            spanned_content = SpanPredict(adt=deepcopy(adt_content), article=deepcopy(content))
                    
            # 接着根据搜到的内容，生成candidate items
            candidate_items_list_local = Extract(article=deepcopy(spanned_content),ADT=deepcopy(adt_content))
            candidate_items_list_global.append(candidate_items_list_local)
            AI_search_content_list.append({
                'title':title,
                'content':content,
                'spanned_content':spanned_content,
                'candidate_items_list_local':candidate_items_list_local
            })
            AI_search_content+=f'{title}\n\n{spanned_content}\n\n'
          
        AI_search_content_replaced=replace_citation_indices(AI_search_content, local_set,existing_citation_number=len(citations))  
        log_json['subquestion'][subquestion]['AI_search_content_list']=AI_search_content_list
        log_json['subquestion'][subquestion]['citations']=list(local_set)
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
        
        citations.extend(list(local_set))
        AI_search_content_full+=f'{subquestion}\n\n{AI_search_content_replaced}\n\n'
        
        dict_data = FrontWrapper_Body(None,'\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
        
    
    # 输出准备好的candidate_items_list
    dict_data = FrontWrapper_Body(None,f'# Prepare Candidate Items List:\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'

    
    candidate_items_list=candidate_items_list_merge(candidate_items_list_global)
    dict_data = FrontWrapper_Body(None,'\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    log_json['candidate_items_list_prepare']=candidate_items_list
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)

    log_json['AI_search_content_for_complete']={}
    external_knowledge_str_local_list=[]
    # 接着对candidate_items_list 中的每一个进行补充和校验
    for index,candidate_item in enumerate(candidate_items_list):
        external_knowledge_str_local=''
        name=candidate_item.get('Name','NOT FOUND')
        if name == 'NOT FOUND':
            continue
        
        log_json['AI_search_content_for_complete'][name]={}
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
            
        
        dict_data = FrontWrapper_Body(None,f'# Checking Validation of Candidate Item: *{name}*\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
        
        valid = True
        max_loop_times=2
        loop_times=0
        # 当 candidate_item 中仍存在 'NOT FOUND' 时，继续循环
        while any(value == 'NOT FOUND' for value in candidate_item.values()) and loop_times<max_loop_times:
            valid=False
            # 找出第一个缺失的 key
            missing_key = None
            for key, value in candidate_item.items():
                if value == 'NOT FOUND':
                    missing_key = key
                    break
            if missing_key is None:
                break  # 无缺失项，退出循环

            in_context_situation = f'''
                User ask for: {question}
                For a candidate item: {name}
                Need to find related information about the {missing_key} for it.
            '''
            generated_query = generate_single_query(in_context_situation=in_context_situation)
            
            dict_data = FrontWrapper_Body(
                None,
                f'# Searching related information about the {missing_key} for {name}. Query {generated_query}\n\n'
            )
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
            
            local_external_knowledge_dict, local_set = self_AI_search(
                query=generated_query, pagenum=1, threshold=0.0, existed_citation_list=deepcopy(list(citations))
            )
            citations.extend(list(local_set))
            
            # 遍历搜索到的结果，并利用其内容去补全 candidate_item
            for title, content in local_external_knowledge_dict.items():
                #shn: 处理检索杂质
                content = content_post_process(content)  # 对 content 进行后处理
                spanned_content = SpanPredict(adt=deepcopy(adt_content), article=deepcopy(content))
                
                # 根据搜索到的内容进行补全，可能会同时补全多个 attribute
                completed_candidate_item = complete(
                    candidate_item=deepcopy(candidate_item),
                    article=deepcopy(spanned_content),
                    ADT=adt_content
                )
                
                log_json['AI_search_content_for_complete'][name] = {
                    'in_context_situation': in_context_situation,
                    'title': title,
                    'content': content,
                    'spanned_content': spanned_content,
                    'candidate_item': candidate_item,
                    'completed_candidate_item': completed_candidate_item
                }
                with open(f'AI_search_content/{time_stamp}.json', 'w', encoding="utf-8") as f:
                    json.dump(log_json, f, ensure_ascii=False, indent=4)

                if completed_candidate_item.get('Name', 'NOT FOUND') == 'NOT FOUND':
                    candidate_item = candidate_item  # 补全失败，candidate_item 保持不变
                else:
                    # 更新 candidate_item 为最新补全的结果，准备下次循环检查是否仍有缺失项
                    candidate_item = completed_candidate_item
            
            loop_times+=1 

        dict_data = FrontWrapper_Body(None,'\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
    
        if valid:
            dict_data=FrontWrapper_Body(None,f'# Candidate Item: *{name}* is valid.\n\n')
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
        else:
            dict_data=FrontWrapper_Body(None,f'# Candidate Item: *{name}* is not valid. Complete it.\n\n')
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
            
            #更新candidate_items_list
            candidate_items_list[index]=candidate_item

    candidate_items_list_valid=[item for item in candidate_items_list if item.get('Name','NOT FOUND')!='NOT FOUND']
    candidate_items_list=candidate_items_list_valid
    log_json['candidate_items_list_final']=candidate_items_list
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
        
    # 输出准备好的candidate_items_list
    dict_data = FrontWrapper_Body(None,f'# Candidate Items List:\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    dict_data = FrontWrapper_Body(None,f'''```json\n{json.dumps(candidate_items_list,indent=4)}\n```\n\n''')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    print(f'Open Candidate Generation Finished, generated {len(candidate_items_list)} candidate items.')
    print(f'The names are {[item.get("Name","NOT FOUND") for item in candidate_items_list]}')
    
    yield candidate_items_list
    
    
    # # 最后进行排序
    # candidate_items_final_str=''''''

    # for _index,candidate in enumerate(candidate_items_list):
    #     candidate_items_final_str+=f'### Candidate Item {_index}\n'
    #     for key,value in candidate.items():
    #         candidate_items_final_str+=f'{key}:{value}\n'
    #     candidate_items_final_str+='\n'

    # response = answer_question(question=deepcopy(question),historical_qa=[],external_knowledge_str=deepcopy(candidate_items_final_str),mindmap=mindmap,user_material_str='',model=model)     
    # content_full_final=''
    # reasoning_content_full=''
    # for item in response:
    #     content = None
    #     reasoning_content = None
    #     if isinstance(item, tuple) and len(item) == 2:
    #         content, reasoning_content = item
    #     else:
    #         content = item
    #         reason_content = None
    #     if content:
    #         content_full_final+=content
    #     if reasoning_content:
    #         reasoning_content_full+=reasoning_content
            
    #     dict_data = FrontWrapper_Body(content,reasoning_content)
    #     json_data = json.dumps(dict_data)
    #     yield f'data: {json_data}\n\n'

    # log_json['final_response']={'content':content_full_final,'reasoning':reasoning_content_full}
    # with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
    #     json.dump(log_json, f, ensure_ascii=False, indent=4)
        
    # #下面是作为对比的
    # # 1. 直接用full AI search content 回答
    # response = answer_question(question=deepcopy(question),historical_qa=[],external_knowledge_str=deepcopy(AI_search_content_full),mindmap=mindmap,user_material_str='',model=model)
    # content_full_final=''
    # reasoning_content_full=''
    # for item in response:
    #     content = None
    #     reasoning_content = None
    #     if isinstance(item, tuple) and len(item) == 2:
    #         content, reasoning_content = item
    #     else:
    #         content = item
    #         reason_content = None
    #     if content:
    #         content_full_final+=content
    #     if reasoning_content:
    #         reasoning_content_full+=reasoning_content

    # log_json['final_response_baseline1']={'content':content_full_final,'reasoning':reasoning_content_full}
    # with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
    #     json.dump(log_json, f, ensure_ascii=False, indent=4)
        
    # # 然后是baseline2，用所有的搜到的东西回答
    # external_knowledge_str_global='\n\n'.join(external_knowledge_str_local_list)
    # response = answer_question(question=deepcopy(question),historical_qa=[],external_knowledge_str=deepcopy(external_knowledge_str_global),mindmap=mindmap,user_material_str='',model=model)
    # content_full_final=''
    # reasoning_content_full=''
    # for item in response:
    #     content = None
    #     reasoning_content = None
    #     if isinstance(item, tuple) and len(item) == 2:
    #         content, reasoning_content = item
    #     else:
    #         content = item
    #         reason_content = None
    #     if content:
    #         content_full_final+=content
    #     if reasoning_content:
    #         reasoning_content_full+=reasoning_content
    # log_json['final_response_baseline2']={'content':content_full_final,'reasoning':reasoning_content_full}
    
    # #把log_json 用utf-8解码后写入文件
      
    # with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
    #     json.dump(log_json, f, ensure_ascii=False, indent=4)
        
        

def generate_response_rec_with_checkpoint(data,checkpoint_json_file):
    #写一个自动判断调用哪个函数的函数
    with open(checkpoint_json_file, 'r') as f:
        checkpoint_json=json.loads(f.read())
    
    #如果没有candidate_items_list_prepare这个key，调用generate_response_rec_with_checkpoint_subquestion
    if 'candidate_items_list_prepare' not in checkpoint_json.keys():
        for chunk in generate_response_rec_with_checkpoint_subquestion(data,checkpoint_json_file):
            yield chunk
    #如果有AI_search_content_for_complete这个key，但是没有candidate_items_list_final这个key，调用generate_response_rec_with_checkpoint_complete
    elif 'candidate_items_list_final' not in checkpoint_json.keys() and 'AI_search_content_for_complete' in checkpoint_json.keys():
        for chunk in generate_response_rec_with_checkpoint_complete(data,checkpoint_json_file):
            yield chunk
    else:
        print('No situation matched')
        
        
    
def generate_response_rec_with_checkpoint_subquestion(data,checkpoint_json_file):
    #subquestion未完成，继续
    question = data.get('question', '')  
    model=data.get('model','')  
    time_stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    with open(checkpoint_json_file, 'r') as f:
        checkpoint_json=json.loads(f.read())
    
    log_json={}
    log_json['question']=question
    log_json['model']=model
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
    
    profile_content=checkpoint_json['profile']
    adt_content=checkpoint_json['ADT']
    subquestion_list=list(checkpoint_json['subquestion'].keys())
    citations=[]
    AI_search_content_full=''
    log_json=checkpoint_json
    
    
    candidate_items_list_global=[]
    for subquestion in subquestion_list:
        if log_json['subquestion'][subquestion]['AI_search_content_list']!=[]:
            continue
        
        log_json['subquestion'][subquestion]={'AI_search_content_list':[],'citations':[]}
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
            
        dict_data = FrontWrapper_Body(None,f'# Searching: *{subquestion}*\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
            
        
        local_external_knowledge_dict,local_set=self_AI_search(
            query=subquestion,pagenum=1,threshold=0.0,existed_citation_list=deepcopy(list(citations))
        )
        AI_search_content_list=[]
        
        AI_search_content=''
        for title,content in local_external_knowledge_dict.items():
            #shn: 处理检索杂质
            content = content_post_process(content)  # 对 content 进行后处理
            spanned_content = SpanPredict(adt=deepcopy(adt_content), article=deepcopy(content))
                    
            # 接着根据搜到的内容，生成candidate items
            candidate_items_list_local = Extract(article=deepcopy(spanned_content),ADT=deepcopy(adt_content))
            candidate_items_list_global.append(candidate_items_list_local)
            AI_search_content_list.append({
                'title':title,
                'content':content,
                'spanned_content':spanned_content,
                'candidate_items_list_local':candidate_items_list_local
            })
            AI_search_content+=f'{title}\n\n{spanned_content}\n\n'
          
        AI_search_content_replaced=replace_citation_indices(AI_search_content, local_set,existing_citation_number=len(citations))  
        log_json['subquestion'][subquestion]['AI_search_content_list']=AI_search_content_list
        log_json['subquestion'][subquestion]['citations']=list(local_set)
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
        
        citations.extend(list(local_set))
        AI_search_content_full+=f'{subquestion}\n\n{AI_search_content_replaced}\n\n'
        
        dict_data = FrontWrapper_Body(None,'\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
        
    
    # 输出准备好的candidate_items_list
    dict_data = FrontWrapper_Body(None,f'# Prepare Candidate Items List:\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'

    
    candidate_items_list=candidate_items_list_merge(candidate_items_list_global)
    dict_data = FrontWrapper_Body(None,'\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    log_json['candidate_items_list_prepare']=candidate_items_list
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)

    log_json['AI_search_content_for_complete']={}
    external_knowledge_str_local_list=[]
    # 接着对candidate_items_list 中的每一个进行补充和校验
    for index,candidate_item in enumerate(candidate_items_list):
        external_knowledge_str_local=''
        name=candidate_item.get('Name','NOT FOUND')
        if name == 'NOT FOUND':
            continue
        
        log_json['AI_search_content_for_complete'][name]={}
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
            
        
        dict_data = FrontWrapper_Body(None,f'# Checking Validation of Candidate Item: *{name}*\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
        
        valid = True
        max_loop_times=2
        loop_times=0
        # 当 candidate_item 中仍存在 'NOT FOUND' 时，继续循环
        while any(value == 'NOT FOUND' for value in candidate_item.values()) and loop_times<max_loop_times:
            valid=False
            # 找出第一个缺失的 key
            missing_key = None
            for key, value in candidate_item.items():
                if value == 'NOT FOUND':
                    missing_key = key
                    break
            if missing_key is None:
                break  # 无缺失项，退出循环

            in_context_situation = f'''
                User ask for: {question}
                For a candidate item: {name}
                Need to find related information about the {missing_key} for it.
            '''
            generated_query = generate_single_query(in_context_situation=in_context_situation)
            
            dict_data = FrontWrapper_Body(
                None,
                f'# Searching related information about the {missing_key} for {name}. Query {generated_query}\n\n'
            )
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
            
            local_external_knowledge_dict, local_set = self_AI_search(
                query=generated_query, pagenum=1, threshold=0.0, existed_citation_list=deepcopy(list(citations))
            )
            citations.extend(list(local_set))
            
            # 遍历搜索到的结果，并利用其内容去补全 candidate_item
            for title, content in local_external_knowledge_dict.items():
                #shn: 处理检索杂质
                content = content_post_process(content)  # 对 content 进行后处理
                spanned_content = SpanPredict(adt=deepcopy(adt_content), article=deepcopy(content))
                
                # 根据搜索到的内容进行补全，可能会同时补全多个 attribute
                completed_candidate_item = complete(
                    candidate_item=deepcopy(candidate_item),
                    article=deepcopy(spanned_content),
                    ADT=adt_content
                )
                
                log_json['AI_search_content_for_complete'][name] = {
                    'in_context_situation': in_context_situation,
                    'title': title,
                    'content': content,
                    'spanned_content': spanned_content,
                    'candidate_item': candidate_item,
                    'completed_candidate_item': completed_candidate_item
                }
                with open(f'AI_search_content/{time_stamp}.json', 'w', encoding="utf-8") as f:
                    json.dump(log_json, f, ensure_ascii=False, indent=4)

                if completed_candidate_item.get('Name', 'NOT FOUND') == 'NOT FOUND':
                    candidate_item = candidate_item  # 补全失败，candidate_item 保持不变
                else:
                    # 更新 candidate_item 为最新补全的结果，准备下次循环检查是否仍有缺失项
                    candidate_item = completed_candidate_item
            
            loop_times+=1 

        dict_data = FrontWrapper_Body(None,'\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
    
        if valid:
            dict_data=FrontWrapper_Body(None,f'# Candidate Item: *{name}* is valid.\n\n')
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
        else:
            dict_data=FrontWrapper_Body(None,f'# Candidate Item: *{name}* is not valid. Complete it.\n\n')
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
            
            #更新candidate_items_list
            candidate_items_list[index]=candidate_item

    candidate_items_list_valid=[item for item in candidate_items_list if item.get('Name','NOT FOUND')!='NOT FOUND']
    candidate_items_list=candidate_items_list_valid
    log_json['candidate_items_list_final']=candidate_items_list
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
        
    # 输出准备好的candidate_items_list
    dict_data = FrontWrapper_Body(None,f'# Candidate Items List:\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    dict_data = FrontWrapper_Body(None,f'''```json\n{json.dumps(candidate_items_list,indent=4)}\n```\n\n''')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    print(f'Open Candidate Generation Finished, generated {len(candidate_items_list)} candidate items.')
    print(f'The names are {[item.get("Name","NOT FOUND") for item in candidate_items_list]}')
    
    yield candidate_items_list
    
    

def generate_response_rec_with_checkpoint_AI_search_content_for_complete(data,checkpoint_json_file):
    #从AI_search_content_for_complete 开始
    
    question = data.get('question', '')  
    model=data.get('model','')  
    time_stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    with open(checkpoint_json_file, 'r') as f:
        checkpoint_json=json.loads(f.read())
        
    log_json={}
    log_json['question']=question
    log_json['model']=model
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
        
        
    
    adt_content=checkpoint_json['ADT']
    citations=[]
    AI_search_content_for_complete=checkpoint_json['AI_search_content_for_complete']
    candidate_items_list=checkpoint_json['candidate_items_list_prepare']
    log_json=checkpoint_json
    
    #检查一遍candidate_items_list中valid的index
    valid_name_list=[]
    for key,value in AI_search_content_for_complete.items():
        in_context_situation=value.get('in_context_situation','')
        title=value.get('title','')
        content=value.get('content','')
        spanned_content=value.get('spanned_content','')
        candidate_item=value.get('candidate_item',{})
        completed_candidate_item=value.get('completed_candidate_item',{})
        if in_context_situation!='' and title!='' and content!='' and spanned_content!='' and candidate_item!={} and completed_candidate_item!={}:
            valid_name_list.append(key)
    
    log_json['AI_search_content_for_complete']={}
    external_knowledge_str_local_list=[]
    # 接着对candidate_items_list 中的每一个进行补充和校验
    for index,candidate_item in enumerate(candidate_items_list):
        external_knowledge_str_local=''
        name=candidate_item.get('Name','NOT FOUND')
        if name == 'NOT FOUND' or name in valid_name_list:
            continue
        log_json['AI_search_content_for_complete'][name]={}
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
            
        
        dict_data = FrontWrapper_Body(None,f'# Checking Validation of Candidate Item: *{name}*\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
        
        valid = True
        max_loop_times=2
        loop_times=0
        # 当 candidate_item 中仍存在 'NOT FOUND' 时，继续循环
        while any(value == 'NOT FOUND' for value in candidate_item.values()) and loop_times<max_loop_times:
            valid=False
            # 找出第一个缺失的 key
            missing_key = None
            for key, value in candidate_item.items():
                if value == 'NOT FOUND':
                    missing_key = key
                    break
            if missing_key is None:
                break  # 无缺失项，退出循环

            in_context_situation = f'''
                User ask for: {question}
                For a candidate item: {name}
                Need to find related information about the {missing_key} for it.
            '''
            generated_query = generate_single_query(in_context_situation=in_context_situation)
            
            dict_data = FrontWrapper_Body(
                None,
                f'# Searching related information about the {missing_key} for {name}. Query {generated_query}\n\n'
            )
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
            
            local_external_knowledge_dict, local_set = self_AI_search(
                query=generated_query, pagenum=1, threshold=0.0, existed_citation_list=deepcopy(list(citations))
            )
            citations.extend(list(local_set))
            
            # 遍历搜索到的结果，并利用其内容去补全 candidate_item
            for title, content in local_external_knowledge_dict.items():
                #shn: 处理检索杂质
                content = content_post_process(content)  # 对 content 进行后处理
                spanned_content = SpanPredict(adt=deepcopy(adt_content), article=deepcopy(content))
                
                # 根据搜索到的内容进行补全，可能会同时补全多个 attribute
                completed_candidate_item = complete(
                    candidate_item=deepcopy(candidate_item),
                    article=deepcopy(spanned_content),
                    ADT=adt_content
                )
                
                log_json['AI_search_content_for_complete'][name] = {
                    'in_context_situation': in_context_situation,
                    'title': title,
                    'content': content,
                    'spanned_content': spanned_content,
                    'candidate_item': candidate_item,
                    'completed_candidate_item': completed_candidate_item
                }
                with open(f'AI_search_content/{time_stamp}.json', 'w', encoding="utf-8") as f:
                    json.dump(log_json, f, ensure_ascii=False, indent=4)

                if completed_candidate_item.get('Name', 'NOT FOUND') == 'NOT FOUND':
                    candidate_item = candidate_item  # 补全失败，candidate_item 保持不变
                else:
                    # 更新 candidate_item 为最新补全的结果，准备下次循环检查是否仍有缺失项
                    candidate_item = completed_candidate_item
            
            loop_times+=1 

        dict_data = FrontWrapper_Body(None,'\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
    
        if valid:
            dict_data=FrontWrapper_Body(None,f'# Candidate Item: *{name}* is valid.\n\n')
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
        else:
            dict_data=FrontWrapper_Body(None,f'# Candidate Item: *{name}* is not valid. Complete it.\n\n')
            json_data = json.dumps(dict_data)
            yield f'data: {json_data}\n\n'
            
            #更新candidate_items_list
            candidate_items_list[index]=candidate_item

    candidate_items_list_valid=[item for item in candidate_items_list if item.get('Name','NOT FOUND')!='NOT FOUND']
    candidate_items_list=candidate_items_list_valid
    log_json['candidate_items_list_final']=candidate_items_list
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
        
    # 输出准备好的candidate_items_list
    dict_data = FrontWrapper_Body(None,f'# Candidate Items List:\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    dict_data = FrontWrapper_Body(None,f'''```json\n{json.dumps(candidate_items_list,indent=4)}\n```\n\n''')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    print(f'Open Candidate Generation Finished, generated {len(candidate_items_list)} candidate items.')
    print(f'The names are {[item.get("Name","NOT FOUND") for item in candidate_items_list]}')
    
    yield candidate_items_list