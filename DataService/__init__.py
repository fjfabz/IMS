from .query import permission_check, handel_res, delete_permission, post_permission, patch_permission

preprocessors_dict = {
    'GET_SINGLE': [permission_check],
    'GET_MANY': [permission_check],
    'PATCH_SINGLE': [permission_check, patch_permission],
    'PATCH_MANY': [permission_check, patch_permission],
    'PUT_SINGLE': [permission_check, patch_permission],
    'PUT_MANY': [permission_check, patch_permission],
    'DELETE_SINGLE': [permission_check, delete_permission],
    'DELETE_MANY': [permission_check, delete_permission],
    'POST': [permission_check, post_permission]
}
postprocessors_dict = {
    'GET_SINGLE': [handel_res],
    'GET_MANY': [handel_res],
    'PATCH_SINGLE': [handel_res],
    'PATCH_MANY': [],
    'PUT_SINGLE': [],
    'PUT_MANY': [],
    'DELETE_SINGLE': [],
    'DELETE_MANY': [],
    'POST': [handel_res]

}