import string

def match(name1, name2):
    """
    计算 Jaccard 相似度，判断两个名字是否匹配
    """
    set_name1 = set(name1.split())
    set_name1 = set([word.strip(string.punctuation) for word in set_name1])

    set_name2 = set(name2.split())
    set_name2 = set([word.strip(string.punctuation) for word in set_name2])

    intersection = set_name1.intersection(set_name2)
    union = set_name1.union(set_name2)
    
    Jaccard = len(intersection) / len(union) if union else 0  # 避免除 0
    return Jaccard >= 0.6  # 设定阈值 0.6

def HR(label_rank_list, predict_rank_list, k):
    """
    计算推荐系统的 Hit Rate
    :param label_rank_list: 真实相关物品列表
    :param predict_rank_list: 预测推荐的物品列表
    :param k: 取 top-k 进行计算
    :return: 命中率 (Hit Rate)
    """
    hit_count = 0
    k=min(k,len(predict_rank_list))

    # 遍历 label_rank_list，看是否有出现在 predict_rank_list 的 top-k
    for label in label_rank_list:
        for predict in predict_rank_list[:k]:  # 只考虑前 k 个
            if match(label, predict):
                hit_count += 1
                break  # 一个 label 只需要匹配一次，跳出当前循环
    
    # 返回命中率
    hit_ratio=hit_count / len(label_rank_list) if len(label_rank_list) else 0
    return hit_ratio
