# 测试私有表注册
from ...module_manager import module_manager
from ...utils.utils import *
from .. import get_config, session
import requests
import pytest
import base64
import json

table_info1 = [
                {
                    'table_name': 'create_table_test1',
                    'primary_key': ['id'],
                    'fields': {
                        'id': {
                            'type': 'Integer',
                            'length': 64,
                            'nullable': False,
                            'foreignkey':{
                                'table': 'create_table_test2',
                                'field': 'id'
                            }
                        },
                        'f1_1': {
                            'type': 'String',
                            'length': 64,
                        },
                        'f1_2': {
                            'type': 'PickleType',
                        },
                    }
                },
                {
                    'table_name': 'create_table_test2',
                    'primary_key': ['id'],
                    'fields': {
                        'id': {
                            'type': 'Integer',
                            'length': 64,
                            'nullable': False,
                        },
                        'f2_1': {
                            'type': 'String',
                            'length': 64,
                        },
                        'f2_2': {
                            'type': 'Boolean',
                        },
                    }
                },
]

@pytest.fixture(scope='function')
def teardown():
    version = session.execute('select * from alembic_version').first()[0]
    yield
    mod = module_manager(1)
    params = {
        'module_id': 1,
        'signature': base64.b64encode(signature(mod.pubkey, priv_str())).decode(),
        'table_info': table_info1,
        'version': version
    }
    conf = get_config()['run_config']['test']
    requests.post('http://{0}:{1}/api/teardonw'.format(conf['host'], conf['port']), params=params)

@pytest.mark.parametrize('table_info', [
    table_info1,
])
def test_register_table(teardown, table_info):
    # 测试内容：
    #   新表接口可用
    mod = module_manager(1)
    params = {
        'module_id': 1,
        'signature': base64.b64encode(signature(mod.pubkey, priv_str())).decode(),
        'table_info': json.dumps(table_info)
    }
    print(params['table_info'])
    conf = get_config()['run_config']['test']
    r = requests.post('http://{0}:{1}/api/register_table'.format(conf['host'], conf['port']), params=params)
    for table in table_info:
        print(r.json())
        assert r.json()['code'] == 200
        # 接口可用测试
        pre_url = 'http://{0}:{1}/query'.format(conf['host'], conf['port'])
        url = pre_url + '/{}'.format(table['table_name'])
        r = requests.get(url, params=params)
        print(url)
        assert r.json()['code'] == 200

