from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..utils.utils import *

conf = get_conf_from_json('../conf.json')
db_conf = conf['db'][conf['current_mod']]
uri = 'mysql+pymysql://{}:0912@{}:{}/{}'.format(db_conf['user'], db_conf['host'],
                                                db_conf['port'], db_conf['name'])

Base = declarative_base()
engine = create_engine('mysql+pymysql://root:0912@localhost:3306/ims')

def get_session():
    db_session = sessionmaker(bind=engine)
    session = db_session()
    return  session

from .sys import *
