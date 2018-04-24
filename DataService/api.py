"""
 TODO:
    - 注册/注销 api
    - 认证api
    - 添加私有数据表
"""
from flask import Flask, request, jsonify
import sys, os
sys.path.append('../')
from DataService.module_manager import module_manager, signature_verify
from DataService.errors import *
from DataService.utils import *

app = Flask(__name__)

@app.route('/api/register', methods=['POST'])
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

@app.route('/api/register_table', methods=['POST'])
@signature_verify
def register_table():
    pass


@app.route('/api/pubkey')
def get_pubkey():
    return jsonify({
        'pubkey': pubkey_str(),
    })

@app.route('/api/module_pubkey/<int:id>')
def module_pubkey(id):
    mod = module_manager(id)
    return jsonify({
        'id': id,
        'pubkey': mod.get('pubkey')
    })


@app.route('/api/test', methods=['GET', 'POST'])
@signature_verify
def test():
    return jsonify({
        'code': 200,
        'msg': 'test success',
    })

if __name__ == '__main__':
    app.run(port=8080, debug=True)

