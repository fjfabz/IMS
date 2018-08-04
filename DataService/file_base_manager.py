from .models import get_session
from .models.sys import *
from .utils.utils import *
from alembic.config import Config
from alembic import command
import hashlib
import os, shutil
import json
from .utils.db_tools import all_tables

class file_scanner:
    def __init__(self, name, file_path=None, layer=0, belonging=None):
        self.name = name
        self.begin = None
        self.end = None
        self.file = os.path.abspath(file_path)
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


class table_manager(file_base_manager):

    def __init__(self, mod=None):
        file_base_manager.__init__(self)
        self.current_mod = mod
        self.mapping_filename = None

    def set_current_mod(self, mod):
        """
        设置当前模块管理器
        :param mod:
        :return:
        """
        self.current_mod = mod

    # -----register table--------
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
        self.create_table(table_info)

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
        self.mapping_filename = m.hexdigest()
        if not formating_check(self.mapping_filename):
            self.mapping_filename = '_' + self.mapping_filename

        with open('models/{}.py'.format(self.mapping_filename), 'a+') as f:
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
            init_s = 'from .{} import * # from module<{}>\n'.format(self.mapping_filename, self.current_mod.get('name'))
            f.write(init_s)
        # 数据库更新
        if update:
            self.update('module<{}> register table'.format(self.current_mod.get('name')))
        self.scan_file('models/{}.py'.format(self.mapping_filename)) # 重新扫描文件
        # 记录文件位置信息
        for table in table_info:
            t = self.session.query(Tables).filter_by(name=table['table_name']).first()
            for i in self.file_info('models/{}.py'.format(self.mapping_filename))['classes']:
                if i.name == table['table_name']:
                    t.file_pos = i.to_json()
        self.session.commit()

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
    #---------------------------

    def delete_table(self, table_name, update=True):
        """
        删除表
        :param table_name:
        :param update:
        :return:
        """
        t = self.session.query(Tables).filter_by(name=table_name).first()
        if not t:
            raise ValueError('{0} is not defined'.format(table_name))
        # 修改映射文件
        if not t.file_pos:
            raise ValueError('file_pos is None')
        pos_info = json.loads(t.file_pos)
        temp_file_name = '{0}\\{1}.temp'.format(os.path.dirname(pos_info['file']),
                                             pos_info['file'].split('\\')[-1].split('.')[0])
        temp_f = open(temp_file_name, 'w', encoding='utf-8')
        with open(pos_info['file'], 'r', encoding='utf-8') as r_f:
            line_id = 0
            for line in r_f:
                line_id += 1
                if int(pos_info['begin']) <= line_id <= int(pos_info['end']):
                    line = ''
                temp_f.write(line)
        temp_f.close()
        os.remove(pos_info['file'])
        os.renames(temp_file_name, temp_file_name.replace('.temp', '.py'))
        # 更新Table表Field表
        table_row = self.session.query(Tables).filter_by(name=table_name, owner_id=self.current_mod.get('id')).first()
        for field in table_row.fields:
            self.session.delete(field)
        self.session.delete(table_row)
        self.session.commit()
        # 数据库更新
        if update:
            self.update('delete table {0}'.format(table_name))
        self.scan_file(pos_info['file'])  # 重新扫描文件

    def update(self, msg):
        """
        更新数据库
        :param msg:
        :return:
        """
        # 绝对路径需要写入路径
        alembic_cfg = Config('C:\\Users\\93214\\Documents\\projects\\python_proj\\IMS\\DataService\\alembic.ini')
        command.revision(alembic_cfg, msg, autogenerate=True)
        command.upgrade(alembic_cfg, 'head')

    def _test_teardown(self, table_info):
        """
        测试失败时恢复环境
        :param table_info:
        :return:
        """
        # 删除__init__导入
        with open('models/__init__.py', 'r') as r_f:
            w_f = open('models/__init__.temp', 'w')
            for line in r_f:
                if self.gene_filename() in line:
                    line = ''
                w_f.write(line)
            w_f.close()
        os.remove('models/__init__.py')
        os.renames('models/__init__.temp', 'models/__init__.py')
        # 删除映射文件
        os.remove('models/{}.py'.format(self.gene_filename()))
        # 删除Table Field表
        for table in table_info:
            table_row = self.session.query(Tables).filter_by(name=table['table_name'], owner_id=self.current_mod.get('id')).first()
            for field in table_row.fields:
                self.session.delete(field)
            self.session.delete(table_row)
        self.session.commit()
        # 恢复alembic版本
        alembic_cfg = Config('alembic.ini')
        command.downgrade(alembic_cfg, '26b27c9afbf9')

    def gene_filename(self):
        m = hashlib.md5()
        m.update(self.current_mod.get('name').encode())
        mapping_filename = m.hexdigest()
        if not formating_check(mapping_filename):
            mapping_filename = '_' + mapping_filename
        return mapping_filename

