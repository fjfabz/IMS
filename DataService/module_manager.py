from .models import get_session
from .models.sys import *
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from .errors import general_error
from .utils.utils import *
import base64
import rsa

"""
 TODO:
    - 根据模块请求建立私有表
    - 模块注册器
    - api注册器
    - super_pw支持
    - pubkey bytes转换
"""

class module_manager:

    def __init__(self, id=None):
        self.session = get_session()
        self.row = None
        self.pubkey = None
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
        self.row = self.session.query(ModuleReg).filter_by(name=name).first()
        if self.row is not None:
            raise ValueError('module with name<{}> is already registered'.format(self.row.name))
        # 公钥合法性校验
        pubkey = module_info.get('pubkey', None)
        if not pubkey_check(pubkey):
            raise ValueError('invalid pubkey')

        self.row = ModuleReg(name=module_info['name'], description=module_info['description'],
                             user_role=module_info['user_role'], pubkey=module_info['pubkey'],
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
        self.row = self.session.query(ModuleReg).filter_by(id=id).first()
        self.pubkey = self.row.pubkey
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
        # return verify(pubkey_str(), sign, self.get('pubkey'))
        if isinstance(sign, str):
            sign = bytes(sign, encoding='utf-8')
        try:
            rsa.verify(self.pubkey.encode(), sign, rsa.PublicKey.load_pkcs1(self.pubkey.encode()))
            return True
        except rsa.pkcs1.VerificationError:
            return False

    def register_table(self, table_info):
        """
        注册私有表
        note: 注册后表进入待审核状态
        :param table_info:
        :return:
        """
        manager = current_app.table_manager
        manager.set_mod(self)
        manager.register_table(table_info)

    def have_query_permission(self, table):
        """
        验证对表的访问权限
        :param table: 表名
        :return: 权限小于表最低权限返回False，否则返回True
        """
        sens = self.session.query(Tables).filter_by(name=table).first().sensitivity
        if sens > self.get('permission'):
            return False
        return True

    def have_row_delete_permission(self, table):
        """
        删除行权限
        当前仅允许删除私有表数据
        :param table:
        :return:
        """
        for t in self.row.private_table:
            if t.name == table:
                return True
        return False

    def modifiable_fields(self, table):
        """
        表修改权限，包括创建表和修改数据
        当前由字段敏感度决定
        :param table:
        :return:
        """
        return self.available_fields(table)

    def have_table(self, table):
        """
        查询私有表
        :param table:
        :return:
        """
        for t in self.row.private_table:
            if t.name == table:
                return True
        return False

    def available_fields(self, table):
        """
        返回表中当前module可查询字段列表
        :param table:
        :return:
        """
        fields = self.session.query(Tables).filter_by(name=table).first().fields
        field_l = []
        for field in fields:
            sens = field.sensitivity
            if sens <= self.get('permission'):
                field_l.append(field.name)
        return field_l

def signature_verify(func):
    """
    签名验证装饰器
    注意：由于使用rsa直接签名在request中会因为decode()出现信息丢失，需要在请求时将sign进行base64编码并解码为str传输
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            id = int(request.args.get('module_id', None))
            sign = request.args.get('signature', None)
            # sign += '=' * (-len(sign) % 4)
            sign = sign.encode()
            sign = base64.b64decode(sign)
            print(len(sign))
            if id is None:
                return general_error('400', 'module_id is required')
            if sign is None:
                return general_error('400', 'signature is required')
            mod = module_manager(id)  # 实例化module_manager
        except ValueError as e:
            return general_error('400', 'unknown error', error_msg=repr(e))
        # 模块权限认证
        # 验证签名
        v = mod.verify(sign) # type(sign) == bytes
        if not v:
            return general_error('403', 'verify failed', pubkey=mod.get('pubkey'), sign=sign.decode())
        return func(*args, **kwargs)
    return wrapper