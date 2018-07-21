from . import postprocessors_dict, preprocessors_dict

def create_db_api(api_manager):
    from DataService.models import ModuleReg
    api_manager.create_api(
        ModuleReg,
        methods=['GET', 'PATCH', 'DELETE'],
        url_prefix='/query',
        preprocessors=preprocessors_dict,
        postprocessors=postprocessors_dict,
        allow_patch_many=True
    )

    from DataService.models import Fields
    api_manager.create_api(
        Fields,
        methods=['GET', 'POST'],
        url_prefix='/query',
        preprocessors=preprocessors_dict,
        postprocessors=postprocessors_dict,
        allow_patch_many=True
    )
