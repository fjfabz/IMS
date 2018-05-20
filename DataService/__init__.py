from .query import permission_check, handel_res

preprocessors_dict = {
   'GET_SINGLE': [permission_check],
   'GET_MANY': [permission_check],
   'PATCH_SINGLE': [permission_check],
   'PATCH_MANY': [permission_check],
}
postprocessors_dict = {
    'GET_SINGLE': [handel_res],
    'GET_MANY': [handel_res],
    'PATCH_SINGLE': [handel_res],
    'PATCH_MANY': [handel_res],
}