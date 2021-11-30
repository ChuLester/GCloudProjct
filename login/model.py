import logging
from utils import get_account_collection, make_result_msg, reload_feature
from schema import request_to_dict, collection_schema_dict, google_to_account
from model import DB_CONNECTOR, FACE_COMPAROR_DICT
from werkzeug.security import check_password_hash
from error_code import error_code_dict


def _google_login(values):
    google_account_dict = request_to_dict(
        values, collection_schema_dict['google_account'])

    account = google_to_account(google_account_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account.data['account']}, {'account': 1})

    if the_same_docs is None:
        account_id = DB_CONNECTOR.insert_data('profile', {account.data})
        account_name = account.data['account']
        logging.info('Create Accont : %s , InsertID : %s' %
                     (account_name, str(account_id)))

    reload_feature(account.data['account'])
    logging.info('%s login' % (account.data['account']))

    return make_result_msg(True)


def _get_login_user():
    return make_result_msg(True, None, list(FACE_COMPAROR_DICT.keys()))


def _login(values):
    login_info = request_to_dict(values, collection_schema_dict['login'])
    account = login_info['account']
    password = login_info['password']

    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'_id': 0})

    if the_same_docs:
        if check_password_hash(the_same_docs[0]['password'], password):
            reload_feature(login_info['account'])
            logging.info('%s login' % (login_info['account']))
            return make_result_msg(True)
        else:
            return make_result_msg(False, error_code_dict[620])
    else:
        return make_result_msg(False, error_code_dict[611])


def _logout(values):
    logout_info = request_to_dict(values, collection_schema_dict['logout'])
    if logout_info['account'] in FACE_COMPAROR_DICT:
        del FACE_COMPAROR_DICT[logout_info['account']]

        logging.info('%s logout' % (logout_info['account']))
        return make_result_msg(True)
    else:
        return make_result_msg(False, error_code_dict[621])
