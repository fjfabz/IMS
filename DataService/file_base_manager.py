from .models import get_session
from .models import get_session
from .models.sys import *
import datetime
from functools import wraps
from flask import request, jsonify
from .errors import general_error
from .utils.utils import *
import base64
import hashlib
from alembic.config import Config
from alembic import command

class file_scanner:
    def __init__(self, name, file_path=None):
        self.name = name
        self.begin = None
        self.end = None
        self.file = file_path
        self.content = ''
        self.content_list = []

    def begin_at(self, line_num):
        self.begin = line_num

    def end_at(self, line_num):
        self.end = line_num
        for i in range(1, len(self.content_list)):
            if self.content_list[-i] == '\n':
                self.end -= 1
            else:
                break


    def add_content(self, line):
        self.content += line
        self.content_list.append(line)

class class_in_file(file_scanner):
    """
        用来表示文件中的一个类
    """
    def __init__(self, name, file_path=None, parent=None):
        file_scanner.__init__(self, name, file_path)
        self.parent = parent

class method_in_file(file_scanner):
    """
        用来表示文件中的一个类
    """
    def __init__(self, name, file_path=None, params=None):
        file_scanner.__init__(self, name, file_path)
        self.params = params

class file_base_manager:
    """
    该类是有关文件生成与修改的管理器基类
    数据表管理器：控制sqlalchemy描述文件生成和修改
    api管理器：管理所有api并负责数据库api的生成和修改
    """
    def __init__(self):
        self.file_info = {
            'classes': [],
            'methods': [],
        }
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
        with open(path, 'r', encoding='utf-8') as f:
            while True:
                line = f.readline()
                if line == '':
                    if current_handle:
                        self.file_info[current_handle][-1].end_at(line_id)
                    break
                line_id += 1
                if line[:5] == 'class' or line[:3] == 'def':
                    # 处理上一段
                    if current_handle:
                        self.file_info[current_handle][-1].end_at(line_id - 1)
                    # 加入下一段
                    if line[:5] == 'class':
                        current_handle = 'classes'
                        class_ = class_in_file(self._get_class_name(line), path, self._get_parent(line))
                        class_.begin_at(line_id)
                        self.file_info['classes'].append(class_)
                    if line[:3] == 'def':
                        current_handle = 'methods'
                        method = method_in_file(self._get_class_name(line), path, self._get_params(line))
                        method.begin_at(line_id)
                        self.file_info['methods'].append(method)
                if current_handle:
                    self.file_info[current_handle][-1].add_content(line)

    @staticmethod
    def _get_class_name(line):
        return line.split(' ')[-1].split(':')[0].split('(')[0]

    @staticmethod
    def _get_parent(line):
        if '(' in line:
            return line.split(' ')[-1].split(':')[0].split('(')[-1].split(')')[0]
        return None

    @staticmethod
    def _get_params(line):
        params = line.split(' ')[-1].split(':')[0].split('(')[-1].split(')')[0].split(',')
        for p in params:
            p.replace(' ', '')
        return params

