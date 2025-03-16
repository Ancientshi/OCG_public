import os
from utils import proj_path, proj_path_shn




prompt_folder_path=os.path.join(proj_path_shn, "prompt")

#读取下面的txt文件，变量名为文件名，文件内容为变量内容
for file_name in os.listdir(prompt_folder_path):
    if file_name.endswith('.txt'):
        with open(os.path.join(prompt_folder_path, file_name), 'r', encoding='utf-8') as f:
            globals()[file_name.split('.')[0]]=f.read()

