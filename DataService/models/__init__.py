from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import configparser
from alembic.config import Config
from alembic import command


from ..utils.utils import *

conf = get_conf_from_json('../conf.json')
db_conf = conf['db'][conf['current_mod']]
uri = 'mysql+pymysql://{}:0912@{}:{}/{}'.format(db_conf['user'], db_conf['host'],
                                                db_conf['port'], db_conf['db_name'])

Base = declarative_base()
engine = create_engine(uri)

if conf['init'] == 'True':
    # 修改alembic.ini
    alembic_conf = configparser.ConfigParser()
    alembic_conf.read('alembic.ini.bak')
    alembic_conf.set('alembic', 'sqlalchemy.url', uri)
    alembic_conf.write(open('alembic.ini', 'w'))
    # 更新数据库
    alembic_conf = Config('alembic.ini')
    command.upgrade(alembic_conf, 'head')
    conf['init'] = 'False'

def get_session():
    db_session = sessionmaker(bind=engine)
    session = db_session()
    return  session

from .sys import *
