import json


file1='output1.json'
file2='output2.json'
with open(file1, 'r') as f:
    data1 = json.load(f)
with open(file2, 'r') as f:
    data2 = json.load(f)
    
data=data1+data2
with open('output.json', 'w') as f:
    json.dump(data, f)