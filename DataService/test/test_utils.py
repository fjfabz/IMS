from .. utils import *
from . import pubkey, privkey, base_url
import requests

"""
 TODO:
    - signature对于str和bytes的兼容 找出为什么
"""

def test_pubkey_one(): # 测试__init__中pubkey与服务器获取一致
    assert pubkey == requests.get(base_url + '/pubkey').json()['pubkey']

def test_signature_gene(): # 测试两个生成过程是否一致
    # 本地生成
    url = base_url + '/pubkey'
    r = requests.get(url)
    msg = r.json()['pubkey']
    sign = signature(msg, privkey)





def test_generate_key():
    pub, priv = generate_key()
    pub_l, priv_l = load_key()
    assert pub.save_pkcs1() == pub_l.save_pkcs1()
    assert priv.save_pkcs1() == priv_l.save_pkcs1()

def test_pubkey_str():
    pub_str = pubkey_str()
    assert pubkey_check(pub_str) == True

def test_signature_verify():
    sign = signature('test', privkey)
    assert verify('test', sign, pubkey) == True

def test_get_conf_from_json():
    conf = get_conf_from_json('../conf.json')
    assert conf.get('current_mod') == 'dev'
