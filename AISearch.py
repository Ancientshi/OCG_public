from openai import OpenAI
from utils import GPT_QA_not_stream, filter_content_bm25
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent
import time
from file_database import docling_read_file

class SerperSearch:
    #65efc04c3887eb81a0fd6e2d79f41c206c7f0682
    def __init__(self,key="9252e59ef78c7d2be2c8885a0884417329b86399"):
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
    return external_knowledge_dict,citation_list
    
def AI_search(api_key="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", base_url="https://api.perplexity.ai", model="sonar", system_message="You need to help to solve user\'s information search question.", user_message=""):
    """
    Interact with OpenAI's chat completion API.

    Parameters:
        api_key (str): Your OpenAI API key.
        base_url (str): The base URL for the OpenAI API.
        model (str): The model to use for chat completions.
        system_message (str): The system's instruction or context for the assistant.
        user_message (str): The user's input message.
        stream (bool): Whether to stream the response or not. Default is False.

    Returns:
        If stream=False: str, the full response content.
        If stream=True: tuple, the concatenated content and a set of citations.
    """
    # Initialize the client
    client = OpenAI(api_key=api_key, base_url=base_url)

    # Prepare the messages
    messages = [
        {
            "role": "system",
            "content": system_message,
        }
    ]+user_message

    # if not stream:
    #     # Chat completion without streaming
    #     response = client.chat.completions.create(
    #         model=model,
    #         messages=messages,
    #     )
    #     response_dict = response.to_dict()
    #     return response_dict["choices"][0]["message"]["content"], response_dict.get("citations", [])

    # else:
    
    # Chat completion with streaming
    response_stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
    
    for response in response_stream:
        response_dict = response.to_dict()
        citations = response_dict.get("citations", [])
        content = response_dict["choices"][0]["delta"]["content"]
        yield content, citations


# Example usage:
if __name__ == "__main__":
    # YOUR_API_KEY = "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"
    # BASE_URL = "https://api.perplexity.ai"
    # MODEL = "sonar"
    # SYSTEM_MESSAGE = (
    #     "You are an artificial intelligence assistant and you need to "
    #     "engage in a helpful, detailed, polite conversation with a user."
    # )
    # USER_MESSAGE = "UTS IT专业怎么样?"

    # # Call without streaming
    # response_content = AI_search(
    #     api_key=YOUR_API_KEY,
    #     base_url=BASE_URL,
    #     model=MODEL,
    #     system_message=SYSTEM_MESSAGE,
    #     user_message=USER_MESSAGE,
    #     stream=False,
    # )
    # print("\nResponse without streaming:")
    # print(response_content)

    # # Call with streaming
    # print("\nResponse with streaming:")
    # response_content, citations = chat_with_openai(
    #     api_key=YOUR_API_KEY,
    #     base_url=BASE_URL,
    #     model=MODEL,
    #     system_message=SYSTEM_MESSAGE,
    #     user_message=USER_MESSAGE,
    #     stream=True,
    # )
    # print("\nCitations:", citations)
    
    
    generated_query, search_content=self_AI_search(
        '''
        User ask for: 我在悉尼科技大学读大一 读的IT专业 我希望你能给我学校的选课推荐 专注在AI方面。 难度从低到高，最好帮我考虑一下学校选课的依赖关系。
        Find a candidate item:
            {
                "Name": "Deep Learning and Convolutional Neural Network",
                "Difficulty Level": "NOT FOUND",
                "Prerequisites": "NOT FOUND",
                "Credits": "NOT FOUND",
                "Focus Area": "深度学习与卷积神经网络",
                "Semester Offered": "NOT FOUND"
            }
        Want to find related information about Difficulty Level.
        '''
    )
