import json
import requests
import os
from QA import *
from utils import *
import logging
from AISearch import self_AI_search
from copy import deepcopy
from datetime import datetime



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
    profile_content=''
    response = ColdRead(query=deepcopy(question))
    for content in response:
        if content:
            profile_content+=content
        dict_data = FrontWrapper_Body(None,content)
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
    log_json['profile']=profile_content
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
        
        
    
    #再生成ADT
    dict_data = FrontWrapper_Body(None,f'# Formulating Candidate Structure\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    
    adt_content=''
    response = ADT_generation(question=deepcopy(question), personality_traits=profile_content)
    for content in response:
        if content:
            adt_content+=content
        dict_data = FrontWrapper_Body(None,content)
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
    dict_data = FrontWrapper_Body(None,'\n\n')
    json_data = json.dumps(dict_data)
    yield f'data: {json_data}\n\n'
    log_json['ADT']=adt_content
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
    
    
    
    #再去网上搜索
    AI_search_content_full=''
    citations=[]
    
    subquestion_list = rewrite(question=deepcopy(question))
    log_json['subquestion']={}
    with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
        json.dump(log_json, f, ensure_ascii=False, indent=4)
    
    print('subquestion_list',subquestion_list)
    
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
        AI_search_content_list=[]
        
        AI_search_content=''
        for title,content in local_external_knowledge_dict.items():
            spanned_content=''
            response=SpanPredict(adt=deepcopy(adt_content), article=deepcopy(content))
            for chunk in response:
                if chunk:
                    spanned_content+=chunk
            spanned_content=spanned_content.split('Reformatted Article')[1].replace('```xml','\n').replace('```','\n').strip()
                    
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

    
    external_knowledge_str_local_list=[]
    # 接着对candidate_items_list 中的每一个进行补充和校验
    for index,candidate_item in enumerate(candidate_items_list):
        external_knowledge_str_local=''
        name=candidate_item.get('Name','NOT FOUND')
        log_json['AI_search_content_for_complete']={f'{name}':{}}
        with open(f'AI_search_content/{time_stamp}.json','w', encoding="utf-8") as f:
            json.dump(log_json, f, ensure_ascii=False, indent=4)
            
        if name == 'NOT FOUND':
            continue
        dict_data = FrontWrapper_Body(None,f'# Checking Validation of Candidate Item: *{name}*\n\n')
        json_data = json.dumps(dict_data)
        yield f'data: {json_data}\n\n'
        
        valid = True
        # 当 candidate_item 中仍存在 'NOT FOUND' 时，继续循环
        while any(value == 'NOT FOUND' for value in candidate_item.values()):
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
                spanned_content = ''
                response = SpanPredict(adt=deepcopy(adt_content), article=deepcopy(content))
                for chunk in response:
                    if chunk:
                        spanned_content += chunk
                spanned_content = spanned_content.split('Reformatted Article')[1].replace('```xml', '\n').replace('```', '\n').strip()
                
                # 根据搜索到的内容进行补全，可能会同时补全多个 attribute
                completed_candidate_item = complete(
                    candidate_item=deepcopy(candidate_item),
                    article=deepcopy(spanned_content),
                    ADT=adt_content
                )
                
                log_json['AI_search_content_for_complete'][f'{name}'] = {
                    'missing_key': missing_key,
                    'title': title,
                    'content': content,
                    'spanned_content': spanned_content,
                    'completed_candidate_item': completed_candidate_item
                }
                with open(f'AI_search_content/{time_stamp}.json', 'w', encoding="utf-8") as f:
                    json.dump(log_json, f, ensure_ascii=False, indent=4)
            
                # 更新 candidate_item 为最新补全的结果，准备下次循环检查是否仍有缺失项
                candidate_item = completed_candidate_item
                

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
        
        
        
    
     