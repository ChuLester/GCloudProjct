import gridfs
import base64
import cv2
import json
import numpy as np
from flask import request,Flask
from mongo_connector import Connector
from inference_client import InferenceClient
from schema import *
from config import MongoConfig,InferenceConfig,RecognizeConfig
from face_comparor import FaceComparor
import logging
import time
from datetime import datetime
# from gevent import monkey

# monkey.patch_all()
app = Flask(__name__)

global DB_CONNECTOR,INFERENCE_CLIENT,FACE_COMPAROR_DICT
DB_CONNECTOR = Connector(MongoConfig)
INFERENCE_CLIENT = InferenceClient(InferenceConfig)
FACE_COMPAROR_DICT = {}
# app.config['db_connector'] = Connector(MongoConfig)
# app.config['inference_client'] = InferenceClient(InferenceConfig)
# app.config['FaceComparorDict'] = {}

@app.route('/get_login_user',methods = ['POST'])
def get_login_user():
    global FACE_COMPAROR_DICT

    if request.method == 'POST':
        return {'result':list(FACE_COMPAROR_DICT.keys())}

@app.route('/company_register',methods = ['POST'])
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
    global DB_CONNECTOR
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

@app.route('/user_reigster',methods = ['POST'])
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
    global DB_CONNECTOR
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
    
@app.route('/login',methods = ['POST'])
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

def _login(values):
    global DB_CONNECTOR,FACE_COMPAROR_DICT
    login_info = request_to_dict(values,collection_schema_dict['login'])
    the_same_docs = DB_CONNECTOR.query_data('accounts',login_info,{})
    
    if the_same_docs:
        reload_feature(login_info['account'])
        return make_result_msg(True)
    else:
        return make_result_msg(False)

def reload_feature(account):
    this_account_collection = get_account_collection(account)
    account_all_eigenvalue = DB_CONNECTOR.query_data(this_account_collection['eigenvalue'],{'userid':{'$ne':None}},{'value':1,'userid':1})
    FACE_COMPAROR_DICT[account] = FaceComparor(account_all_eigenvalue) 

@app.route('/logout',methods = ['POST'])
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

def _logout(values):
    global FACE_COMPAROR_DICT
    logout_info = request_to_dict(values,collection_schema_dict['logout'])
    if logout_info['account'] in FACE_COMPAROR_DICT:
        del FACE_COMPAROR_DICT[logout_info['account']]
        return make_result_msg(True)
    else:
        return make_result_msg(False)


@app.route('/clockin',methods = ['POST'])
def clockin():
    """
    input:
        'account' : company account's name.
        'userid' : user object id which link record data and eigenvalue data.
        'date' : user clockin time.
        'recordID': record object id link user.
        'status' : ON work or OFF work 
    output:
        result_string:
            if status is not [ON,OFF]:
                status : False
            else:
                ststus : True
    """    
    logging.info('Call clockin')
    if request.method == 'POST':
        result_string = _clockin(request.get_json())
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')


def _clockin(values):
    global DB_CONNECTOR
    account,clockin_info = request_to_dict(values,collection_schema_dict['clockin'],is_include_account = True)
    clockin = Clockin(clockin_info)


    this_account_collection = get_account_collection(account)

    if clockin_info['status'] in ['ON','OFF']:
        eigenvalue_id = DB_CONNECTOR.query_data(this_account_collection['record'],{'_id':ObjectId(clockin.data['recordID'])},{'eigenvalue':1}).__getitem__(0)['eigenvalue']
        DB_CONNECTOR.update_data(this_account_collection['eigenvalue'],{'_id':eigenvalue_id},{'userid':clockin.data['userid']})
        insert_clockin_id = DB_CONNECTOR.insert_data(this_account_collection['clockin'],clockin.data)
        return make_result_msg(True)
    else:
        return make_result_msg(False)

