from ..module_manager import module_manager
import pytest

table_info1 = [
                {
                    'table_name': 't1',
                    'primary_key': ['id'],
                    'fields': {
                        'id': {
                            'type': 'Integer',
                            'length': 64,
                            'nullable': False,
                            'foreignkey':{
                                'table': 't2',
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
                    'table_name': 't2',
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

# @pytest.mark.parametrize('table_info', [
#     table_info1,
# ])
# def test_create_mapping_file(table_info):
#     mod = module_manager(id=1)
#     mod.create_table(table_info)
#     assert 0 == 1

@pytest.mark.parametrize('table_info', [
    table_info1,
])
def test_register_table(table_info):
    mod = module_manager(id=1)
    mod.register_table(table_info)
    assert 0 == 1