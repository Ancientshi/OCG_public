import os
from utils import proj_path


prompt_folder_path=os.path.join(proj_path, "prompt")
#读取下面的txt文件，变量名为文件名，文件内容为变量内容
for file_name in os.listdir(prompt_folder_path):
    if file_name.endswith('.txt'):
        with open(os.path.join(prompt_folder_path, file_name), 'r') as f:
            globals()[file_name.split('.')[0]]=f.read()

