from typing import Callable, List
from flask import Flask, current_app
from mako.template import Template
import json

from . import postprocessors_dict, preprocessors_dict
from .file_base_manager import file_base_manager, file_scanner, class_in_file
from .models import get_session, Tables
from .table_manager import table_Context

predefine_params = ['methods', 'url_prefix', 'allow_patch_many']

class api_info:
    def __init__(self, model_name, file_info: file_scanner, methods=None, url_prefix='/query', allow_patch_many=True, **kwargs):
        self.module_name = model_name
        self.table_context_ = table_Context(file_info)
        self.module = self.table_context_.class_
        self.methods = methods if  methods else ['GET', 'POST', 'PATCH', 'DELETE']
        self.url_prefix = url_prefix
        self.allow_patch_many = allow_patch_many
        for key in kwargs:
            self.__setattr__(key, kwargs[key])

    def loads(self, info):
        """
        加载json配置
        :param info:
        :return:
        """
        info = json.loads(info)
        for attr in self.__dir__():
            try:
                self.__setattr__(attr, info[attr])
            except KeyError:
                continue

    def to_json(self):
        j = {}
        attrs = self.__dir__()
        for attr in attrs:
            if attr[:1] == '_' or attr[-1:] == '_':
                continue
            j[attr] = self.__getattribute__(attr)
        return json.dumps(j)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, item):
        self.__getattribute__(item)


class api_manager(file_base_manager):
    def __init__(self, app: Flask):
        file_base_manager.__init__(self)
        self.app = app
        self.api = [] # type: List(API)
        self.query_api = [] # type: List(query_api)
        if app:
            self.api_config = app.service_config['api']
            self.init_app(app)

    @staticmethod
    def init_api_from_db(restless_manager):
        """
        根据Tables数据初始化query_api
        """
        session = get_session()
        tables = session.query(Tables).all()
        for table in tables:
            if table.file_pos is None:
                continue
            file_pos = json.loads(table.file_pos)
            cl = class_in_file(file_pos['name'])
            cl.load_from_json(file_pos)
            info = api_info(cl.name, cl)
            api_manager.load_api(restless_manager, info)

    @staticmethod
    def load_api(restless_manager, info: api_info):
        restless_manager.create_api(
            info.table_context_.class_,
            methods=info.methods,
            url_prefix=info.url_prefix,
            preprocessors=preprocessors_dict,
            postprocessors=postprocessors_dict,
            allow_patch_many=info.allow_patch_many
        )

    def init_app(self, app):
        app.api_manager = self
        for rule in self.app.url_map._rules:
            if rule.rule.startswith(self.api_config['query_prefix']):
                api = query_api(rule, self, rule.rule.split('/')[2],
                                url_prefix=self.api_config['query_prefix'])
                self.query_api.append(api)
            else:
                api = API(rule, self)
            self.api.append(api)

    def close_api(self, api_path):
        for api in self.api:
            if api_path == api.rule.rule:
                api.close()

    def open_api(self, api_path):
        for api in self.api:
            if api_path == api.rule.rule:
                api.open()

    def register_query_api(self):
        for table in current_app.table_context: # table: table_Context
            self.app.restless_manager.create_api(
                table.module,
                methods=['GET', 'PATCH', 'DELETE'],
                url_prefix='/query',
                preprocessors=preprocessors_dict,
                postprocessors=postprocessors_dict,
                allow_patch_many=True
            )

class API:
    """
    描述一个API接口
    封装了相关接口实现代码的信息，通过该类对单个API进行管理
    """
    def __init__(self, rule, manager, params=None, status=0, sensitivity=0):
        self.rule = rule
        self.manager = manager
        self.params = params if params else []
        self._status = status
        self.sensitivity = sensitivity
        self.config = manager.api_config

    def update(self):
        pass

    def status(self):
        return 'running' if self._status == 1 else 'closing'

    def open(self):
        for rule in self.config['intercept_urls']:
            if rule == self.rule.rule:
                self.config['intercept_urls'].remove(rule)
                self.config.update()

    def close(self):
        if self.rule.rule not in self.config['intercept_urls']:
            self.config['intercept_urls'].append(self.rule.rule)
            self.config.update()


class query_api(API):
    """
    数据库接口api
    """
    def __init__(self, rule, manager:api_manager, module, params: List[str]=None,
                 status: int=0, sensitivity: int=0,
                 url_prefix: str=None, preprocessors: List[Callable]=None,
                 postprocessors: List[Callable]=None, allow_patch_many:bool=True):
        API.__init__(self, rule, manager, params=params, status=status, sensitivity=sensitivity)
        self.module_name = module
        self.url_prefix = url_prefix
        self.preprocessors = preprocessors if preprocessors else preprocessors_dict
        self.postprocessors = postprocessors if postprocessors else postprocessors_dict
        self.allow_patch_many = allow_patch_many
        self.predefine_params = ['methods', 'url_prefix', 'allow_patch_many']

    def api_info(self):
        """
        生成文件写入相关信息
        注意：属性需要是可以调用__repr__得到需要的字符串
        :return:
        apis = [
            ...
            {
                predefine_params:,
                model_name:,
                ...
                param:
                ...
            }
        ]
        """
        api_info = {
            'module_name': self.module_name,
            'predefine_params': self.predefine_params
        }
        for param in self.predefine_params:
            api_info[param] = self.__getattribute__(param).__repr__()
        return api_info






