import logging
import gridfs
from flask import request,Blueprint
from utils import get_account_collection,make_result_msg,extract_face,reload_feature
from model import DB_CONNECTOR,FACE_COMPAROR_DICT
from schema import User,request_to_dict,eigenvalue_to_dict,collection_schema_dict
from face_process.face_comparor import Face_Comparor
user_app = Blueprint('user', __name__)

@user_app.route('/user_reigster',methods = ['POST'])
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
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _user_register(values):
    account,user_dict = request_to_dict(values,collection_schema_dict['user'],is_include_account=True)
    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data('accounts',{'account':account},{'account':1})
    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False,error_msg = 'Account was not register.')
    this_account_collection = get_account_collection(account)
    
    all_user_docs = DB_CONNECTOR.query_data(this_account_collection['user'],{},{'name':1})

    if all_user_docs:
        all_user_list = [doc['name'] for doc in all_user_docs]
    else:
        all_user_list = []
    # print(all_user_list)
    isValid,error_text = user.check(all_user_list)
    if not(isValid):
        logging.warning('front-end POST the same user in the account collection.')
        return make_result_msg(False,error_msg = error_text)

    fs = gridfs.GridFS(DB_CONNECTOR.db,this_account_collection['image'])
    encode_image = values['cropimage'].encode()
    image_id = fs.put(encode_image)
    user.update_image(image_id)
    
    user_insert_id = DB_CONNECTOR.insert_data(this_account_collection['user'],user.data).inserted_id
    
    landmarks = values['landmarks']
    face_embedding = extract_face(encode_image,landmarks)
    eigenvalue = eigenvalue_to_dict(user_insert_id,face_embedding,image_id)
    # print(eigenvalue)
    insert_eigenvalue = DB_CONNECTOR.insert_data(this_account_collection['eigenvalue'],eigenvalue).inserted_id
    reload_feature(account)
    return make_result_msg(True)

@user_app.route('/get_user_profile',methods = ['POST'])
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
        return make_result_msg(False,error_msg='REQUEST FAILED')        

def _get_user_profile(values):
    global DB_CONNECTOR
    account = values['account']

    this_account_collection = get_account_collection(account)
    fs = gridfs.GridFS(DB_CONNECTOR.db,this_account_collection['image'])

    result_data = DB_CONNECTOR.query_data(this_account_collection['user'],{},{'_id':0})
    
    user_list = []
    for doc in result_data:
        user = doc
        user['cropimageid'] = str(fs.get(user['cropimageid']).read())[1:]
        user_list.append(user)

    return make_result_msg(True,None,user_list)

@user_app.route('/edit_user_profile',methods = ['POST'])
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
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _edit_user_profile(values):
    global DB_CONNECTOR
    account,user_dict = request_to_dict(values,collection_schema_dict['user'],is_include_account=True)
    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data('accounts',{'account':account},{'account':1})
    
    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False,error_msg = 'Account was not register.')
    
    this_account_collection = get_account_collection(account)
    the_same_user_docs = DB_CONNECTOR.query_data(this_account_collection['user'],{'name':user_dict['name']},{})

    if the_same_user_docs:
        user_id = the_same_user_docs[0]['_id']
        if 'cropimage' in values.keys():
            fs = gridfs.GridFS(DB_CONNECTOR.db,this_account_collection['image'])
            encode_image = values['cropimage'].encode()
            image_id = fs.put(encode_image)
            user.update_image(image_id)
            
            landmarks = values['landmarks']
            face_embedding = extract_face(encode_image,landmarks)
            eigenvalue = eigenvalue_to_dict(user_id,face_embedding,image_id)
            insert_eigenvalue = DB_CONNECTOR.insert_data(this_account_collection['eigenvalue'],eigenvalue).inserted_id
    else:
        return make_result_msg(False,'No match user.')

    DB_CONNECTOR.update_data(this_account_collection['user'],{'_id':user_id},user.data)
    return make_result_msg(True)
