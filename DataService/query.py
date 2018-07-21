from flask_restless import ProcessingException
from flask import request
from .module_manager import module_manager
import base64

def permission_check(*args, **kwargs):
    """
    restless全局preprocessor.
    签名校验
    验证当前表最低访问权限
    """
    # print('###########permission_check#################')
    try:
        id = int(request.args.get('module_id', None))
        sign = base64.b64decode(request.args.get('signature', None))  # sign通过base64编码上传
        if id is None:
            raise ProcessingException('module id is required', 400)
        if sign is None:
            raise ProcessingException('signature is required', 400)
        mod = module_manager(id)  # 实例化module_manager
    except Exception:
        raise ProcessingException('module_id is invalid', 400)
    v = mod.verify(sign)
    if not v:
        raise ProcessingException('sign verify failed', 403)
    table = request.path.split('/')[2]
    if not mod.have_query_permission(table):
        raise ProcessingException('query is refused', 403)
    request.mod = mod
    request.table = table

def handel_res(result=None, **kw):
    """
        隐藏结果中的高敏感数据
        作用于：GET GET_MANY POST PATCH
    """
    # print('###########postprocessor#################')
    # print(result)
    mod = request.mod
    if result is None:
        return
    field_l = ['id', 'name', 'description', 'user_role', 'certification'] # mod.available_fields(request.table)
    for item in result:
        if item not in field_l:
            result[item] = 'no permission'


def delete_permission(instance_id=None, **kwargs):
    """
    delete方法preprocessor，只有私有表才可以执行删除操作
    作用于：DELETE DELETE_MANY
    :param instance_id: which is the primary key of the instance which will be deleted.
    :param kwargs:
    :return:
    """
    mod = request.mod
    table = request.table
    if not mod.have_row_delete_permission(table):
        raise ProcessingException('no permission to delete row')

def post_permission(data=None, **kwargs):
    """
    post权限验证preprocessor
    作用于：POST
    当前验证操作字段是否允许被模块修改
    :param data: which is the dictionary of fields to set on the new instance of the model.
    :param kwargs:
    :return:
    """
    mod = request.mod
    table = request.table
    fields = mod.modifiable_fields(table)
    for f in data:
        if f not in fields:
            raise ProcessingException('no permission to CREATE field<{0}>'.format(f))

def patch_permission(data=None, **kwargs):
    """
    patch权限验证preprocessor
    作用于：PATCH PATCH_MANY PUT PUT_MANY
    :return:
    """
    mod = request.mod
    table = request.table
    fields = mod.modifiable_fields(table)
    for f in data:
        if f not in fields:
            raise ProcessingException('no permission to UPDATE field<{0}>'.format(f))
