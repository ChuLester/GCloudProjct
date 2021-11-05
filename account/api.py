import logging
from flask import Blueprint,request
from model import DB_CONNECTOR
from face_process.face_comparor import Face_Comparor
from utils import make_result_msg,check_account_exist,get_account_collection
from schema import Account,request_to_dict,collection_schema_dict

account_app = Blueprint('account', __name__)

@account_app.route('/company_register',methods = ['POST'])
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
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _company_register(values):
    account_dict = request_to_dict(values,collection_schema_dict['account'])
    account = Account(account_dict)

    the_same_docs = DB_CONNECTOR.query_data('accounts',{'account':account.data['account']},{'account':1})

    if the_same_docs is None:
        account_id = DB_CONNECTOR.insert_data('accounts',account.data)
        account_name = account.data['account']
        DB_CONNECTOR.create_collection('user_%s'%(account_name))
        DB_CONNECTOR.create_collection('eigenvalue_%s'%(account_name))
        DB_CONNECTOR.create_collection('record_%s'%(account_name))
        DB_CONNECTOR.create_collection('image_%s.files'%(account_name))
        DB_CONNECTOR.create_collection('image_%s.chunks'%(account_name))
        DB_CONNECTOR.create_collection('clockin_%s'%(account_name))
        return make_result_msg(True)
    else:
        logging.warning('front-end POST the same account in DB.')
        return make_result_msg(False,error_msg='Account is registed')

@account_app.route('/remove_company_account',methods=['POST'])
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
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _remove_company_account(values):
    account = values['account']
    this_account_collection = get_account_collection(account)
    if check_account_exist(account):
        DB_CONNECTOR.delete_data('accounts',{'account': account})
        for collection_type in this_account_collection.keys():
            print('kill ',this_account_collection[collection_type])
            DB_CONNECTOR.drop_collection(this_account_collection[collection_type])
    
        return make_result_msg(True)
    else:
        return make_result_msg(False,error_msg='Account is invalid.') 