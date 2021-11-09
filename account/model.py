import logging
from model import DB_CONNECTOR
from core.face_process.face_comparor import Face_Comparor
from utils import make_result_msg,check_account_exist,get_account_collection
from schema import Account,request_to_dict,collection_schema_dict

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