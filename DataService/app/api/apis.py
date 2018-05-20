from . import api
from flask import request, jsonify
from DataService.module_manager import module_manager, signature_verify
from DataService.errors import *
from DataService.utils.utils import *

@api.route('/register', methods=['POST'])
def register():
    register_field_check = ['name', 'description', 'user_role', 'pubkey', 'auth_email']
    mod_manager = module_manager()
    mod_info = request.args
    for filed in register_field_check:
        value = request.values.get(filed, None)
        if value is None:
            return general_error(400, 'filed <{}> is required'.format(filed))
    try:
        mod_row = mod_manager.register(mod_info)
    except Exception as e:
        return general_error(400, repr(e))
    return jsonify({
        'code': 200,
        'msg': 'register success',
        'pubkey': pubkey_str(),
        'module_info': {
            'id': mod_row.id,
            'name': mod_row.name,
            'status': mod_row.status,
            'register_time': mod_row.register_time,
            'permission': mod_row.permission,
        }
    })

@api.route('/register_table', methods=['POST'])
@signature_verify
def register_table():
    id = request.args.get('id', None) # signature_verify会验证id存在
    table_info = request.args.get('table_info', None)
    if table_info is None:
        return general_error(400, 'table info is required')
    mod = module_manager(id)
    try:
        mod.register_table(table_info)
    except ValueError as e:
        return general_error(400, repr(e))


@api.route('/pubkey')
def get_pubkey():
    return jsonify({
        'pubkey': pubkey_str(),
    })

@api.route('/module_pubkey/<int:id>')
def module_pubkey(id):
    mod = module_manager(id)
    return jsonify({
        'id': id,
        'pubkey': mod.get('pubkey')
    })


@api.route('/test', methods=['GET', 'POST'])
@signature_verify
def test_():
    return jsonify({
        'code': 200,
        'msg': 'test success',
    })