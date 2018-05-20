from ..module_manager import module_manager

def test_create_api():
    mod = module_manager()
    mod.create_api('Fields', ['GET', 'POST'])
