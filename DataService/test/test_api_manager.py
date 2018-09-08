import requests

def test_api_close():
    base_url = 'http://127.0.0.1:8080'
    r = requests.get(base_url + '/api/test').json()
    # 第一次请求成功
    assert r['code'] == 200
    assert r['msg'] == 'test success'

    requests.get(base_url + '/api/close_test')
    r = requests.get(base_url + '/api/test').json()
    # api关闭
    assert r['code'] == 403
    assert r['msg'] == 'request url is intercepted'