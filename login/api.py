import logging
from flask import Blueprint, request, render_template
from utils import make_result_msg
from login.model import _login, _logout, _get_login_user, _google_login
from error_code import error_code_dict
from config import GOOGLE_OAUTH2_CLIENT_ID
login_app = Blueprint('login', __name__)

@login_app.route('/google_welcome_view')
def google_welcome():
    logging.info('Call Google Welcome')
    return render_template('index.html', google_oauth2_client_id=GOOGLE_OAUTH2_CLIENT_ID)

@login_app.route('/google_login', methods=['POST'])
def google_login():
    """
    input:
        'id' : 'google account id',
        'name': 'google name',
        'mail': 'google account email address',
        'token': 'google token'

    output:
        'status' : True
    """
    logging.info('Call Google Login') 
    if request.method == 'POST':
        result_string = _google_login(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@login_app.route('/login', methods=['POST'])
def login():
    """
    input:
        'account' : company account's name.
        'password' : company account's passowrd.

    output:
        result_string:
            if account and password conform to DB : 
                status : True
            else:
                status : False
    """
    logging.info('Call login.')
    if request.method == 'POST':
        result_string = _login(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@login_app.route('/get_login_user', methods=['POST'])
def get_login_user():
    if request.method == 'POST':
        result_string = _get_login_user()
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@login_app.route('/logout', methods=['POST'])
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
        return make_result_msg(False, error_msg=error_code_dict[600])
