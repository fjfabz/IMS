from .file_base_manager import file_scanner
import importlib

class table_Context:
    """
    table上下文
    在处理表请求时用于传递表相关信息，特别是从/models中import的sqlalchemy module对象
    """
    def __init__(self, file_info:file_scanner, table_info=None):
        """
        :param file_info: file_scanner对象
        :param table_info: 注册表使用的table_info参数
        """
        self.file_info = file_info
        self.table_info = table_info
        # 导入模型类
        module = importlib.import_module('.models.{0}'.format(self.file_info.file_name.split('.')[0]), 'DataService')
        self.class_ = getattr(module, self.file_info.name)
