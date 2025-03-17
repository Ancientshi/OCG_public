from openai import OpenAI
from utils import GPT_QA_not_stream, filter_content_bm25, content_post_process
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent
import time
from file_database import docling_read_file
from config import SerperSearch_key

class SerperSearch:
    #65efc04c3887eb81a0fd6e2d79f41c206c7f0682
    def __init__(self,key=SerperSearch_key):
        self.api_key=key
        self.url = "https://google.serper.dev/search"
        self.max_chars=100000
    
    def searchserper(self,query,pagenum):
        payload = json.dumps({
            "q": query
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
            
        # Call the API
        retry_interval_exp = 0
        while True:
            try:
                response = requests.request("POST", self.url, headers=headers, data=payload)
                response.raise_for_status()
                return response.json()
            except Exception as ex:
                if retry_interval_exp > 3:
                    return {}
                time.sleep(max(2, 0.5 * (2 ** retry_interval_exp)))
                retry_interval_exp += 1
    
    def search(self, query, pagenum,threshold=1.0,existed_citation_list=[]):
        external_knowledge = {}
        search_results = self.searchserper(query,pagenum)
        
        def process_result(result):
            title = result["title"]
            if 'link' in result.keys():
                url=result['link']
                if url in existed_citation_list:
                    return None
            else:
                return None    
            
            #page_content = extract_page(url, True, True)
            page_content = docling_read_file(url)
            if page_content != 'Not available':
                content_length = len(page_content)
                max_chars = min(self.max_chars, content_length)
                page_content = page_content[:max_chars]
                try:
                    page_content=filter_content_bm25(page_content, query, threshold=threshold,maxlength = 10000)
                except:
                    pass
                formatted_title = title + ':' + url
                return formatted_title, page_content
            return None

        citation_list=[]
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_result, result) for result in search_results['organic'][:pagenum]]
            index=1
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    formatted_title, page_content=result
                    _title, _url = formatted_title.split(':http')
                    citation_list.append('http'+_url)
                    external_knowledge.update({f'{_title}[{index}]': page_content})
        return external_knowledge, citation_list

bingsearch_tool=SerperSearch()


def self_AI_search(query="",pagenum=1,threshold=1.5,existed_citation_list=[]):
    external_knowledge_dict,citation_list=bingsearch_tool.search(query, pagenum,threshold,existed_citation_list)
    #shn: 处理检索杂质
    # 对每个返回的 content 进行后处理
    for key in external_knowledge_dict:
        external_knowledge_dict[key] = content_post_process(external_knowledge_dict[key])
    # content = content_post_process(content)  # 对 content 进行后处理
    return external_knowledge_dict,citation_list
    


# Example usage:
if __name__ == "__main__":
    pass