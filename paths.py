import sys
import os
def get_base_dir():
    if getattr(sys, 'frozen', False):
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(appdata, 'ScanProgramm')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    else:
        return os.path.dirname(os.path.abspath(__file__))
BASE_DIR = get_base_dir()
os.chdir(BASE_DIR)
print(f'[PATHS] BASE_DIR: {BASE_DIR}')
print(f'[PATHS] os.getcwd(): {os.getcwd()}')
