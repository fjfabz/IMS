import sys
import os
import json

class Config:
    def __init__(self, config_path='conf.json'):
        self.config_path = self._relative_to_abs(config_path)
        # print(path)
        with open(self.config_path, 'r') as f:
            self.config = json.load(f) # 此处不处理IOError


    @staticmethod
    def _relative_to_abs(path):
        filename = sys._getframe(2).f_code.co_filename # 保护方法，外界调用源栈中索引为2
        file_dir = os.path.split(os.path.abspath(filename))[0]  # 实现相对目录导入
        if path[0] != '/' or '\\':  # 处理同目录文件的情况
            path = os.sep + path.replace('/', '\\')
        path = file_dir + path
        return path

    def __getitem__(self, item):
        return self.config[item]

    def __setitem__(self, key, value):
        self.config[key] = value

    def update(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)