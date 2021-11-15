import logging
import gridfs
from flask import request, Blueprint
from utils import make_result_msg
from user.model import _user_register, _edit_user_profile, _get_user_profile
from error_code import error_code_dict
user_app = Blueprint('user', __name__)


@user_app.route('/user_reigster', methods=['POST'])
def user_reigster():
    """
        input:
            'account' : company account name which user belongs.
            'phone' : user phone.
            'mail' : user mail address.
            'birthday' : user birthday.
            'manager' : Is user has manage auth?
            'face' : when Identify accept ,print user face image.
            'landmarks' : five face landmark.
            'user' : user name
            'wage' : user salary for hour

        output:
            result_string:
                if request.method not POST: 'error'
                if company has the same username : 'user is exist'
                if no any error: None

    """
    logging.info('Call user_register')
    if request.method == 'POST':
        result_string = _user_register(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@user_app.route('/get_user_profile', methods=['POST'])
def get_user_profile():
    """
    input:
        account : company account's name
    output:
        if success:
            status : 
                True
            result:
                'account' : company account name which user belongs.
                'phone' : user phone.
                'mail' : user mail address.
                'birthday' : user birthday.
                'manager' : Is user has manage auth?
                'face' : when Identify accept ,print user face image.
                'user' : user name
                'wage' : user salary for hour
            error_msg:
                None
        else:
            status :
                False
            result:
                None
            error_msg:
                None

    """
    logging.info('Get user profile')
    if request.method == 'POST':
        result_string = _get_user_profile(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@user_app.route('/edit_user_profile', methods=['POST'])
def edit_user_profile():
    """
    input:
        account : company account's name
        phone : user phone.
        mail : user mail address.
        birthday : user birthday.
        manager : Is user has manage auth?
        face : when Identify accept ,print user face image.
        landmarks : five face landmark.
        user : user name
        wage : user salary for hour
    output:
        if success:
            status : 
                True
            result:
                None
            error_msg:
                None
        else:
            status :
                False
            result:
                None
            error_msg:
                if no match user : No match user.
                if no match account : Account was not register.

    """
    logging.info('Call edit user profile.')
    if request.method == 'POST':
        result_string = _edit_user_profile(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])
