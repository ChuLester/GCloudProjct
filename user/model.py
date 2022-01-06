import logging
import gridfs
from utils import get_account_collection, make_result_msg, extract_face, reload_feature
from model import DB_CONNECTOR, FACE_COMPAROR_DICT
from schema import User, request_to_dict, eigenvalue_to_dict, collection_schema_dict
from core.face_process.face_comparor import Face_Comparor
from error_code import error_code_dict
from config import PayConfig


def _get_user_profile(values):
    logging.info(values)
    global DB_CONNECTOR
    account = values['account']
    fs = gridfs.GridFS(DB_CONNECTOR.db, 'image')

    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'users': 1, 'user_detail': 1})

    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg=error_code_dict[611])

    result_data = the_same_docs[0]
    result_data = dict(zip(result_data['users'], result_data['user_detail']))
    user_list = []
    for user_name in result_data.keys():
        user = result_data[user_name]
        print(user)
        user['face'] = str(fs.get(user['cropimageid']).read())[1:]
        del user['cropimageid']
        user_list.append(user)

    return make_result_msg(True, None, user_list)


def _edit_user_profile(values):
    logging.info(values)
    global DB_CONNECTOR
    account, user_dict, loss_argument = request_to_dict(
        values, collection_schema_dict['edituser'], is_include_account=True)

    if 'wage' in loss_argument:
        user_dict['wage'] = PayConfig['wage']
        loss_argument.remove('wage')

    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'account': 1, 'users': 1, 'user_detail': 1})

    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg=error_code_dict[611])

    account_profile = the_same_docs[0]
    account_profile_users = account_profile['users']
    account_profile_user_detail = account_profile['user_detail']

    if user.data['name'] in account_profile_users:
        target_user_index = account_profile_users.index(user.data['name'])
        if 'face' in values.keys():
            fs = gridfs.GridFS(
                DB_CONNECTOR.db, 'image')
            encode_image = values['user'].encode()
            image_id = fs.put(encode_image)
            user.update_image(image_id)

            landmarks = values['landmark']
            face_embedding = extract_face(encode_image, landmarks)

            eigenvalue = eigenvalue_to_dict(
                user.data['name'], face_embedding, image_id, account)

            insert_eigenvalue = DB_CONNECTOR.insert_data(
                'eigenvalue', eigenvalue).inserted_id
        else:

            user_ori_imageid = account_profile_user_detail[target_user_index]['cropimageid']
            user.update_image(user_ori_imageid)
    else:
        return make_result_msg(False, error_code_dict[631])

    target_user_index = account_profile_users.index(user.data['name'])
    account_profile_user_detail[target_user_index] = user.data

    DB_CONNECTOR.update_data('profile', {
        'account': account}, {'user_detail': account_profile_user_detail})

    return make_result_msg(True)


def _user_register(values):
    logging.info(values)
    account, user_dict, loss_argument = request_to_dict(
        values, collection_schema_dict['user'], is_include_account=True)

    if 'wage' in loss_argument:
        user_dict['wage'] = PayConfig['wage']
        loss_argument.remove('wage')

    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    del user_dict['face']

    user = User(user_dict)
    the_same_docs = DB_CONNECTOR.query_data(
        'profile', {'account': account}, {'account': 1,
                                          'users': 1,
                                          'user_detail': 1})

    if not(the_same_docs):
        logging.warning('Account was not register.')
        return make_result_msg(False, error_msg=error_code_dict[611])

    account_profile = the_same_docs[0]
    account_profile_users = account_profile['users']
    account_profile_user_detail = account_profile['user_detail']

    isValid, error_text = user.check(account_profile_users)
    if not(isValid):
        logging.warning(
            'front-end POST the same user in the account collection.')
        return make_result_msg(False, error_msg=error_text)

    fs = gridfs.GridFS(DB_CONNECTOR.db, 'image')
    encode_image = values['face'].encode()

    landmarks = values['landmark']
    print(landmarks)
    face_embedding = extract_face(encode_image, landmarks)

    if face_embedding == None:
        return make_result_msg(False, error_msg=error_code_dict[650])

    image_id = fs.put(encode_image)

    eigenvalue = eigenvalue_to_dict(
        user.data['name'], face_embedding, image_id, account)

    # print(eigenvalue)
    insert_eigenvalue = DB_CONNECTOR.insert_data(
        'eigenvalue', eigenvalue).inserted_id

    user.update_image(image_id)

    account_profile_users.append(user.data['name'])
    account_profile_user_detail.append(user.data)
    DB_CONNECTOR.update_data('profile', {'account': account}, {
                             'users': account_profile_users,
                             'user_detail': account_profile_user_detail})

    reload_feature(account)
    return make_result_msg(True)
