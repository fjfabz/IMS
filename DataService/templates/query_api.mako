from . import postprocessors_dict, preprocessors_dict

def create_db_api(api_manager):
%for api in apis:
    api_manager.create_api(
        ${api.model_name},
    %for param in api.predefine_params:
        param=api[param]
    %endfor
    )
%endfor
%if len(apis) == 0:
    pass
%endif