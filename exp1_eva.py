
from ask import narative_recommendation
from rank import LLM_rank
from evaluate import HR
import json
import os
from copy import deepcopy

handled_data = {}
# 读取目录下的所有 JSON 文件
directory = '/Users/j4-ai/workspace/OCG/AI_search_content'

for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('.json'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 确保数据是字典类型
                    if isinstance(data, dict):
                        question = data.get("question")
                        candidate_items = data.get("candidate_items_list_final")
                        profile = data.get("profile")

                        # 确保 question 存在，candidate_items_list_final 不为空
                        if question and isinstance(candidate_items, list) and candidate_items:
                            handled_data[question] = {
                                "candidate_items_list_final": candidate_items,
                                "profile": profile
                            }

            except (json.JSONDecodeError, OSError) as e:
                print(f"Error processing {file_path}: {e}")
            
                        


def all_result_eva():
    updated_test_data = []
    
    dataset_name='movie'
    test_file=f'dataset/{dataset_name}.json'
    with open(test_file, 'r') as f:
        test_data = json.load(f)

    for index, test_case in enumerate(test_data):
        narrative_query=test_case['narrative query']
        result=test_case['result']
        merged_result=test_case['merged_result']
        
        OCG_list=handled_data[narrative_query]['candidate_items_list_final']
        profile=handled_data[narrative_query]['profile']
        new_case=deepcopy(test_case)
        new_case['OCG_list']=OCG_list
        new_case['profile']=profile
        updated_test_data.append(new_case)
    
    #存一下f'dataset/new_{dataset_name}.json'
    with open(f'dataset/new_{dataset_name}.json', 'w') as f:
        json.dump(updated_test_data, f, indent=4)

if __name__ == '__main__':
    all_result_eva()
        