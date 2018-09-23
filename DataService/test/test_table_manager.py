from ..module_manager import module_manager
import pytest
from ..table_manager import table_manager
from ..models import get_session
from ..models.sys import *
from ..utils.db_tools import all_tables
from ..manager import create_app

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
test_info = [table_info1]

@pytest.fixture(scope='module')
def table_test_fixture():
    app = create_app('test')
    app_ctx = app.app_context()
    app_ctx.push()
    mod = module_manager(id=1)
    manager = table_manager(mod)
    version = manager.session.execute('select * from alembic_version').first()[0]
    print(version)
    manager.set_test_rollback_version(version)
    yield manager
    for i in test_info:
        manager._test_teardown(i)


@pytest.mark.parametrize('table_info', [
    table_info1,
])
def test_register_table(table_test_fixture, table_info):
    # 测试要求结果：
    # Table Field表更新
    # 新表生成(新表生成说明数据库已经正常迁移，映射文件正常)
    # *api生成 等待api管理器开发完成
    manager = table_test_fixture
    session = manager.session
    manager.register_table(table_info)

    all_table = all_tables()
    # Table Field表更新
    for table in table_info:
        table_row = session.query(Tables).filter_by(name=table['table_name'], owner_id=manager.current_mod.get('id')).first()
        assert table_row is not None
        # 新表生成
        print(table_row)
        assert table['table_name'] in all_table
        for field in table['fields']:
            field_row = session.query(Fields).filter_by(name=field, table_id=table_row.id).first()
            assert field_row is not None


@pytest.mark.parametrize('table_info', [
    table_info1,
])
def test_delete_table(table_test_fixture, table_info):
    # 测试结果要求：
    # Table Field表更新
    # 旧表删除
    session = get_session()
    manager = table_test_fixture

    for table in table_info:
        manager.delete_table(table['table_name'])

    all_table = all_tables()
    # Table Field表更新
    for table in table_info:
        table_row = session.query(Tables).filter_by(name=table['table_name'], owner_id=manager.current_mod.get('id')).first()
        assert table_row is None
        # 新表生成
        assert table['table_name'] not in all_table
        for field in table['fields']:
            field_row = session.query(Fields).filter_by(name=field, table_id=table_row.id).first()
            assert field_row is None
