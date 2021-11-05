import logging
import time
import gridfs
from flask import request,Blueprint
from bson.objectid import ObjectId
from utils import make_result_msg,extract_face,get_account_collection
from model import DB_CONNECTOR,FACE_COMPAROR_DICT
from face_process.face_comparor import Face_Comparor
from schema import request_to_dict,Clockin,eigenvalue_to_dict,Record,collection_schema_dict
from config import RecognizeConfig

identify_app = Blueprint('identify', __name__)

@identify_app.route('/clockin',methods = ['POST'])
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

@identify_app.route('/identify',methods = ['POST'])
def identify():
    """
    input:
        cropimage: user crop face image.
        landmark: face landmark

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

@identify_app.route('/update_face_feature',methods = ['POST'])
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
        FACE_COMPAROR_DICT[account] = Face_Comparor(account_all_eigenvalue)
        return make_result_msg(True)
    else:
        return make_result_msg(False,error_msg='Account is invalid.')