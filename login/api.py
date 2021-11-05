import logging
from flask import Blueprint,request
from model import DB_CONNECTOR,FACE_COMPAROR_DICT
from utils import get_account_collection,make_result_msg
from schema import request_to_dict,collection_schema_dict

login_app = Blueprint('login', __name__)


@login_app.route('/get_login_user',methods = ['POST'])
def get_login_user():
    if request.method == 'POST':
        return make_result_msg(True,None,list(FACE_COMPAROR_DICT.keys()))


@login_app.route('/logout',methods = ['POST'])
def logout():
    """
    input:
        account : company account's name.
    output:
        result_string:
            if account's FaceComparorDict has be created: 
                status : True
            else:
                status : False
    """
    logging.info('Call logout')
    if request.method == 'POST':
        result_string = _logout(request.get_json())
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _logout(values):
    logout_info = request_to_dict(values,collection_schema_dict['logout'])
    if logout_info['account'] in FACE_COMPAROR_DICT:
        del FACE_COMPAROR_DICT[logout_info['account']]
        return make_result_msg(True)
    else:
        return make_result_msg(False)
