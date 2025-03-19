import json


file1='output1.json'
file2='output2.json'
with open(file1, 'r') as f:
    data1 = json.load(f)
with open(file2, 'r') as f:
    data2 = json.load(f)
    
data=data1+data2

for one_data in data:
    merged_result = {}
    result = one_data['result']
    
    # 记录item的首次出现的comment索引
    item_order = {}
    
    for comment_index, (comment, items) in enumerate(result.items()):
        for item in items:
            if item in merged_result:
                merged_result[item] += 1
            else:
                merged_result[item] = 1
                item_order[item] = comment_index  # 记录首次出现的comment顺序
    
    # 先按出现次数排序，再按首次出现的comment顺序排序
    merged_result = sorted(merged_result.items(), key=lambda x: (-x[1], item_order[x[0]]))
    
    # 只保留名字
    one_data['merged_result'] = [item[0] for item in merged_result]
         
with open('output.json', 'w') as f:
    json.dump(data, f)