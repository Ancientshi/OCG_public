from ask import narative_recommendation
from rank import LLM_rank
from evaluate import HR
import json
import os

test_file='dataset/test.json'
with open(test_file, 'r') as f:
    test_data = json.load(f)

exp1_folder='exp_result/exp1'
# 读取result.json, 如果不存在则创建
if not os.path.exists(f'{exp1_folder}/result.json'):
    with open(f'{exp1_folder}/result.json', 'w') as f:
        json.dump({}, f)
with open(f'{exp1_folder}/result.json', 'r') as f:
    existing_result = json.load(f)
    
max=20
for index, test_case in enumerate(test_data):
    narrative_query=test_case['narrative query']
    result=test_case['result']
    all_label_rank_list=list(result.values())
    
    if narrative_query in existing_result:
        print(f"Test Case {index+1} already exists in result.json")
        continue
    
    OCG_list=narative_recommendation(narrative_query=narrative_query,model='gpt-4o-mini')
    LLM_rank_list=LLM_rank(OCG_list)
    
    hit_ratio_avg=0
    for label_rank_list in all_label_rank_list:
        hit_ratio = HR(label_rank_list, LLM_rank_list, k=10)
        hit_ratio_avg+=hit_ratio
    hit_ratio_avg/=len(all_label_rank_list)
    print(f"Test Case {index+1} Hit Ratio: {hit_ratio_avg}")
    
    existing_result[narrative_query]=hit_ratio_avg
    # 保存到result.json
    with open(f'{exp1_folder}/result.json', 'w') as f:
        json.dump(existing_result, f)

    if index+1==max:
        break