from . import Base, engine
from sqlalchemy.types import  String, Text, TIMESTAMP, PickleType, Integer, Boolean
from sqlalchemy.orm import  relationship
from sqlalchemy import Column, ForeignKey

class ModuleReg(Base):
    __tablename__ = 'module_reg'

    id = Column(Integer, primary_key=True)
    pubkey = Column(String(256)) # 模块公钥
    auth = Column(String(64)) # 作者
    admin_pw = Column(String(256)) # 管理员密码
    auth_email = Column(String(64)) # 作者邮箱
    name = Column(String(64)) # 模块名
    description = Column(Text) # 模块描述
    user_role = Column(Integer) # 适配角色 二进制表示
    certification = Column(Integer) # 认证状态
    # 0  系统模块
    # 1  公共功能模块
    # 2  私有模块
    status = Column(Integer) # 模块状态
    # 0  未审核
    # 1  服务运行
    # 2  服务停止
    # 3  服务异常
    # 4  服务关闭
    register_time = Column(TIMESTAMP) # 注册时间
    star_time = Column(TIMESTAMP) # 挂载时间
    stop_time = Column(TIMESTAMP) # 停止时间
    permission = Column(Integer) # 权限级别
    private_table = relationship('Tables', backref='module_reg') # 模块私有表
    modify_permission = relationship('Tables') # 修改权限
    server_entry = Column(String(256)) # 服务入口地址

class Tables(Base):
    __tablename__ = 'tables'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True)
    description = Column(String(256))
    owner_id = Column(Integer, ForeignKey('module_reg.id'))
    fields = relationship('Fields', backref='tables')
    status = Column(Integer)
    # 0 未审核
    # 1 已审核
    # 2 修改未审核
    note = Column(Text)
    sensitivity = Column(Integer)
    file_pos = Column(String(256)) # sqlalchemy位置描述 type: json

class Fields(Base):
    __tablename__ = 'fields'

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(256))
    note = Column(Text)
    name = Column(String(64))
    table_id = Column(Integer, ForeignKey('tables.id'))
    sensitivity = Column(Integer)

class SysAPI(Base):
    __tablename__ = 'sys_api'

    id = Column(Integer, primary_key=True)
    name = Column(String(64)) # API名
    param_description = Column(String(256)) # json格式参数列表
    status = Column(Integer)
    # 0 关闭
    # 1 开放
    sensitivity = Column(Integer) # API敏感度

# 系统管理员
class Admins(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(64))
    pw = Column(String(256))
    permission = Column(Integer) # 二进制位图

# log
class APILog(Base):
    __tablename__ = 'api_log'

    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, ForeignKey('sys_api.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('module_reg.id'), nullable=False)
    timestamp = Column(TIMESTAMP)
    level = Column(String(64))
    params = Column(String(256)) # 调用参数列表, json
    http_status = Column(Integer)
    detail = Column(String(256))

class ModuleLog(Base):
    __tablename__ = 'module_log'

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey('module_reg.id'), nullable=False)
    timestamp = Column(TIMESTAMP)
    level = Column(String(64))
    detail = Column(String(256))

class SysLog(Base):
    __tablename__ = 'sys_log'

    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP)
    level = Column(String(64))
    pos = Column(String(64)) # 产生位置
    detail = Column(String(256))



# 配置表
class ModuleStatus(Base):
    __tablename__ = 'module_status'

    code = Column(Integer, primary_key=True, autoincrement=False)
    description = Column(String(64))

class Sensitivity(Base):
    __tablename__ = 'sensitivity'
    # 0 开放数据
    # n n级敏感

    code = Column(Integer, primary_key=True, autoincrement=False)
    description = Column(String(64))

class Roles(Base):
    __tablename__ = 'roles'

    code = Column(Integer, primary_key=True, autoincrement=False) # 二进制位表示
    description = Column(String(64))

def create_db():
    Base.metadata.create_all(engine)
