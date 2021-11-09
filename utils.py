import base64
import gridfs
import cv2
import json
import numpy as np
import time
from model import INFERENCE_CLIENT,DB_CONNECTOR,FACE_COMPAROR_DICT
from core.face_process.face_comparor import Face_Comparor

def decode_image(base64_buffer):
    raw_image = bytes(base64_buffer[1:])
    raw_image = base64.decodebytes(raw_image)
    
    raw_image = np.frombuffer(raw_image,np.uint8).reshape(-1,1)
    image = cv2.imdecode(raw_image,cv2.IMREAD_COLOR)
    return image

def extract_face(encode_image,landmarks):
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

def reload_feature(account):
    this_account_collection = get_account_collection(account)
    account_all_eigenvalue = DB_CONNECTOR.query_data(this_account_collection['eigenvalue'],{'userid':{'$ne':None}},{'value':1,'userid':1})
    FACE_COMPAROR_DICT[account] = Face_Comparor(account_all_eigenvalue) 

