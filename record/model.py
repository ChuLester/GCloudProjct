import gridfs
from utils import make_result_msg, get_account_collection
from schema import request_to_dict, collection_schema_dict
from model import DB_CONNECTOR
from datetime import datetime


def _cal_working_hours(values):

    account, workhour_dict = request_to_dict(
        values, collection_schema_dict['workhour'], is_include_account=True)
    this_account_collection = get_account_collection(account)
    starttime = datetime.strptime(workhour_dict['starttime'], "%Y/%m/%d")
    endtime = datetime.strptime(workhour_dict['endtime'], "%Y/%m/%d")
    expression_list = []
    expression_list.append({"$project": {"status": "$status", "_id": "$_id",
                           "userid": "$userid", "date": {"$dateFromString": {"dateString": "$date"}}}})
    expression_list.append(
        {"$match": {"date": {"$gte": starttime, "$lt": endtime}}})
    expression_list.append({"$group": {"_id": "$userid", "result_list": {
                           "$push": {"status": "$status", "date": "$date"}}}})
    expression_list.append({"$sort": {"result_list.date": 1}})
    expression_list.append({"$lookup": {
                           "from": this_account_collection['user'], "localField": "_id", "foreignField": "_id", "as": "user"}})
    result_data = DB_CONNECTOR.aggregate(
        this_account_collection['clockin'], expression_list)

    user_hour_dict = {}
    for user_clockin_doc in result_data:
        user_name = user_clockin_doc['user'][0]['name']
        user_wage = user_clockin_doc['user'][0]['wage']
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
    this_account_collection = get_account_collection(account)

    if 'starttime' in workhour_dict.keys() and 'endtime' in workhour_dict.keys():
        starttime = datetime.strptime(workhour_dict['starttime'], "%Y/%m/%d")
        endtime = datetime.strptime(workhour_dict['endtime'], "%Y/%m/%d")
    else:
        endtime = datetime.today()
        starttime = endtime - datetime.timedelta(days=30)

    expression_list = []
    expression_list.append(
        {"$match": {"date": {"$gte": starttime, "$lt": endtime}}})
    expression_list.append({"$lookup": {
                           "from": this_account_collection['user'], "localField": "userid", "foreignField": "_id", "as": "user"}})
    expression_list.append({"$lookup": {
                           "from": this_account_collection['record'], "localField": "recordID", "foreignField": "_id", "as": "image"}})
    expression_list.append({"$project": {
                           "date": 1, "status": 1, "user.name": 1, "image.cropimageID": 1}})
    result_data = DB_CONNECTOR.aggregate(
        this_account_collection['clockin'], expression_list)

    fs = gridfs.GridFS(DB_CONNECTOR.db, this_account_collection['image'])

    output = []
    for doc in result_data:
        del doc['_id']
        doc['user'] = doc['user'][0]['name']
        raw_image = fs.get(doc['image'][0]['cropimageID']).read()
        raw_image = str(raw_image)[1:]
        doc['image'] = raw_image
        output.append(doc)

    return make_result_msg(True, result=output)
