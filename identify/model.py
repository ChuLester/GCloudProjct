import gridfs
import logging
from bson.objectid import ObjectId
from utils import make_result_msg, extract_face, get_account_collection, reload_feature
from model import DB_CONNECTOR, FACE_COMPAROR_DICT
from core.face_process.face_comparor import Face_Comparor
from schema import request_to_dict, Clockin, eigenvalue_to_dict, Record, collection_schema_dict
from config import RecognizeConfig
from error_code import error_code_dict


def _clockin(values):
    logging.info(values)
    account, clockin_info, loss_argument = request_to_dict(
        values, collection_schema_dict['clockin'], is_include_account=True)

    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    clockin = Clockin(clockin_info)

    if clockin_info['status'] in ['ON', 'OFF']:

        eigenvalue_id = DB_CONNECTOR.query_data('record', {'_id': ObjectId(
            clockin.data['record_object_id'])}, {'eigenvalue': 1})[0]['eigenvalue']

        DB_CONNECTOR.update_data('eigenvalue', {'account': account,
                                 '_id': eigenvalue_id}, {'userid': clockin.data['user_object_id']})

        DB_CONNECTOR.update_data('record', {'_id': ObjectId(
            clockin.data['record_object_id'])}, clockin.data)
        print(clockin.data)

        return make_result_msg(True)
    else:
        return make_result_msg(False, error_code_dict[642])


def _identify(values):
    logging.info(values)
    account, identify_info, loss_argument = request_to_dict(
        values, collection_schema_dict['identify'], is_include_account=True)

    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    if account not in FACE_COMPAROR_DICT.keys():
        return make_result_msg(False, error_code_dict[621])

    if len(FACE_COMPAROR_DICT[account].eigenvalue_data_list) == 0:
        return make_result_msg(False, error_code_dict[641], None)

    encode_image = values['cropimage'].encode()

    fs = gridfs.GridFS(DB_CONNECTOR.db, 'image')

    landmarks = values['landmark']

    face_embedding = extract_face(encode_image, landmarks)

    if face_embedding == None:
        return make_result_msg(False, error_msg=error_code_dict[650])

    image_id = fs.put(encode_image)
    eigenvalue = eigenvalue_to_dict(None, face_embedding, image_id, account)
    userid, cosine_distance = FACE_COMPAROR_DICT[account].identify(
        face_embedding)

    if cosine_distance < RecognizeConfig['threshold']:
        insert_eigenvalue = DB_CONNECTOR.insert_data(
            'eigenvalue', eigenvalue).inserted_id

        record = Record(insert_eigenvalue, account)
        # print(record.data)

        insert_record_id = DB_CONNECTOR.insert_data(
            'record', record.data).inserted_id

        result_data = DB_CONNECTOR.query_data(
            'profile', {"account": account}, {"users": 1, "user_detail": 1})

        account_profile_users = result_data[0]['users']
        account_profile_user_detail = result_data[0]['user_detail']

        target_user_index = account_profile_users.index(userid)
        user_profile = account_profile_user_detail[target_user_index]

        match_user_cropimageid = user_profile['cropimageid']
        raw_image = fs.get(match_user_cropimageid).read()

        username = user_profile['name']
        logging.info('%s %f' % (username, cosine_distance))

        out_dict = {}
        out_dict['username'] = username
        out_dict['manager'] = user_profile['manager']
        out_dict['user_object_id'] = username
        out_dict['record_object_id'] = str(insert_record_id)
        out_dict['image'] = str(raw_image)[1:]
        return make_result_msg(True, error_msg=None, result=out_dict)
    else:
        return make_result_msg(False, error_msg=error_code_dict[640])


def _update_face_feature(values):
    logging.info(values)
    global DB_CONNECTOR
    account = values['account']
    this_account_collection = get_account_collection(account)

    # TODO face embedding clusting
    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {}, {'account': account})

    if the_same_docs:
        reload_feature(account)
        logging.info('account %s update face feature' % (account))
        return make_result_msg(True)
    else:
        return make_result_msg(False, error_msg=error_code_dict[611])
