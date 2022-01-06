import logging
from model import DB_CONNECTOR
from core.face_process.face_comparor import Face_Comparor
from utils import make_result_msg, check_account_exist, get_account_collection
from schema import Account, request_to_dict, collection_schema_dict, google_to_account
from werkzeug.security import generate_password_hash
from error_code import error_code_dict


def _company_register(values):
    logging.info(values)
    account_dict, loss_argument = request_to_dict(
        values, collection_schema_dict['account'])

    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    account = Account(account_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account.data['account']}, {'account': 1})

    account.data['password'] = generate_password_hash(account.data['password'])
    account.data['user_detail'] = []
    account.data['users'] = []
    if the_same_docs is None:

        account_id = DB_CONNECTOR.insert_data('profile', account.data)
        account_name = account.data['account']
        logging.info('Create Accont : %s , InsertID : %s' %
                     (account_name, str(account_id)))
        return make_result_msg(True)
    else:
        logging.warning('front-end POST the same account in DB.')
        return make_result_msg(False, error_msg=error_code_dict[611])


def _remove_company_account(values):
    logging.info(values)
    account = values['account']

    if check_account_exist(account):
        DB_CONNECTOR.delete_data('profile', {'account': account})
        DB_CONNECTOR.delete_data('eigenvalue', {'account': account})
        DB_CONNECTOR.delete_data('record', {'account': account})

        return make_result_msg(True)
    else:
        return make_result_msg(False, error_msg=error_code_dict[611])
