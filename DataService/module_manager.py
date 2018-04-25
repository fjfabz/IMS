from .models import get_session
from .models.sys import *
import datetime
from functools import wraps
from flask import request, jsonify
from .errors import general_error
from .utils import *
import json, base64
import hashlib


"""
 TODO:
    - 根据模块请求建立私有表
    - 模块注册器
    - api注册器
    - super_pw支持
    - pubkey bytes转换
"""

class module_manager():

    def __init__(self, id=None):
        self.session = get_session()
        self.row = None
        self.pubkey = load_key()
        if id is not None:
            self.load_module(id)

    def register(self, module_info):
        """
        模块注册方法
        :param module_info:
        :return: 注册完成的行对象
        """
        # 重复模块校验
        name = module_info.get('name', None)
        self.row = self.session.query(module_reg).filter_by(name=name).first()
        if self.row is not None:
            raise ValueError('module with name<{}> is already registered'.format(self.row.name))
        # 公钥合法性校验
        pubkey = module_info.get('pubkey', None)
        if not pubkey_check(pubkey):
            raise ValueError('invalid pubkey')

        self.row = module_reg(name=module_info['name'], description=module_info['description'],
                              user_role=module_info['user_role'],pubkey=module_info['pubkey'],
                              auth=module_info.get('auth', 'anonymous'),
                              auth_email=module_info['auth_email'],
                              status=0, certification=module_info.get('certification', 1),
                              register_time=datetime.datetime.now(), permission=0)
        self.session.add(self.row)
        self.session.commit()
        return self.row

    def load_module(self, id):
        """
        加载模块
        :param id: 模块id
        :return: 行对象
        """
        self.row = self.session.query(module_reg).filter_by(id=id).first()
        if self.row is None:
            raise ValueError('Failed to load mod whit id={}'.format(id))
        return self.row

    def loaded(self):
        """
        是否加载模块
        :return:
        """
        if self.row is None:
            return False
        else:
            return True

    def get(self, field):
        """
        获取字段值
        :param field: 字段名
        :return: 字段值
        """
        if not self.loaded():
            raise AttributeError('Do not load any module')
        return getattr(self.row, field, None)

    def verify(self, sign):
        """
        签名验证
        :param sign:
        :return:
        """
        # self.pubkey = load_key()[0]
        return verify(pubkey_str(), sign, self.get('pubkey'))

    def create_table(self, table_info):
        """
        注册私有表
        :param table_info: [...
                {
                    table_name:
                    primary_key: []
                    fields: {
                        name: {
                            type:
                            length:
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
        # 文件生成
        # 语句模板
        tab = '    '
        import_template = 'from {package} import {statement}\n'
        class_template = 'class {table_name}(Base):\n'

        m = hashlib.md5()
        m.update(self.get('name').encode())
        filename = m.hexdigest()

        with open('models/{}.py'.format(filename), 'w+') as f:
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
            field = table['fields'][field_] # 获取field字典
            type =  field['type']
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
            print(field_name, table['primary_key'])
            print(field_name in table['primary_key'])
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


    @staticmethod
    def check_table_info(table_info):
        tables = []
        for table in table_info:
            # table name
            table_name = table.get('table_name', None)
            if table_name is None:
                raise ValueError('table_name is required')
            if table_name in tables:
                raise ValueError('table_name<{}> is repeat'.format(table_name))
            if not formating_check(table_name):
                raise ValueError('table_name<{}> is invalid'.format(table_name))
            tables.append(table_name)

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
                    raise ValueError('foreign table of field<{}> in table<{}> is not defined'.format(field, table))

                for t in table_info:
                    if t['table_name'] == foreign_key['table']:
                        if foreign_key['field'] not in t['fields']:
                            raise ValueError(
                                'foreign key of field<{}> in table<{}> is not defined'.format(field, table))



def signature_verify(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            id = int(request.args.get('module_id', None))
            sign = base64.b64decode(request.args.get('signature', None)) # sign通过base64编码上传
            if id is None:
                return general_error('400', 'module_id is required')
            if sign is None:
                return general_error('400', 'signature is required')
            mod = module_manager(id)  # 实例化module_manager
        except ValueError:
            return general_error('400', 'module_id invalid')

        v = mod.verify(sign) # type(sign) == bytes
        if not v:
            return general_error('403', request.args.get('signature', None), pubkey=mod.get('pubkey'))
        return func(*args, **kwargs)
    return wrapper




'''

:param
[{
            table: 'table_a',
            primary: {
                
            }
            fields: {
                'a': 'Colunm(String(128))',
                'b': 'relationship('table_b', backref='table_a')'
        }

        },
        {
            table: 'xx',
            associative: True,
            define: 'Table(
                "teacher_classes",
                Base.metadata,
                Column("teacher_id", Integer, ForeignKey("teacher.id"), nullable=False, primary_key=True),
                Column("classes_id", Integer, ForeignKey("classes.id"), nullable=False, primary_key=True)'
        )'
        }]
:return:

filed_template = '{filed} = {declaration}'
import_template = 'from {} import '
with open('/models/{}.py'.format(self.row.name), 'w+') as f:
    f.write()
'''
