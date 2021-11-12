import logging
from flask import Blueprint, request
from utils import make_result_msg
from account.model import _company_register, _remove_company_account
from error_code import error_code_dict
account_app = Blueprint('account', __name__)


@account_app.route('/company_register', methods=['POST'])
def company_register():
    """
        input: 
            'account' : user will registe company account name.
            'password' : just set the password.
            'mail' : user mail address.
            'workspace' : company name
            'third_party' : this columms isn't using.

        output:
            result_string:
                if request.method not POST: 'error'
                if database has the same account : 'Account is already registed.'
                if passowrd format is invalid : 'Password length is invalid.'
                if no any error: None

    """
    logging.info('Call Company_register')
    if request.method == 'POST':
        result_string = _company_register(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@account_app.route('/remove_company_account', methods=['POST'])
def remove_company_account():
    """
    input:
        account : company account's name

    output:
        if removing account is success:
            status:
                True
            result:
                None
            error_msg:
                None
        else:
            status:
                False
            result:
                None
            error_msg:
                if account is invalid : Account is invalid.

    """
    logging.info('Call remove_company_account.')
    if request.method == 'POST':
        result_string = _remove_company_account(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])
