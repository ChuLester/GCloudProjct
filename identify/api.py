import logging
from flask import request, Blueprint
from utils import make_result_msg
from identify.model import _clockin, _identify, _update_face_feature
from error_code import error_code_dict
identify_app = Blueprint('identify', __name__)


@identify_app.route('/clockin', methods=['POST'])
def clockin():
    """
    input:
        'account' : company account's name.
        'userid' : user object id which link record data and eigenvalue data.
        'date' : user clockin time.
        'recordID': record object id link user.
        'status' : ON work or OFF work 
    output:
        result_string:
            if status is not [ON,OFF]:
                status : False
            else:
                ststus : True
    """
    logging.info('Call clockin')
    if request.method == 'POST':
        result_string = _clockin(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@identify_app.route('/identify', methods=['POST'])
def identify():
    """
    input:
        cropimage: user crop face image.
        landmark: face landmark

    output:
        if recognize is suceess and face is match:
            status: 
                True
            result:
                username : face model preidct user who is the most simility. 
                user_object_id : it match username. 
                record_object_id : store user eigenvalue and cropimage record objectid
            error_msg:
                None     
        else:
            status:
                False
            result:
                None
            error_msg: 
                if face is not match: : Cannot recognized.
                if account dose not login : account not login
                if account no avaliable data : No data can reognition.
    """

    logging.info('Call identify')
    if request.method == 'POST':
        result_string = _identify(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@identify_app.route('/update_face_feature', methods=['POST'])
def update_face_feature():
    """
    input:
        account : company account's name.

    output:
        if update face feature success:
            status : 
                True
            result :
                None
            error_msg :
                None
        else:
            status : 
                False
            result :
                None
            error_msg :
                if account info is incorrect : Account is invalid.       

    """
    logging.info('Call update_face_feature.')
    if request.method == 'POST':
        result_string = _update_face_feature(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])
