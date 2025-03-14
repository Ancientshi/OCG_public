from rec import *


question_list=['I want to watch a thriller with a mind-bending story, like Shutter Island.',
'我想要去蓝山的酒店推荐  价格200刀一晚以内  我还要行程安排推荐',
'推荐悉尼看动物的地方',
'推荐悉尼海滩',
'推荐悉尼看银河的地方']

for question in question_list[:1]:
    for model in ['gpt-4o-mini','Pro/deepseek-ai/DeepSeek-R1','Pro/THUDM/glm-4-9b-chat','Qwen/Qwen2.5-7B-Instruct'][:1]:
        data={
            'question':question,
            'model':model
        }

        for chunk in generate_response_rec(data):
            print(chunk)