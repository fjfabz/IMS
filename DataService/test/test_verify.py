import requests
from ..utils.utils import *
import base64
from ..module_manager import module_manager

def test_verify():
    # 测试module_manager.verify()
    # 该测试通过
    # module_manager.verify() signature() 函数功能正常
    mod = module_manager(1)
    assert mod.verify(signature(mod.pubkey, priv_str())) == True

def test_server_sign_verify():
    # 测试验证装饰器 通过sign验证
    # 该测试通过
    # verify逻辑正常
    mod = module_manager(1)
    params = {
        'module_id': 1,
        'signature': base64.b64encode(signature(mod.pubkey, priv_str())).decode()
    }
    # assert params['signature'] == signature(mod.pubkey, priv_str())
    print(len(params['signature']))
    r = requests.post('http://127.0.0.1:8888/api/verify_test', params=params)
    print(len(bytes(r.json()['sign'], encoding='utf-8')))
    assert r.json()['msg'] == 'pass'
    assert r.json()['sign'] == params['signature']

def test_server_pw_verify():
    pass
