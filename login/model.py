from utils import get_account_collection,make_result_msg,reload_feature
from schema import request_to_dict,collection_schema_dict
from model import DB_CONNECTOR,FACE_COMPAROR_DICT

def _get_login_user():
    return make_result_msg(True,None,list(FACE_COMPAROR_DICT.keys()))

def _login(values):
    login_info = request_to_dict(values,collection_schema_dict['login'])
    the_same_docs = DB_CONNECTOR.query_data('accounts',login_info,{})
    
    if the_same_docs:
        reload_feature(login_info['account'])
        return make_result_msg(True)
    else:
        return make_result_msg(False)

def _logout(values):
    logout_info = request_to_dict(values,collection_schema_dict['logout'])
    if logout_info['account'] in FACE_COMPAROR_DICT:
        del FACE_COMPAROR_DICT[logout_info['account']]
        return make_result_msg(True)
    else:
        return make_result_msg(False)
