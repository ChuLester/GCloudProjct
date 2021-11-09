import logging
from flask import Blueprint,request
from utils import make_result_msg
from login.model import _login,_logout,_get_login_user
login_app = Blueprint('login', __name__)

@login_app.route('/login',methods = ['POST'])
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
        return make_result_msg(False,error_msg='REQUEST FAILED')


@login_app.route('/get_login_user',methods = ['POST'])
def get_login_user():
    if request.method == 'POST':
        result_string = _get_login_user()
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')

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

