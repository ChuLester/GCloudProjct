import gridfs
from utils import make_result_msg, get_account_collection
from schema import request_to_dict, collection_schema_dict
from model import DB_CONNECTOR
from datetime import datetime


def _cal_working_hours(values):

    account, workhour_dict = request_to_dict(
        values, collection_schema_dict['workhour'], is_include_account=True)

    result_user_data = DB_CONNECTOR.query_data(
        'record', {"account": account}, {"users": 1})

    result_user_data = result_user_data[0]["users"]

    starttime = datetime.strptime(workhour_dict['starttime'], "%Y/%m/%d")
    endtime = datetime.strptime(workhour_dict['endtime'], "%Y/%m/%d")
    expression_list = []
    expression_list.append(
        {"$match": {"account": account, "user_id": {"$exists": True}, "status": {"$exists": True}}})
    expression_list.append({"$project": {"status": "$status", "_id": "$_id",
                           "userid": "$userid", "date": {"$dateFromString": {"dateString": "$date"}}}})
    expression_list.append(
        {"$match": {"date": {"$gte": starttime, "$lt": endtime}}})
    expression_list.append({"$group": {"_id": "$userid", "result_list": {
                           "$push": {"status": "$status", "date": "$date"}}}})
    expression_list.append({"$sort": {"result_list.date": 1}})

    result_record_data = DB_CONNECTOR.aggregate('record', expression_list)

    user_hour_dict = {}
    for user_clockin_doc in result_record_data:
        user_name = user_clockin_doc['userid']
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
            day_hours = ((end_time - start_time).seconds) // (60 * 30)
            detail_clockon_list.append([start_time, end_time, day_hours])
            total_hours = day_hours + total_hours
            Clock_On = False

    return detail_clockon_list, total_hours


def _get_user_record(values):

    account, workhour_dict = request_to_dict(
        values, collection_schema_dict['workhour'], is_include_account=True)

    if 'starttime' in workhour_dict.keys() and 'endtime' in workhour_dict.keys():
        starttime = datetime.strptime(workhour_dict['starttime'], "%Y/%m/%d")
        endtime = datetime.strptime(workhour_dict['endtime'], "%Y/%m/%d")
    else:
        endtime = datetime.today()
        starttime = endtime - datetime.timedelta(days=30)

    result_user_data = DB_CONNECTOR.query_data(
        'profile', {"account": account}, {"users": 1})

    result_user_data = result_user_data[0]["users"]

    result_record_data = DB_CONNECTOR.query_data('record', {'account': account, "date": {
        "$gte": starttime, "$lt": endtime}, "status": {"$exists": True}, "username": {"$exists": True}}, {'_id': 0})

    fs = gridfs.GridFS(DB_CONNECTOR.db, 'image')

    output = []
    for doc in result_record_data:
        raw_image = fs.get(
            result_user_data[doc['username']]['cropimageID']).read()
        raw_image = str(raw_image)[1:]
        out_record = {
            'user': doc['username'],
            'date': doc['date'],
            'status': doc['status'],
            'image': raw_image
        }
        output.append(out_record)

    return make_result_msg(True, result=output)
