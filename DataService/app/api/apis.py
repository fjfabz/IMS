from . import api
from flask import request, jsonify, current_app
from DataService.module_manager import module_manager, auth_verify
from DataService.errors import *
from DataService.utils.utils import *
import json

@api.route('/register', methods=['POST'])
def register():
    register_field_check = ['name', 'admin_pw', 'description', 'user_role', 'pubkey', 'auth_email']
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
@auth_verify
def register_table():
    id = int(request.args.get('module_id', None)) # signature_verify会验证id存在
    table_info =  json.loads(request.args.get('table_info', None))
    if table_info is None:
        return general_error(400, 'table info is required')
    mod = module_manager(id)
    try:
        mod.register_table(table_info)
        return jsonify({
            'code': 200,
            'msg': 'register success'
        })
    except ValueError as e:
        return general_error(400, repr(e))

@api.route('/module_pubkey/<int:id>')
def module_pubkey(id):
    mod = module_manager(id)
    return jsonify({
        'id': id,
        'pubkey': mod.get('pubkey')
    })

############# test API ################

@api.route('/test', methods=['GET', 'POST'])
def test_():
    return jsonify({
        'code': 200,
        'msg': 'test success',
    })

@api.route('/close_test')
def close_test():
    current_app.api_manager.close_api('/api/test')

@api.route('/teardown', methods=['POST'])
def teardown():
    current_app.table_manager.set_mod(module_manager(int(request.args.get('module_id'))))
    table_info = json.loads(request.args.get('table_info'))
    current_app.table_manager.test_teardown(table_info, request.args.get('version', None))

@api.route('/verify_test', methods=['POST'])
@auth_verify
def verify_test():
    return jsonify({
        'code': 200,
        'msg': 'pass',
        'sign': request.args.get('signature')
    })