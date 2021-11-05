import logging
import gridfs
from flask import Flask,request,Blueprint
from utils import make_result_msg,get_account_collection
from schema import request_to_dict,collection_schema_dict
from model import DB_CONNECTOR
from datetime import datetime

record_app = Blueprint('record',__name__)

@record_app.route('/cal_working_hours',methods = ['POST'])
def cal_working_hours():
    """
    input:
        account : company account's name
        starttime: set search start date.
        endtime: set search end date.
    output:
        status:
            True
        result:
            list:
                user : Num work hour.
        error_msg:
            None
    """
    logging.info('Call cal working hours.')
    if request.method == 'POST':
        result_string = _cal_working_hours(request.get_json())
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')
    
def _cal_working_hours(values):
    
    account,workhour_dict = request_to_dict(values,collection_schema_dict['workhour'],is_include_account=True)
    this_account_collection = get_account_collection(account)
    starttime = datetime.strptime(workhour_dict['starttime'],"%Y/%m/%d")
    endtime = datetime.strptime(workhour_dict['endtime'],"%Y/%m/%d")
    expression_list = []
    expression_list.append({"$project":{"status":"$status","_id":"$_id","userid":"$userid","date":{"$dateFromString":{"dateString":"$date"}}}})
    expression_list.append({"$match":{"date":{"$gte":starttime,"$lt":endtime}}})
    expression_list.append({"$group" : {"_id" : "$userid" ,"result_list" : {"$push" : {"status" : "$status","date" : "$date"}}}})
    expression_list.append({"$sort" : {"result_list.date" : 1}})
    expression_list.append({"$lookup" : {"from" : this_account_collection['user'] ,"localField" : "_id" ,"foreignField" : "_id" ,"as" : "user"}})
    result_data = DB_CONNECTOR.aggregate(this_account_collection['clockin'],expression_list)

    user_hour_dict = {}
    for user_clockin_doc in result_data:
        username = user_clockin_doc['user'][0]['name']
        work_hours = cal_work_hours(user_clockin_doc['result_list'])
        user_hour_dict[username] = work_hours

    return make_result_msg(True,None,user_hour_dict)
    
def cal_work_hours(clockin_dict):
    Clock_On = None
    ClockOn_time = 0
    total_hours = 0
    for doc in clockin_dict:
        status = doc['status']
        date = doc['date']
        if status == 'ON':
            Clock_On = True
            ClockOn_time = date
        elif status == "OFF" and Clock_On:
            end_time = date
            start_time = ClockOn_time
            total_hours = ((end_time - start_time).seconds) + total_hours
            Clock_On = False
    return total_hours // 3600     

@record_app.route('/get_user_record',methods = ['POST'])
def get_user_record():
    """
    input:
        account : company account's name
    output:
        if success:
            status : 
                True
            result:
                user : user name
                image : user face image
                date : clockin date
                status : NO / OFF
            error_msg:
                None
        else:
            status :
                False
            result:
                None
            error_msg:
                None
            
    """
    logging.info('Call user_record.')
    if request.method == 'POST':
        result_string = _get_user_record(request.get_json())
        return result_string
    else:
        return make_result_msg(False,error_msg='REQUEST FAILED')

def _get_user_record(values):

    account = values['account']
    this_account_collection = get_account_collection(account)
    
    expression_list = []
    expression_list.append({"$lookup":{"from":this_account_collection['user'],"localField":"userid","foreignField":"_id","as":"user"}})
    expression_list.append({"$lookup":{"from":this_account_collection['record'],"localField":"recordID","foreignField":"_id","as":"image"}})
    expression_list.append({"$project":{"date":1,"status":1,"user.name":1,"image.cropimageID":1}})
    result_data = DB_CONNECTOR.aggregate(this_account_collection['clockin'],expression_list)

    fs = gridfs.GridFS(DB_CONNECTOR.db,this_account_collection['image'])
    
    output = []
    for doc in result_data:
        del doc['_id']
        doc['user'] = doc['user'][0]['name']
        raw_image = fs.get(doc['image'][0]['cropimageID']).read()
        raw_image = str(raw_image)[1:]
        doc['image'] = raw_image
        output.append(doc)


    return make_result_msg(True,result=output)
