def LLM_rank(OCG_list):
    rank_list=[]
    for candidate in OCG_list:
        rank_list.append(candidate['Name'])
    return rank_list