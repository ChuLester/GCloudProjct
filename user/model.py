import logging
import gridfs
from utils import get_account_collection, make_result_msg, extract_face, reload_feature
from model import DB_CONNECTOR, FACE_COMPAROR_DICT
from schema import User, request_to_dict, eigenvalue_to_dict, collection_schema_dict
from core.face_process.face_comparor import Face_Comparor


def _get_user_profile(values):
    global DB_CONNECTOR
    account = values['account']

    this_account_collection = get_account_collection(account)
    fs = gridfs.GridFS(DB_CONNECTOR.db, this_account_collection['image'])

    result_data = DB_CONNECTOR.query_data(
        this_account_collection['user'], {}, {'_id': 0})

    user_list = []
    for doc in result_data:
        user = doc
        user['cropimageid'] = str(fs.get(user['cropimageid']).read())[1:]
        user_list.append(user)

    return make_result_msg(True, None, user_list)


def _edit_user_profile(values):
    global DB_CONNECTOR
    account, user_dict = request_to_dict(
        values, collection_schema_dict['user'], is_include_account=True)
    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'accounts', {'account': account}, {'account': 1})

    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg='Account was not register.')

    this_account_collection = get_account_collection(account)
    the_same_user_docs = DB_CONNECTOR.query_data(this_account_collection['user'], {
                                                 'name': user_dict['name']}, {})

    if the_same_user_docs:
        user_id = the_same_user_docs[0]['_id']
        if 'cropimage' in values.keys():
            fs = gridfs.GridFS(
                DB_CONNECTOR.db, this_account_collection['image'])
            encode_image = values['cropimage'].encode()
            image_id = fs.put(encode_image)
            user.update_image(image_id)

            landmarks = values['landmarks']
            face_embedding = extract_face(encode_image, landmarks)
            eigenvalue = eigenvalue_to_dict(user_id, face_embedding, image_id)
            insert_eigenvalue = DB_CONNECTOR.insert_data(
                this_account_collection['eigenvalue'], eigenvalue).inserted_id
    else:
        return make_result_msg(False, 'No match user.')

    DB_CONNECTOR.update_data(this_account_collection['user'], {
                             '_id': user_id}, user.data)
    return make_result_msg(True)


def _user_register(values):
    account, user_dict = request_to_dict(
        values, collection_schema_dict['user'], is_include_account=True)
    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'accounts', {'account': account}, {'account': 1})
    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg='Account was not register.')
    this_account_collection = get_account_collection(account)

    all_user_docs = DB_CONNECTOR.query_data(
        this_account_collection['user'], {}, {'name': 1})

    if all_user_docs:
        all_user_list = [doc['name'] for doc in all_user_docs]
    else:
        all_user_list = []
    # print(all_user_list)
    isValid, error_text = user.check(all_user_list)
    if not(isValid):
        logging.warning(
            'front-end POST the same user in the account collection.')
        return make_result_msg(False, error_msg=error_text)

    fs = gridfs.GridFS(DB_CONNECTOR.db, this_account_collection['image'])
    encode_image = values['cropimage'].encode()
    image_id = fs.put(encode_image)
    user.update_image(image_id)

    user_insert_id = DB_CONNECTOR.insert_data(
        this_account_collection['user'], user.data).inserted_id

    landmarks = values['landmarks']
    face_embedding = extract_face(encode_image, landmarks)
    eigenvalue = eigenvalue_to_dict(user_insert_id, face_embedding, image_id)
    # print(eigenvalue)
    insert_eigenvalue = DB_CONNECTOR.insert_data(
        this_account_collection['eigenvalue'], eigenvalue).inserted_id
    reload_feature(account)
    return make_result_msg(True)
