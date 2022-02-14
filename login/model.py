import logging
from google.oauth2 import id_token
from google.auth.transport import requests
from utils import get_account_collection, make_result_msg, reload_feature
from schema import request_to_dict, collection_schema_dict, google_to_account
from model import DB_CONNECTOR, FACE_COMPAROR_DICT
from werkzeug.security import check_password_hash
from error_code import error_code_dict
from config import GOOGLE_OAUTH2_CLIENT_ID


def _google_login(values):
    logging.info(values)
    google_account_dict, loss_argument = request_to_dict(
        values, collection_schema_dict['google_account'])

    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    account = google_to_account(google_account_dict)
    # token = account.data['third_party']['token']
    # try:
    #     # Specify the GOOGLE_OAUTH2_CLIENT_ID of the app that accesses the backend:
    #     id_info = id_token.verify_oauth2_token(
    #         token,
    #         requests.Request(),
    #         GOOGLE_OAUTH2_CLIENT_ID
    #     )

    #     # print(id_info)

    #     if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
    #         raise ValueError('Wrong issuer.')

    #     # ID token is valid. Get the user's Google Account ID from the decoded token.
    #     # user_id = id_info['sub']
    #     # reference: https://developers.google.com/identity/sign-in/web/backend-auth
    # except ValueError:
    #     # Invalid token
    #     # raise ValueError('Invalid token')
    #     return make_result_msg(False, error_code_dict[613], False)

    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account.data['account']}, {'account': 1})

    if the_same_docs is None:
        account.data['users'] = []
        account.data['user_detail'] = []
        account_id = DB_CONNECTOR.insert_data('profile', account.data)
        account_name = account.data['account']
        logging.info('Create Accont : %s , InsertID : %s' %
                     (account_name, str(account_id)))

    reload_feature(account.data['account'])
    logging.info('%s login' % (account.data['account']))

    return make_result_msg(True, None, True)


def _get_login_user():
    return make_result_msg(True, None, list(FACE_COMPAROR_DICT.keys()))


def _login(values):
    logging.info(values)
    login_info, loss_argument = request_to_dict(
        values, collection_schema_dict['login'])
    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)
    account = login_info['account']
    password = login_info['password']

    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'_id': 0})

    if the_same_docs:
        if check_password_hash(the_same_docs[0]['password'], password):
            reload_feature(login_info['account'])
            logging.info('%s login' % (login_info['account']))
            return make_result_msg(True, None, True)
        else:
            return make_result_msg(False, error_code_dict[620], False)
    else:
        return make_result_msg(False, error_code_dict[611], False)


def _logout(values):
    logging.info(values)
    logout_info, loss_argument = request_to_dict(
        values, collection_schema_dict['logout'])
    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)
    if logout_info['account'] in FACE_COMPAROR_DICT:
        del FACE_COMPAROR_DICT[logout_info['account']]

        logging.info('%s logout' % (logout_info['account']))
        return make_result_msg(True, None, True)
    else:
        return make_result_msg(False, error_code_dict[621], False)
