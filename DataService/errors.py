from flask import jsonify

def general_error(error_code, msg, **kwargs):
    res = {
        'code': error_code,
        'msg': msg,
    }
    for i in kwargs:
        res[i] = kwargs[i]
    return jsonify(res)