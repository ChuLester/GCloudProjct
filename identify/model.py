import gridfs
import logging
from bson.objectid import ObjectId
from utils import make_result_msg, extract_face, get_account_collection
from model import DB_CONNECTOR, FACE_COMPAROR_DICT
from core.face_process.face_comparor import Face_Comparor
from schema import request_to_dict, Clockin, eigenvalue_to_dict, Record, collection_schema_dict
from config import RecognizeConfig
from error_code import error_code_dict


def _clockin(values):
    account, clockin_info = request_to_dict(
        values, collection_schema_dict['clockin'], is_include_account=True)
    clockin = Clockin(clockin_info)

    this_account_collection = get_account_collection(account)

    if clockin_info['status'] in ['ON', 'OFF']:
        eigenvalue_id = DB_CONNECTOR.query_data(this_account_collection['record'], {'_id': ObjectId(
            clockin.data['recordID'])}, {'eigenvalue': 1}).__getitem__(0)['eigenvalue']
        DB_CONNECTOR.update_data(this_account_collection['eigenvalue'], {
                                 '_id': eigenvalue_id}, {'userid': clockin.data['userid']})
        insert_clockin_id = DB_CONNECTOR.insert_data(
            this_account_collection['clockin'], clockin.data)
        return make_result_msg(True)
    else:
        return make_result_msg(False, error_code_dict[642])


def _identify(values):
    account, identify_info = request_to_dict(
        values, collection_schema_dict['identify'], is_include_account=True)
    if account not in FACE_COMPAROR_DICT:
        return make_result_msg(False, error_code_dict[621])

    if len(FACE_COMPAROR_DICT[account].eigenvalue_data_list) == 0:
        return make_result_msg(False, error_code_dict[641], None)

    this_account_collection = get_account_collection(account)

    encode_image = values['cropimage'].encode()
    fs = gridfs.GridFS(DB_CONNECTOR.db, this_account_collection['image'])
    image_id = fs.put(encode_image)

    landmarks = values['landmarks']
    face_embedding = extract_face(encode_image, landmarks)
    eigenvalue = eigenvalue_to_dict(None, face_embedding, image_id)

    insert_eigenvalue = DB_CONNECTOR.insert_data(
        this_account_collection['eigenvalue'], eigenvalue).inserted_id
    record = Record(image_id, insert_eigenvalue)
    # print(record.data)

    insert_record_id = DB_CONNECTOR.insert_data(
        this_account_collection['record'], record.data).inserted_id
    out_dict = {}
    userid, cosine_distance = FACE_COMPAROR_DICT[account].identify(
        face_embedding)

    match_user_cropimageid = DB_CONNECTOR.query_data(
        this_account_collection['user'], {"_id": userid}, {"cropimageid": 1})
    raw_image = fs.get(match_user_cropimageid[0]['cropimageid']).read()

    if cosine_distance < RecognizeConfig['threshold']:
        # print(userid)
        result_query_data = DB_CONNECTOR.query_data(
            this_account_collection['user'], {'_id': userid}, {'name': 1, 'manager': 1})
        # print(result_query_data)
        username = result_query_data.__getitem__(0)['name']
        logging.info('%s %f' % (username, cosine_distance))
        out_dict['username'] = username
        out_dict['manager'] = result_query_data.__getitem__(0)['manager']
        out_dict['user_id'] = str(userid)
        out_dict['record_id'] = str(insert_record_id)
        out_dict['image'] = str(raw_image)[1:]
        return make_result_msg(True, error_msg=None, result=out_dict)
    else:

        return make_result_msg(False, error_msg=error_code_dict[640])


def _update_face_feature(values):
    global DB_CONNECTOR
    account = values['account']
    this_account_collection = get_account_collection(account)

    # TODO face embedding clusting

    if the_same_docs:
        the_same_docs = DB_CONNECTOR.query_data(
            'accounts', {}, {'account': account})

        account_all_eigenvalue = DB_CONNECTOR.query_data(
            this_account_collection['eigenvalue'], {}, {'value': 1, 'userid': 1})

        FACE_COMPAROR_DICT[account] = Face_Comparor(account_all_eigenvalue)
        logging.info('account %s update face feature' % (account))
        return make_result_msg(True)
    else:
        return make_result_msg(False, error_msg=error_code_dict[611])
