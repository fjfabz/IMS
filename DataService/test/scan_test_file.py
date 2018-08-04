from ..models import get_session
from ..models.sys import *
from ..utils.utils import *
from alembic.config import Config
from alembic import command
import hashlib
import os, shutil
import json

class layer_0_class:
    def __init__(self, name, file_path=None, layer=0):
        self.name = name
        self.begin = None
        self.end = None
        self.file = os.path.abspath(file_path)
        self._content = ''
        self._content_list = []
        self.layer = layer

    def begin_at(self, line_num):
        pass

    def end_at(self, line_num):
        pass

    def add_content(self, line):
        pass

    def to_json(self):
        pass

    class layer_1_class:
        pass

class multilayer_class(layer_0_class):
    """
        用来表示文件中的一个方法
    """
    def __init__(self, name, file_path=None, params=None, belonging=None, layer=0):
        layer_0_class.__init__(self, name, file_path, layer=layer)
        self.params = params
        self.belonging = belonging
        def layer_2_func():
            pass

def layer_0_func(arg1, arg2):
    def layer_1_func():
        pass