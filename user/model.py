import logging
import gridfs
from utils import get_account_collection, make_result_msg, extract_face, reload_feature
from model import DB_CONNECTOR, FACE_COMPAROR_DICT
from schema import User, request_to_dict, eigenvalue_to_dict, collection_schema_dict
from core.face_process.face_comparor import Face_Comparor
from error_code import error_code_dict


def _get_user_profile(values):
    global DB_CONNECTOR
    account = values['account']

    this_account_collection = get_account_collection(account)
    fs = gridfs.GridFS(DB_CONNECTOR.db, 'image')

    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'users': 1})

    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg=error_code_dict[611])

    result_data = the_same_docs[0]
    user_list = []
    for user_name in result_data.keys():
        user = result_data[user_name]
        user['cropimageid'] = str(fs.get(user['cropimageid']).read())[1:]
        user_list.append(user)

    return make_result_msg(True, None, user_list)


def _edit_user_profile(values):
    global DB_CONNECTOR
    account, user_dict = request_to_dict(
        values, collection_schema_dict['user'], is_include_account=True)
    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'account': 1})

    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg=error_code_dict[611])

    account_profile = the_same_docs[0]
    account_profile_users = account_profile['users']

    if user.data['name'] in account_profile_users.keys():

        if 'cropimage' in values.keys():
            fs = gridfs.GridFS(
                DB_CONNECTOR.db, 'image')
            encode_image = values['cropimage'].encode()
            image_id = fs.put(encode_image)
            user.update_image(image_id)

            landmarks = values['landmarks']
            face_embedding = extract_face(encode_image, landmarks)

            eigenvalue = eigenvalue_to_dict(
                user.data['name'], face_embedding, image_id, account)

            insert_eigenvalue = DB_CONNECTOR.insert_data(
                'eigenvalue', eigenvalue).inserted_id
    else:
        return make_result_msg(False, error_code_dict[631])

    account_profile_users[user.data['name']] = user.data
    DB_CONNECTOR.update_data('profile', {
        'account': account}, {'users': account_profile_users})

    return make_result_msg(True)


def _user_register(values):
    account, user_dict = request_to_dict(
        values, collection_schema_dict['user'], is_include_account=True)

    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'account': 1,
                                          'users': 1})

    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg=error_code_dict[611])

    account_profile = the_same_docs[0]
    account_proflie_users = account_profile['users']

    isValid, error_text = user.check(account_proflie_users.keys())
    if not(isValid):
        logging.warning(
            'front-end POST the same user in the account collection.')
        return make_result_msg(False, error_msg=error_text)

    fs = gridfs.GridFS(DB_CONNECTOR.db, 'image')
    encode_image = values['cropimage'].encode()
    image_id = fs.put(encode_image)
    user.update_image(image_id)

    account_proflie_users[user.data['name']] = user.data
    DB_CONNECTOR.update_data('profile', {'account': account}, {
                             'users': account_proflie_users})

    landmarks = values['landmarks']
    face_embedding = extract_face(encode_image, landmarks)
    eigenvalue = eigenvalue_to_dict(
        user.data['name'], face_embedding, image_id, account)

    # print(eigenvalue)
    insert_eigenvalue = DB_CONNECTOR.insert_data(
        'eigenvalue', eigenvalue).inserted_id
    reload_feature(account)
    return make_result_msg(True)
