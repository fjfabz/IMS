import requests
import json, base64
from . import privkey
from . import base_url as api_url
from ..utils.utils import *

base_url = 'http://127.0.0.1:8080/query/'
headers = {'Content-Type': 'application/json'}

def test_query():
    url = api_url + '/pubkey'
    r = requests.get(url)
    msg = r.json()['pubkey']
    sign = signature(msg, privkey)
    params = {
        'module_id': 1,
        'signature': base64.b64encode(sign),
    }
    response = requests.get(base_url + 'module_reg/1', params=params, headers=headers)
    print(response.json())
    assert response.status_code == 200
    assert 1 == 2