@app.route('/identify',methods = ['POST'])
def identify():
    """
    input:
        cropimage: user crop face image.

    output:
        if recognize is suceess and face is match:
            status: 
                True
            result:
                username : face model preidct user who is the most simility. 
                user_object_id : it match username. 
                record_object_id : store user eigenvalue and cropimage record objectid
            error_msg:
                None     
        else:
            status:
                False
            result:
                None
            error_msg: 
                if face is not match: : Cannot recognized.
                if account dose not login : account not login
                if account no avaliable data : No data can reognition.
    """  
    t1 = time.time()
    logging.info('Call identify')
    if request.method == 'POST':
        result_string = _identify(request.get_json())
        print("identify using time : ",time.time() - t1)
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _identify(values):
    global FACE_COMPAROR_DICT,DB_CONNECTOR
    
    account,identify_info = request_to_dict(values,collection_schema_dict['identify'],is_include_account = True)
    if account not in FACE_COMPAROR_DICT:return make_result_msg(False,'account not login')

    if len(FACE_COMPAROR_DICT[account].eigenvalue_data_list) == 0:return make_result_msg(False,'No data can reognition',None)

    this_account_collection = get_account_collection(account)

    encode_image = values['cropimage'].encode()
    
    t1 = time.time()
    fs = gridfs.GridFS(DB_CONNECTOR.db,this_account_collection['image'])
    image_id = fs.put(encode_image)
    t2 = time.time()
    print("Put image to DB using time : ",t2 - t1)

    landmarks = values['landmarks']
    face_embedding = extract_face(encode_image,landmarks)
    eigenvalue = eigenvalue_to_dict(None,face_embedding,image_id)
    t3 = time.time()
    print("Extract using time : ",(t3 - t2))

    insert_eigenvalue = DB_CONNECTOR.insert_data(this_account_collection['eigenvalue'],eigenvalue).inserted_id
    t4 = time.time()
    print("Insert Data to DB using time : ",t4 - t3)

    record = Record(image_id,insert_eigenvalue)
    # print(record.data)

    insert_record_id = DB_CONNECTOR.insert_data(this_account_collection['record'],record.data).inserted_id

    out_dict = {}
    userid,cosine_distance = FACE_COMPAROR_DICT[account].identify(face_embedding)
    
    t5 = time.time()
    match_user_cropimageid = DB_CONNECTOR.query_data(this_account_collection['user'],{"_id":userid},{"cropimageid":1})
    raw_image = fs.get(match_user_cropimageid[0]['cropimageid']).read()
    t6 = time.time()
    print("Query Data from DB using time : ",t6 - t5)

    if cosine_distance < RecognizeConfig['threshold']:
        # print(userid)
        result_query_data = DB_CONNECTOR.query_data(this_account_collection['user'],{'_id':userid},{'name':1})    
        # print(result_query_data)
        username = result_query_data.__getitem__(0)['name']
        logging.info('%s %f'%(username,cosine_distance))     
        out_dict['username'] = username
        out_dict['user_id'] = str(userid)
        out_dict['record_id'] = str(insert_record_id)
        out_dict['image'] = str(raw_image)[1:]
        return make_result_msg(True,error_msg=None,result=out_dict)
    else:
        
        return make_result_msg(False,error_msg='Cannot recognized.')

@app.route('/update_face_feature',methods = ['POST'])
def update_face_feature():
    """
    input:
        account : company account's name.
    
    output:
        if update face feature success:
            status : 
                True
            result :
                None
            error_msg :
                None
        else:
            status : 
                False
            result :
                None
            error_msg :
                if account info is incorrect : Account is invalid.       

    """


    logging.info('Call update_face_feature.')
    if request.method == 'POST':
        result_string = _update_face_feature(request.get_json())
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _update_face_feature(values):
    global DB_CONNECTOR
    account = values['account']
    this_account_collection = get_account_collection(account)

    #TODO face embedding clusting

    if the_same_docs:
        the_same_docs = DB_CONNECTOR.query_data('accounts',{},{'account':account})
        account_all_eigenvalue = DB_CONNECTOR.query_data(this_account_collection['eigenvalue'],{},{'value':1,'userid':1})
        FACE_COMPAROR_DICT[account] = FaceComparor(account_all_eigenvalue)
        return make_result_msg(True)
    else:
        return make_result_msg(False,error_msg='Account is invalid.')

@app.route('/remove_company_account',methods=['POST'])
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
    global DB_CONNECTOR
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