class table_manager(file_base_manager):

    def __init__(self, mod=None):
        file_base_manager.__init__(self)
        self.current_mod = mod

    def set_current_mod(self, mod):
        """
        设置当前模块管理器
        :param mod:
        :return:
        """
        self.current_mod = mod

    def check_table_info(self, table_info):
        """
        检查表信息正确性
        :param table_info:
        :return:
        """
        tables = []
        for table in table_info:
            # table name
            table_name = table.get('table_name', None)
            if table_name is None:
                raise ValueError('table_name is required')
            table['table_name'] = table_name.lower() # 表名统一小写
            # 表名查重
            if len(self.session.query(Tables).filter_by(name=table_name).all()):
                # 有同名表
                raise ValueError('table<{}> is existed'.format(table_name))
            if table_name in tables:
                # print(tables)
                raise ValueError('table_name<{}> is repeat'.format(table_name))
            if not formating_check(table_name):
                raise ValueError('table_name<{}> is invalid'.format(table_name))
            tables.append(table_name)
            # sensitivity
            try:
                int(table.get('sensitivity', 0))
            except ValueError:
                raise ValueError('sensitivity of table<{}> is invalid'.format(table_name))

        for table in table_info:
            table_name = table.get('table_name', None)
            primary_keys = table.get('primary_key', None)
            fields = table.get('fields', None)
            # primary key
            if primary_keys is None or len(primary_keys) == 0:
                raise ValueError('primary key of table<{}> is required', format(table_name))
            if fields is None:
                raise ValueError('fields of table<{}> is required', format(table_name))
            for primary_key in primary_keys:
                if primary_key not in fields:
                    raise ValueError('primary key<{}> is not defined'.format(primary_key))
            # fields
            # 该type列表支持python 其他语言支持后续添加
            types = ['Integer', 'String', 'Text', 'Boolean', 'PickleType',
                     'Date', 'Time', 'Unicode', 'BigInteger', 'Interval']
            for field in fields:
                if not formating_check(field):
                    raise ValueError('field name<{}> in table<{}> is invalid'.format(field, table_name))
                try:
                    int(fields[field].get('sensitivity', 0))
                except ValueError:
                    raise ValueError('sensitivity of field<{}> in table<{}> is invalid'.format(field, table_name))
                # type
                type = fields[field].get('type', None)
                if type is None:
                    raise ValueError('type of field<{}> is required', format(field))
                if type not in types:
                    raise ValueError('type<{}> of field<{}> in table<{}> is invalid'.format(type, field, table))
                # length
                length = fields[field].get('length', 256)
                if int(length) > 256:
                    raise ValueError('length of field<{}> in table<{}> is larger than 256.'.format(field, table))
                # foreignkey
                foreign_key = fields[field].get('foreignkey', None)
                if foreign_key is None:
                    continue
                if 'table' not in foreign_key and 'field' not in foreign_key:
                    continue
                if 'table' not in foreign_key and 'field' in foreign_key:
                    raise ValueError('foreign key of field<{}> in table<{}> requires param table'.format(field, table))
                if 'table' in foreign_key and 'field' not in foreign_key:
                    raise ValueError('foreign key of field<{}> in table<{}> requires param field'.format(field, table))

                if foreign_key['table'] not in tables:
                    print(foreign_key['table'])
                    raise ValueError('foreign table of field<{}> in table<{}> is not defined'.format(field, table['table_name']))

                for t in table_info:
                    if t['table_name'] == foreign_key['table']:
                        if foreign_key['field'] not in t['fields']:
                            raise ValueError(
                                'foreign key of field<{}> in table<{}> is not defined'.format(field, table))



    def register_table(self, table_info):
        """
        注册私有表
        note: 注册后表进入待审核状态
        :param table_info: [...
                {
                    table_name:
                    sensitivity:
                    primary_key: []
                    description:
                    note:
                    fields: {
                        name: {
                            type:
                            length:
                            sensitivity： # 敏感度
                            description:
                            note:
                            nullable:
                            unique:
                            default: # 待支持
                            foreignkey:{
                                table:,
                                field:
                            }
                        }
                    }
                }
        :return:
        """
        # 合法性校验
        self.check_table_info(table_info)
        for table in table_info:
            sensitivity = int(table.get('sensitivity', 0))
            table_row = Tables(name=table['table_name'], owner_id=self.current_mod.get('id'), status=0, sensitivity=sensitivity)
            self.session.add(table_row)
            self.session.commit() # 获取id
            for field in table['fields']:
                f_sensitivity = int(table['fields'][field].get('sensitivity', 0))
                field_row = Fields(name=field, table_id=table_row.id, sensitivity=f_sensitivity)
                self.session.add(field_row)
            try:
                self.session.commit()
            except:
                self.session.rollback()

    def create_table(self, table_info, update=True):
        """
        生成私有表
        TODO：
            - 文件可用性测试
            - __init__重复导入校验
            - 表属性记录
            - default参数
            - 注释
        :param update: 是否更新数据库
        :param table_info:
        :return:
        """
        # 文件生成
        # 语句模板
        tab = '    '
        import_template = 'from {package} import {statement}\n'
        class_template = 'class {table_name}(Base):\n'
        # 文件名hash
        m = hashlib.md5()
        m.update(self.current_mod.get('name').encode())
        filename = m.hexdigest()
        if not formating_check(filename):
            filename = '_' + filename

        with open('models/{}.py'.format(filename), 'a+') as f:
            # import
            f.write(import_template.format(package='.', statement='Base'))
            f.write(import_template.format(package='sqlalchemy.types',
                                           statement='Integer, String, Text, Boolean, PickleType, Date, Time, Unicode, BigInteger, Interval'))
                                            # 导入了所有常用类型以便直接添加表
            f.write(import_template.format(package='sqlalchemy', statement='Column, ForeignKey'))
            f.write('\n')
            for table in table_info:
                f.write(class_template.format(table_name=table['table_name']))
                f.write(tab + "__tablename__ = '{}'\n\n".format(table['table_name']))
                columns = self.render_column(table)
                for column in columns:
                    f.write(tab + column + '\n')
                f.write('\n')

        with open('models/__init__.py', 'a+') as f:
            init_s = 'from .{} import * # from module<{}>\n'.format(filename, self.get('name'))
            f.write(init_s)
        # 数据库更新
        if update:
            alembic_cfg = Config('alembic.ini')
            command.revision(alembic_cfg, 'module<{}> register table'.format(self.get('name')),
                             autogenerate=True)
            command.upgrade(alembic_cfg, 'head')

    @staticmethod
    def render_column(table):
        """
        渲染列语句
        :param table:
        :return:
        """
        columns = []
        column_template = '{field} = Column({type}{params})'
        for field_ in table['fields']:
            param_s = ''
            # 生成type参数
            field_name = field_
            field = table['fields'][field_]  # 获取field字典
            type = field['type']
            if type == 'String':
                length = field.get('length', '256')
            else:
                length = ''
            if length != '':
                length = '({})'.format(length)

            type_s = '{name}{length}'.format(name=type, length=length)
            # foreign key
            foreignkey = field.get('foreignkey', None)
            if foreignkey is not None:
                param_s += ", ForeignKey('{table}.{field}')".format(table=foreignkey['table'],
                                                                    field=foreignkey['field'])
            # primary key
            if field_name in table['primary_key']:
                param_s += ', primary_key=True'
            # 生成其他参数 对default参数支持待开发
            nullable = field.get('nullable', True)
            unique = field.get('unique', False)

            if not nullable:
                param_s += ', nullable=False'
            if unique:
                param_s += ', unique=True'

            # 生成语句
            column_s = column_template.format(field=field_name, type=type_s, params=param_s)
            columns.append(column_s)
        return columns
