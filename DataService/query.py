from flask_restless import ProcessingException
from .models import Tables, get_session
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
    if not mod.check_table_permission(table):
        raise ProcessingException('query is refused', 403)
    request.mod = mod
    request.table = table

def handel_res(result=None, **kw):
    """
        隐藏结果中的高敏感数据
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

