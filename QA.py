from utils import *
from prompt import *

import threading


def timeout_handler():
    raise TimeoutError("Execution timed out!")


def search_external_knowledge(question):
    external_knowledge_base=search_snippets(question)
    #处理external_knowledge_base，将其拼成txt
    external_knowledge_str=""
    for index,knowledge_point in enumerate(external_knowledge_base):
        point=knowledge_point['point']
        summary=knowledge_point['summary']
        snippet=knowledge_point['snippet']
        knowledge_str=f"### Index {index+1}\n- Point\n{point}\n- Summary\n{summary}\n- Snippet\n{snippet}\n\n"
        external_knowledge_str+=knowledge_str
    return external_knowledge_str

def generate_mindmap(question="SQL的搜索语句怎么写？",historical_qa=None,consider_knowledge=None,user_material_str=''):
    if consider_knowledge != None:
        external_knowledge_str=consider_knowledge
    else:
        external_knowledge_str="Currently We Don\'t Support External Knowledge"
    
    QA_prompt= QA_RAG_TEMPLATE.replace("{{user_question}}", question).replace("{{external_knowledge_str}}", external_knowledge_str).replace("{{user_material_str}}", user_material_str)
    historical_qa=[{
        'role': 'system',
        'content': MINDMAP_SYSTEM
    }]+historical_qa
    answer=GPT_QA_not_stream(QA_prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=historical_qa)
    #answer=SiliconFlow_QA_not_stream(QA_prompt, model_name="deepseek-ai/DeepSeek-V3", t=0.6,historical_qa=historical_qa)
    #如果第一行以```开头，逻辑是去掉第一行和最后一行
    if answer.startswith("```"):
        mindmap='\n'.join(answer.split('\n')[1:-1])
    else:
        mindmap=answer
    
    #对于肯呢个的错误
    mindmap=mindmap.replace("\"","")
    return mindmap
    
def rewrite(question='',profile=''):
    rewrite_prompt= REWRITE_TEMPLATE.replace("{{query}}", question).replace("{{profile}}", profile)
    response=GPT_QA(rewrite_prompt, model_name="gpt-4o-mini", t=0.0)
    
    all_answer=''
    for answer in response:
        if answer:
            all_answer+=answer
        
    subquestion_list=[]
    for line in all_answer.split('\n'):
        line=line.strip()
        if line:
            subquestion_list.append(line)
    return subquestion_list

def generate_single_query(in_context_situation):
    SINGLE_QUERY_GENERATION.replace("{{in_context_situation}}", in_context_situation)
    response=GPT_QA_not_stream(SINGLE_QUERY_GENERATION, model_name="gpt-4o-mini", t=0.0)
    generated_query=response.split('```json')[1].split('```')[0].strip()
    generated_query=json.loads(generated_query)
    return generated_query['query']


def SpanPredict(adt='', article=''):
    SpanPredict_prompt= SPANPREDICT_TEMPLATE.replace("{{ADT}}", adt).replace("{{article}}", article)
    spanned_content=GPT_QA_not_stream(SpanPredict_prompt, model_name="gpt-4o-mini", t=0.0)
    spanned_content=spanned_content.split('Reformatted Article')[1].replace('```xml', '\n').replace('```', '\n').strip()
    return spanned_content
    
def answer_question(question="SQL的搜索语句怎么写？",historical_qa=None,external_knowledge_str=None,mindmap=None,user_material_str='',model='gpt-4o-mini'):
    assert model in ['gpt-4o-mini','Pro/deepseek-ai/DeepSeek-R1','Pro/THUDM/glm-4-9b-chat','Qwen/Qwen2.5-7B-Instruct']
    if external_knowledge_str is None:
        external_knowledge_base=search_snippets(question)
        #处理external_knowledge_base，将其拼成txt
        external_knowledge_str=""
        for index,knowledge_point in enumerate(external_knowledge_base):
            point=knowledge_point['point']
            summary=knowledge_point['summary']
            snippet=knowledge_point['snippet']
            knowledge_str=f"### Index {index+1}\n- Point\n{point}\n- Summary\n{summary}\n- Snippet\n{snippet}\n\n"
            external_knowledge_str+=knowledge_str
    else:
        pass


    if mindmap is None:
        QA_prompt= QA_RAG_TEMPLATE.replace("{{user_question}}", question).replace("{{external_knowledge_str}}", external_knowledge_str).replace("{{user_material_str}}", user_material_str)
    else:
        QA_prompt= QA_RAG_TEMPLATE_WITH_MINDMAP.replace("{{user_question}}", question).replace("{{external_knowledge_str}}", external_knowledge_str).replace("{{mindmap}}", mindmap).replace("{{user_material_str}}", user_material_str)
    historical_qa=[{
        'role': 'system',
        'content': QA_SYSTEM_normal
    }]+historical_qa
    


    #answer=GPT_QA(QA_prompt, model_name="gpt-4o-mini", t=0.0,historical_qa=historical_qa)
    # answer=GPT_QA_reasoning(QA_prompt, model_name="o3-mini-2025-01-31", t=0.0,historical_qa=historical_qa)
    #answer=SiliconFlow_QA(QA_prompt, model_name="Pro/deepseek-ai/DeepSeek-R1", t=0.6,historical_qa=historical_qa)
    #answer=ERK_QA(QA_prompt,model_name="deepseek-r1-250120", t=0.6, historical_qa=historical_qa)
    
    if model=='gpt-4o-mini':
        answer = GPT_QA(QA_prompt, "gpt-4o-mini", 0.2, historical_qa)
    else:
        answer = SiliconFlow_QA(QA_prompt, model, 0.2, historical_qa)
    return answer


def ColdRead(query=''):
    ColdRead_prompt= COLDREAD_TEMPLATE.replace("{{query}}", query)
    profile_content=GPT_QA_not_stream(ColdRead_prompt, model_name="gpt-4o-mini", t=0.2)
    return profile_content


def ADT_generation(question='', personality_traits=''):
    ADT_prompt= ADT_TEMPLATE.replace("{{query}}", question).replace("{{profile}}", personality_traits)
    adt=GPT_QA_not_stream(ADT_prompt, model_name="gpt-4o-mini", t=0.2)
    return adt

def Extract(article='',ADT=''):
    extract_prompt= EXTRACT_TEMPLATE.replace("{{article}}", article).replace("{{ADT}}", ADT)
    response=GPT_QA(extract_prompt, model_name="gpt-4o-mini", t=0.0)
    
    candidate_items_str=''
    for content in response:
        if content:
            candidate_items_str+=content

    candidate_items_str=candidate_items_str.split('```json')[1].split('```')[0].strip()
    candidate_items_list=json.loads(candidate_items_str)
    
    
    return candidate_items_list


def complete(candidate_item='',article='',ADT=''):
    candidate_item_str=json.dumps(candidate_item)
    complete_prompt= COMPLETE_TEMPLATE.replace("{{candidate_item}}", candidate_item_str).replace("{{article}}", article).replace("{{ADT}}", ADT)
    response=GPT_QA_not_stream(complete_prompt, model_name="gpt-4o-mini", t=0.0)
    completed_candidate=response.split('```json')[1].split('```')[0].strip()
    return completed_candidate


if __name__ == '__main__':
    user_question="SQL的搜索语句怎么写？"
    response=generate_mindmap(user_question,[])
    print(response)