import requests
import io
from utils import proj_path
import os


def docling_read_file(file_path):
    #本地可以用http://0.0.0.0:6000/convert
    #外部可以用http://103.120.11.97:4747/file/convert
    url = "http://0.0.0.0:6000/convert"
    json_data = {"file_path": file_path}
    try:
        response = requests.post(url, json=json_data, timeout=60)  # 设置超时时间为60秒
        content = response.json().get("content", "no response")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Request error: {e}")  # 打印报错信息
        content = "request error"  # 设置content 为request error
    return content

if __name__ == "__main__":
    pass