from flask import Flask, request
from flask_restless import APIManager
from sqlalchemy.orm import scoped_session, sessionmaker
from DataService.utils.config_parser import Config
from DataService.errors import *

import os

def create_app(mode):

    app = Flask(__name__)
    config = Config('conf.json')
    config['current_mod'] = mode
    config['init'] = True
    app.service_config = config

    # mode配置需要在db_engine产生前完成
    from DataService.models import engine, get_session
    from DataService.api_manager import api_manager
    from DataService.table_manager import table_manager

    # 切换工作目录
    os.chdir(config['working_dir'])

    # 设置全局db_session
    app.db_session = get_session()

    # 设置全局table_manager
    app.table_manager = table_manager()

    # flask-restless
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    mysession = scoped_session(Session)
    restless_manager = APIManager(app, session=mysession) # 全局preprocessors postprocessors无效 原因不明
    app.restless_manager = restless_manager
    api_manager.init_api_from_db(restless_manager)


    # url屏蔽
    @app.before_request
    def intercept():
        if request.path in app.service_config['api']['intercept_urls']:
            return general_error(403, 'request url is intercepted')

    from DataService.app.api import api
    app.register_blueprint(api, url_prefix='/api')

    # 设置全局api_manager
    sys_api_manager = api_manager(app)
    app.api_manager = sys_api_manager

    from DataService.app.manager import manager
    app.register_blueprint(manager, url_prefix='/manager')

    return app

if __name__ == '__main__':
    app = create_app('dev')
    app.run(port=8080, debug=True)
