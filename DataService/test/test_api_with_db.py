import pytest
import requests
import json
from ..utils.utils import *
# from . import pubkey
pubkey = pubkey_str()

"""
 TODO:
    - teardown
"""

@pytest.mark.parametrize('name, description, user_role, pubkey, auth, auth_email, certification', [
    (None, 'description', 0, 'pubkey', None, 'auth_email', None),
    ('test', 'description', 0, 'pubkey', None, 'auth_email', None)
])
def test_register_fail(name, description, user_role, pubkey, auth, auth_email, certification):
    data = {
        'name': name,
        'description': description,
        'user_role': user_role,
        'pubkey': pubkey,
        'auth': auth,
        'auth_email': auth_email,
        'certification': certification,
    }
    url = 'http://127.0.0.1:8080/api/register'
    r = requests.post(url, json=json.dumps(data))
    r = r.json()
    assert r['code'] == 400

@pytest.mark.parametrize('name, description, user_role, pubkey, auth, auth_email, certification', [
    ('test', 'description', 0, pubkey, None, 'auth_email', None)
])
def test_register_success(name, description, user_role, pubkey, auth, auth_email, certification):
    data = {
        'name': name,
        'description': description,
        'user_role': user_role,
        'pubkey': pubkey,
        'auth': auth,
        'auth_email': auth_email,
        'certification': certification,
    }
    url = 'http://127.0.0.1:8080/api/register'
    r = requests.post(url, params=data)
    r = r.json()
    print(r['msg'])
    assert r['code'] == 200

