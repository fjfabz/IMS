from flask import Flask, request
from flask_restless import APIManager
from DataService.models import engine, get_session
from sqlalchemy.orm import scoped_session, sessionmaker
from DataService.query_api import create_db_api
from DataService.api_manager import api_manager
from DataService.utils.config_parser import Config
from DataService.errors import *
from DataService.table_manager import table_manager

import os

app = Flask(__name__)
config = Config('conf.json')
app.service_config = config

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
create_db_api(restless_manager)

# url屏蔽
@app.before_request
def intercept():
    if request.path in app.service_config['api']['intercept_urls']:
        return general_error(403, 'request url is intercepted')

from DataService.app.api import api
app.register_blueprint(api, url_prefix='/api')

# api_manager
sys_api_manager = api_manager(app)

from DataService.app.manager import manager
app.register_blueprint(manager, url_prefix='/manager')

if __name__ == '__main__':
    app.run(port=8080, debug=True)
