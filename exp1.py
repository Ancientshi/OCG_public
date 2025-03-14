import json
from utils import *


json_file='AI_search_content/2025-03-03-15-33-03.json'
#读取
dict_data = json.load(open(json_file, 'r'))

question=dict_data.get('question','')
mindmap=dict_data.get('mindmap','')
ADT=dict_data.get('ADT','')
subquestion_list=dict_data.get('subquestion','')
for subquestion in subquestion_list.keys():
    AI_search_content=subquestion_list[subquestion]['AI_search_content']
    citations=subquestion_list[subquestion]['citations']

candidate_items_list_prepare=dict_data.get('candidate_items_list_prepare','')
candidate_items_list_AI_search_content=dict_data.get('candidate_items_list_AI_search_content','')
for candidate_name in candidate_items_list_AI_search_content.keys():
    candidate_dict=candidate_items_list_AI_search_content[candidate_name]
    for attribute in candidate_dict.keys():
        candidate_AI_search_content=candidate_dict[attribute]['AI_search_content']
        candidate_citations=candidate_dict[attribute]['citations']

candidate_items_list_final=dict_data.get('candidate_items_list_final','')
final_response=dict_data.get('final_response','')
final_response_reasoning=final_response.get('reasoning','')
final_response_content=final_response.get('content','')
 
print('final_response_reasoning:',final_response_reasoning)
print('final_response_content:',final_response_content)

#如果直接用
if __name__ == '__main__':
    pass