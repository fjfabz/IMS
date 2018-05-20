import pytest
import requests
from . import base_url, privkey
from ..utils.utils import *
import json, base64

'''
issues：
    - 发送sign和接受sign
'''

'''
note:
    sign通过bas64编码后传输
    
    
'''

def test_get_pubkey():
    url = base_url + '/pubkey'
    r = requests.get(url)
    assert pubkey_check(r.json()['pubkey']) == True

def test_pubkey_one(): # 使用公钥与记录公钥一致
    url = base_url + '/module_pubkey/1'
    r = requests.get(url).json()
    # print(pubkey_str())
    # print(r['pubkey'])
    assert pubkey_str() == r['pubkey'] # 与记录的公钥不一致


def test_signature_verify():  # 测试本地privkey和上传之后一致

    priv = priv_str()
    url = base_url + '/pubkey'
    r = requests.get(url)
    msg = r.json()['pubkey']
    sign = signature(msg, privkey)
    data = {
        'module_id': 1,
        'signature': base64.b64encode(sign),
        'privkey': priv
    }
    url = base_url + '/test'
    r = requests.post(url, params=data)
    r = r.json()
    assert True == verify(msg, sign, pubkey_str())
    if r['code'] == 403:
        assert pubkey_str() == r['pubkey'] # 测试密钥对匹配
        assert sign == base64.b64decode(r['msg'])
        assert verify(msg, sign, pubkey_str())
        assert verify(msg, sign, r['pubkey']) # 不是pubkey问题
    assert r['code'] == 200

