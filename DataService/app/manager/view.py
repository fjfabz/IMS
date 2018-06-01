from . import manager
from flask import render_template
from DataService.models import get_session, Tables, Fields

@manager.route('/')
def index():
    data = {
        'tag_list': [
            '模块管理',
            '数据库管理',
        ],
        'current_tag': '模块管理',
        'tables': {},
        'show_info': {
            'id': '表id',
            'description': '描述',
            'owner_id': '所属模块',
            'status': '状态',
            'api_gene': 'API状态',
            'sensitivity': '敏感度',
            },
    }
    db_session = get_session()
    tables = db_session.query(Tables).all()
    data['count'] = len(tables)
    for table in tables:
        data['tables'][table.name] = {'fields': []}
        for field in table.fields:
            f = {
                'id': field.id,
                'name': field.name,
                'table_id': field.table_id,
                'sensitive': field.sensitivity,
            }
            data['tables'][table.name]['fields'].append(f)
        data['tables'][table.name]['id'] = table.id
        data['tables'][table.name]['name'] = table.name
        data['tables'][table.name]['owner_id'] = table.owner_id
        data['tables'][table.name]['status'] = table.status
        data['tables'][table.name]['api_gene'] = table.api_gene
        data['tables'][table.name]['sensitivity'] = table.sensitivity

    # fields = db_session.query(Fields).all()
    # for field in fields:
    #     f = {
    #         'id': field.id,
    #         'name': field.name,
    #         'table_id': field.table_id,
    #         'sensitive': field.sensitivity,
    #     }
    #     data['tables'][field.table].append(f)
    return render_template('manager.html', data=data)

"""
data = {
    tag_list: [
    ],
    current_tag: 
    tables: {
        tablename: {
            id:
            name:
            description:
            owner_id:
            fields:
            status:
            api_gene:
            sensitivity:
            fields: {
                id:
                name:
                description:
                table_id:
                sensitive:
            },
        }
    }
    show_info: [],
    count:
}
"""