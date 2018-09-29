# 测试数据查询api
# 该测试需要运行web服务以完全模拟生产环境
from ...models import get_session, Tables
from ...module_manager import module_manager
import requests

def test_query_api():
    # 测试内容：
    #   各表查询接口按要求生成
    session = get_session()
    tables = session.query(Tables).all()
    mod = module_manager(1)
    pre_url = 'http://127.0.0.1:8888/query'
    base_params = {
        'module_id': 1,
        'signature': mod.pubkey
    }
    for table in tables:
        if table.file_pos is None:
            continue
        url = pre_url + '/{}'.format(table.name)
        r = requests.get(url, params=base_params)
        print(r.content)
        assert r.status_code == 200