from flask import Flask
from flask_restless import APIManager
from DataService.models import engine
from sqlalchemy.orm import scoped_session, sessionmaker
from DataService.query_api import create_db_api

app = Flask(__name__)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
mysession = scoped_session(Session)
api_manager = APIManager(app, session=mysession) # 全局preprocessors postprocessors无效 原因不明
create_db_api(api_manager)

from DataService.app.api import api
app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    app.run(port=8080, debug=True)