@app.route('/user_record',methods = ['POST'])
def user_record():
    """
    input:
        account : company account's name
    output:
        if success:
            status : 
                True
            result:
                user : user name
                image : user face image
                date : clockin date
                status : NO / OFF
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
    logging.info('Call user_record.')
    if request.method == 'POST':
        result_string = _user_record(request.get_json())
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _user_record(values):

    account = values['account']
    this_account_collection = get_account_collection(account)
    
    expression_list = []
    expression_list.append({"$lookup":{"from":this_account_collection['user'],"localField":"userid","foreignField":"_id","as":"user"}})
    expression_list.append({"$lookup":{"from":this_account_collection['record'],"localField":"recordID","foreignField":"_id","as":"image"}})
    expression_list.append({"$project":{"date":1,"status":1,"user.name":1,"image.cropimageID":1}})
    result_data = DB_CONNECTOR.aggregate(this_account_collection['clockin'],expression_list)

    fs = gridfs.GridFS(DB_CONNECTOR.db,this_account_collection['image'])
    
    output = []
    for doc in result_data:
        del doc['_id']
        doc['user'] = doc['user'][0]['name']
        raw_image = fs.get(doc['image'][0]['cropimageID']).read()
        raw_image = str(raw_image)[1:]
        doc['image'] = raw_image
        output.append(doc)


    return make_result_msg(True,result=output)

@app.route('/get_user_profile',methods = ['POST'])
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
                'landmarks' : five face landmark.
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

@app.route('/edit_user_profile',methods = ['POST'])
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

            face_embedding = extract_face(encode_image)
            eigenvalue = eigenvalue_to_dict(user_id,face_embedding,image_id)
            insert_eigenvalue = DB_CONNECTOR.insert_data(this_account_collection['eigenvalue'],eigenvalue).inserted_id
    else:
        return make_result_msg(False,'No match user.')

    DB_CONNECTOR.update_data(this_account_collection['user'],{'_id':user_id},user.data)
    return make_result_msg(True)    

@app.route('/cal_working_hours',methods = ['POST'])
def cal_working_hours():
    """
    input:
        account : company account's name
    output:
        status:
            True
        result:
            list:
                user : Num work hour.
        error_msg:
            None
    """
    logging.info('Call cal working hours.')
    if request.method == 'POST':
        result_string = _cal_working_hours(request.get_json())
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')
    
def _cal_working_hours(values):
    global DB_CONNECTOR
    # account,peroid_dict = request_to_dict(values,is_include_account = True)
    account,workhour_dict = request_to_dict(values,collection_schema_dict['workhour'],is_include_account=True)
    this_account_collection = get_account_collection(account)
    starttime = datetime.strptime(workhour_dict['starttime'],"%Y/%m/%d")
    endtime = datetime.strptime(workhour_dict['endtime'],"%Y/%m/%d")
    expression_list = []
    expression_list.append({"$project":{"status":"$status","_id":"$_id","userid":"$userid","date":{"$dateFromString":{"dateString":"$date"}}}})
    expression_list.append({"$match":{"date":{"$gte":starttime,"$lt":endtime}}})
    expression_list.append({"$group" : {"_id" : "$userid" ,"result_list" : {"$push" : {"status" : "$status","date" : "$date"}}}})
    expression_list.append({"$sort" : {"result_list.date" : 1}})
    expression_list.append({"$lookup" : {"from" : this_account_collection['user'] ,"localField" : "_id" ,"foreignField" : "_id" ,"as" : "user"}})
    result_data = DB_CONNECTOR.aggregate(this_account_collection['clockin'],expression_list)

    user_hour_dict = {}
    for user_clockin_doc in result_data:
        username = user_clockin_doc['user'][0]['name']
        work_hours = cal_work_hours(user_clockin_doc['result_list'])
        user_hour_dict[username] = work_hours

    return make_result_msg(True,None,user_hour_dict)
    
def cal_work_hours(clockin_dict):
    Clock_On = None
    ClockOn_time = 0
    total_hours = 0
    for doc in clockin_dict:
        status = doc['status']
        date = doc['date']
        if status == 'ON':
            Clock_On = True
            ClockOn_time = date
        elif status == "OFF" and Clock_On:
            end_time = date
            start_time = ClockOn_time
            total_hours = ((end_time - start_time).seconds) + total_hours
            Clock_On = False
    return total_hours // 3600      

def decode_image(base64_buffer):
    raw_image = bytes(base64_buffer[1:])
    raw_image = base64.decodebytes(raw_image)
    
    raw_image = np.frombuffer(raw_image,np.uint8).reshape(-1,1)
    image = cv2.imdecode(raw_image,cv2.IMREAD_COLOR)
    return image

def extract_face(encode_image,landmarks):
    global INFERENCE_CLIENT
    face_image = decode_image(encode_image)
    # cv2.imwrite('%f.jpg'%(time.time()),face_image)
    t1 = time.time()
    face_embedding = INFERENCE_CLIENT.predict(face_image,landmarks)
    print('Extract Using time : ',(time.time() - t1))
    return face_embedding

def get_account_collection(account_name):
    collection_dict = {}
    collection_dict['user'] = 'user_%s'%(account_name)
    collection_dict['eigenvalue'] = 'eigenvalue_%s'%(account_name)
    collection_dict['record'] = 'record_%s'%(account_name)
    collection_dict['image'] = 'image_%s'%(account_name)
    collection_dict['clockin'] = 'clockin_%s'%(account_name)
    collection_dict['image.files'] = collection_dict['image'] + '.files'
    collection_dict['image.chunks'] = collection_dict['image'] + '.chunks'
    return collection_dict

def check_account_exist(account):
    the_same_docs = DB_CONNECTOR.query_data('accounts',{'account':account},{'account':1})
    if the_same_docs is None:
        return False
    else:
        return True            

def make_result_msg(status,error_msg = None,result = None):
    out = {}
    out['status'] = status
    out['error_msg'] = error_msg
    out['result'] = result
    return json.dumps(out)

if __name__ == '__main__':
    # app.debug = True
    logging.basicConfig(filename='run.log',level=logging.DEBUG)
    app.run(host='0.0.0.0',port=8080, debug = True)
    
