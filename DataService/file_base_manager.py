from .models import get_session
import os
import json

class file_base_manager:
    """
    该类是有关文件生成与修改的管理器基类
    数据表管理器：控制sqlalchemy描述文件生成和修改
    api管理器：管理所有api并负责数据库api的生成和修改
    """
    def __init__(self):
        self.file_map = {}
        self.session = get_session()

    def scan_file(self, path):
        """
        获取文件中的类和函数
        :param path:
        :return:
        """
        if path[-2:] != 'py':
            raise ValueError('.py file required')
        line_id = 0
        current_handle = None
        file_info = {
            'classes': [],
            'methods': [],
        }
        with open(path, 'r', encoding='utf-8') as f:
            # 所有层级的类和方法都被统计到file_info中 所属关系在类中记录
            for line in f:
                line_id += 1
                current_obj = self._get_obj(line, path)
                if current_obj: # 起始行
                    current_obj.begin_at(line_id)
                    # 处理上下关系
                    if current_handle:
                        # 定义下的第一个二级方法
                        if current_handle.layer == current_obj.layer - 1:
                            current_obj.belong_to(current_handle)
                        # 后续同级定义
                        if current_handle.layer == current_obj.layer \
                            and current_handle.root():
                            current_obj.belong_to(current_handle.root())
                            current_handle.end_at(line_id - 1)
                        # 新的顶层定义
                        if current_handle.root().layer == current_obj.layer:
                            current_handle.end_at(line_id - 1, final=True)
                    current_handle = current_obj
                    file_info[current_obj.type_].append(current_obj)
                elif current_handle:
                    current_handle.add_content(line)
            current_handle.end_at(line_id, final=True)
        self.file_map[os.path.abspath(path)] = file_info
        return file_info

    def _get_obj(self, line, path):
        s = line.split(' ')
        if 'def' in s:
            return method_in_file(self._get_class_name(line), path, self._get_params(line), layer=self._get_layer(line))
        if 'class' in s:
            return class_in_file(self._get_class_name(line), path, self._get_parent(line), layer=self._get_layer(line))
        return None



    @staticmethod
    def _get_layer(line):
        pre = ''
        for i in line:
            if i.isalpha() or i == '_':
                break
            pre += i
        if len(pre) == 0 or pre[0] == '\t':
            return pre.count('\t')
        if pre[0] == ' ':
            return pre.count(' ') / 4
        raise ValueError('wrong input: {}'.format(line))

    @staticmethod
    def _get_class_name(line):
        return line.split('(')[0].split(':')[0].split(' ')[-1]

    @staticmethod
    def _get_parent(line):
        if '(' in line:
            return line.split(' ')[-1].split(':')[0].split('(')[-1].split(')')[0]
        return None

    @staticmethod
    def _get_params(line):
        params = line.split(' ')[-1].split(':')[0].split('(')[-1].split(')')[0].split(',')
        if params == '':
            return None
        for p in params:
            p.replace(' ', '')
        return params

    def file_info(self, path):
        return self.file_map[os.path.abspath(path)]

class file_scanner:
    def __init__(self, name, file_path=None, layer=0, belonging=None):
        self.name = name
        self.begin = None
        self.end = None
        self.file_path = os.path.abspath(file_path)
        self.file_name = os.path.split(self.file_path)[-1]
        self._content = ''
        self._content_list = []
        self.layer = layer
        self.inner_methods = [] # 子方法 对class是成员方法 对func是内部函数
        self.inner_classes = []
        self.belonging = belonging
        self.type_ = None

    def root(self):
        s = self
        while s.belonging:
            s = s.belonging
        return s

    def belong_to(self, class_or_methods):
        self.belonging = class_or_methods
        if self.type_ == 'classes':
            self.belonging.add_class(self)
        if self.type_ == 'methods':
            self.belonging.add_method(self)
        if not self.type_:
            raise TypeError('base class can not be used')

    def add_class(self, class_):
        self.inner_classes.append(class_)

    def begin_at(self, line_num):
        self.begin = line_num

    def end_at(self, line_num, final=False):
        self.end = line_num
        for i in range(1, len(self._content_list)):
            if self._content_list[-i] == '\n':
                self.end -= 1
            else:
                break
        if final:
            bl = self
            while bl.belonging:
                if not bl.belonging.end:
                    bl.belonging.end_at(self.end)
                    bl = bl.belonging

    def add_content(self, line):
        self._content += line
        self._content_list.append(line)

    def to_json(self):
        j = {}
        attrs = dir(self)
        for attr in attrs:
            if attr[:1] == '_':
                continue
            a = self.__getattribute__(attr)
            if a.__class__.__name__ == 'method':
                continue
            j[attr] = a.__str__()
        return json.dumps(j)

    def add_method(self, method):
        self.inner_methods.append(method)

class class_in_file(file_scanner):
    """
        用来表示文件中的一个类
    """

    def __init__(self, name, file_path=None, parent=None, layer=0, belonging=None):
        file_scanner.__init__(self, name, file_path, layer=layer, belonging=belonging)
        self.parent = parent
        self.type_ = 'classes'

class method_in_file(file_scanner):
    """
        用来表示文件中的一个方法
    """
    def __init__(self, name, file_path=None, params=None, layer=0, belonging=None):
        file_scanner.__init__(self, name, file_path, layer=layer, belonging=belonging)
        self.params = params
        self.type_ = 'methods'