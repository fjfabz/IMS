from typing import Callable, List
from flask import Flask

from . import postprocessors_dict, preprocessors_dict
from .file_base_manager import file_base_manager

class api_manager(file_base_manager):
    def __init__(self, app: Flask):
        file_base_manager.__init__(self)
        self.app = app
        self.api = [] # type: List(API)
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.api_manager = self
        for rule in self.app.url_map._rules:
            if rule.rule.startswith(self.app.service_config['query_prefix']):
                api = query_api(rule, self)
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
        self.config = self.manager.app.service_config

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
    def __init__(self, rule, manager:api_manager, params: List[str]=None,
                 status: int=0, sensitivity: int=0,
                 url_prefix: str=None, preprocessors: List[Callable]=None,
                 postprocessors: List[Callable]=None, allow_patch_many:bool=True):
        API.__init__(self, rule, manager, params=params, status=status, sensitivity=sensitivity)
        self.url_prefix = url_prefix
        self.preprocessors = preprocessors if preprocessors else preprocessors_dict
        self.postprocessors = postprocessors if postprocessors else postprocessors_dict
        self.allow_patch_many = allow_patch_many


    def dump(self):
        """

        :return:
        """






