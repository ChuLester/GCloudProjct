import gridfs
from utils import make_result_msg, get_account_collection
from schema import request_to_dict, collection_schema_dict
from model import DB_CONNECTOR
from datetime import datetime, timedelta
import logging
from error_code import error_code_dict
from bson.objectid import ObjectId


def _cal_working_hours(values):
    logging.info(values)
    account, workhour_dict, loss_argument = request_to_dict(
        values, collection_schema_dict['workhour'], is_include_account=True)

    # if loss_argument:
    #     return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    result_user_data = DB_CONNECTOR.query_data(
        'profile', {"account": account}, {"users": 1, "user_detail": 1})

    result_users = result_user_data[0]["users"]
    result_user_detail = result_user_data[0]["user_detail"]
    result_user_data = dict(zip(result_users, result_user_detail))

    if 'starttime' in workhour_dict.keys() and 'endtime' in workhour_dict.keys():
        starttime = datetime.strptime(workhour_dict['starttime'], "%Y/%m/%d")
        endtime = datetime.strptime(
            workhour_dict['endtime'], "%Y/%m/%d") + timedelta(days=1)
    else:
        endtime = datetime.today() + timedelta(days=1)
        starttime = endtime - timedelta(days=30)

    expression_list = []
    expression_list.append(
        {"$match": {"account": account, "user_object_id": {"$exists": True}, "status": {"$exists": True}}})
    # expression_list.append({"$project": {"status": "$status", "_id": "$_id",
    #                        "userid": "$userid", "date": {"$dateFromString": {"dateString": "$date"}}}})
    expression_list.append(
        {"$match": {"date": {"$gte": starttime, "$lte": endtime}}})
    expression_list.append({"$group": {"_id": "$user_object_id", "result_list": {
                           "$push": {"status": "$status", "date": "$date"}}}})
    expression_list.append({"$sort": {"result_list.date": 1}})

    result_record_data = DB_CONNECTOR.aggregate('record', expression_list)

    user_hour_dict = {}
    for user_clockin_doc in result_record_data:
        # print(user_clockin_doc)
        user_name = user_clockin_doc['_id']
        user_wage = result_user_data[user_name]['wage']
        detail_clockon_list, work_hours = cal_work_hours(
            user_clockin_doc['result_list'])

        user_hour_dict[user_name] = {
            'detail': detail_clockon_list, 'hours': work_hours, 'wage': user_wage}

    return make_result_msg(True, None, user_hour_dict)


def cal_work_hours(clockin_dict):
    Clock_On = None
    ClockOn_time = 0
    total_hours = 0
    detail_clockon_list = []
    for doc in clockin_dict:
        status = doc['status']
        date = doc['date']
        if status == 'ON':
            Clock_On = True
            ClockOn_time = date
        elif status == "OFF" and Clock_On:
            end_time = date
            start_time = ClockOn_time
            day_hours = (end_time.timestamp() -
                         start_time.timestamp()) // (60 * 30) / 2
            detail_clockon_list.append([start_time.strftime(
                "%Y/%m/%d %H:%M:%S"), end_time.strftime("%Y/%m/%d %H:%M:%S"), day_hours])
            total_hours = day_hours + total_hours
            Clock_On = False

    return detail_clockon_list, total_hours


def _get_user_record(values):
    logging.info(values)
    account, workhour_dict, loss_argument = request_to_dict(
        values, collection_schema_dict['workhour'], is_include_account=True)

    # if loss_argument:
    #     return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    if 'starttime' in workhour_dict.keys() and 'endtime' in workhour_dict.keys():
        starttime = datetime.strptime(workhour_dict['starttime'], "%Y/%m/%d")
        endtime = datetime.strptime(
            workhour_dict['endtime'], "%Y/%m/%d") + timedelta(days=1)
    else:
        endtime = datetime.today() + timedelta(days=1)
        starttime = endtime - timedelta(days=365)
    #print('start time : ', starttime)
    #print('end time : ', endtime)
    # result_user_data = DB_CONNECTOR.query_data(
    #     'profile', {"account": account}, {"users": 1, "user_detail": 1})

    # result_users = result_user_data[0]["users"]
    # result_user_detail = result_user_data[0]["user_detail"]
    # result_user_data = dict(zip(result_users, result_user_detail))

    # # result_record_data = DB_CONNECTOR.query_data('record', {'account': account, "date": {
    # #     "$gte": starttime, "$lt": endtime}, "status": {"$exists": True}, "user_object_id": {"$exists": True}}, {'_id': 0})

    expression_list = []
    expression_list.append({"$match": {"status": {"$exists": True}, "user_object_id": {
                           "$exists": True}, "account": account, "date": {"$gte": starttime, "$lt": endtime}}})
    expression_list.append({"$lookup": {
                           "from": 'eigenvalue', "localField": "eigenvalue", "foreignField": "_id", "as": "eigenvalue"}})
    expression_list.append({"$project": {
                           "user_object_id": 1, "cropimageid": '$eigenvalue.cropimageID', 'date': '$date', 'status': '$status'}})
    result_record_data = DB_CONNECTOR.aggregate('record', expression_list)

    fs = gridfs.GridFS(DB_CONNECTOR.db, 'image')

    if result_record_data is None:
        return make_result_msg(True, None, None)

    output = []

    for doc in result_record_data:
        raw_image = fs.get(doc['cropimageid'][0]).read()
        raw_image = str(raw_image)[1:]
        out_record = {
            'user': doc['user_object_id'],
            'date': doc['date'].strftime("%Y/%m/%d %H:%M:%S"),
            'status': doc['status'],
            'image': raw_image
        }
        output.append(out_record)

    return make_result_msg(True, result=output)


def _edit_user_record(values):
    logging.info(values)
    account, edit_record_dict, loss_argument = request_to_dict(
        values, collection_schema_dict['edit_record'], is_include_account=True)

    if loss_argument:
        return make_result_msg(False, error_msg=error_code_dict[601], result=loss_argument)

    origin_time = datetime.strptime(
        edit_record_dict['origin_time'], "%Y/%m/%d %H:%M:%S")
    edit_time = datetime.strptime(
        edit_record_dict['edit_time'], "%Y/%m/%d %H:%M:%S")

    result_record_data = DB_CONNECTOR.query_data('record', {'account': account, "date": origin_time,
                                                            "status": edit_record_dict['status'], "user_object_id": edit_record_dict['user']}, {'_id': 1})
    if result_record_data:
        if result_record_data.count() != 1:
            return make_result_msg(False, error_msg=error_code_dict[660], result=None)
        else:
            DB_CONNECTOR.update_data('record', {
                '_id': result_record_data[0]['_id']}, {'date': edit_time})
    else:
        return make_result_msg(False, error_msg=error_code_dict[660], result=None)

    return make_result_msg(True)
