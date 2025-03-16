from rec import *
  
def narative_recommendation(narrative_query='',model=''):
    data={
        'question':narrative_query,
        'model':model
    }
    try:
        for chunk in generate_response_rec(data):
            print(chunk)
    except Exception as e:
        print(e)
        #记录一下data，存到/Users/j4-ai/workspace/OCG/AI_search_content/error.jsonl中
        with open('/Users/j4-ai/workspace/OCG/AI_search_content/error.jsonl','a') as f:
            f.write(json.dumps(data)+'\n')
        return []
    # for chunk in generate_response_rec_with_checkpoint(data,'/Users/j4-ai/workspace/OCG/AI_search_content/2025-03-16-02-58-10.json'):
    #         print(chunk)
        
    #最后一个chunk是candidate_items_list
    if isinstance(chunk, list):
        return chunk
    
if __name__ == '__main__':
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