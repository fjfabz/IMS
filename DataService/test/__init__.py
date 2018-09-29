from ..utils.utils import *
from ..models import get_session, ModuleReg
from ..utils.config_parser import Config

pubkey = pubkey_str()
privkey = priv_str()
base_url = 'http://127.0.0.1:8080/api'
session = get_session()

def init_test_data():
    # session = get_session()
    test_module = ModuleReg(pubkey=pubkey_str(), name='test_module')
    session.add(test_module)
    session.commit()

def get_config():
    return Config('../conf.json')