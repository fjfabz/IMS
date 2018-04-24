import pytest
from ..module_manager import module_manager
from . import pubkey as pub_key

@pytest.mark.parametrize('name, description, user_role, pubkey, auth, auth_email, certification', [
    ('test2', 'description', 0, pub_key, None, 'auth_email', None)
])
def test_register(name, description, user_role, pubkey, auth, auth_email, certification):
    mod = module_manager()
    mod_info = {
        'name': name,
        'description': description,
        'user_role': user_role,
        'pubkey': pubkey,
        'auth': auth,
        'auth_email': auth_email,
        'certification': certification,
    }
    row = mod.register(mod_info)
    assert row.name == name
    assert row.description == description
    assert row.user_role == user_role
    assert row.pubkey == pubkey
    assert row.auth == auth
    assert row.auth_email == auth_email