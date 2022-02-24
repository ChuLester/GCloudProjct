import logging
from flask import Flask, request, Blueprint
from utils import make_result_msg
from record.model import _cal_working_hours, _get_user_record, _edit_user_record, _manual_update_record
from error_code import error_code_dict
record_app = Blueprint('record', __name__)


@record_app.route('/cal_working_hours', methods=['POST'])
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
        return make_result_msg(False, error_msg=error_code_dict[600])


@record_app.route('/get_user_record', methods=['POST'])
def get_user_record():
    """
    input:
        account : company account's name
        starttime: set search start date.
        endtime: set search end date.
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
    logging.info('Call get_user_record.')
    if request.method == 'POST':
        result_string = _get_user_record(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@record_app.route('/edit_user_record', methods=['POST'])
def edit_user_record():
    """
    input:
        account : company account's name
        user: user name.
        status: Original record clockin status : ON/OFF.
        origin_time: Original record clockin time.
        edit_time: Edit record clockin time.
    output:
        True,False

    """
    logging.info('Call edit_user_record.')
    if request.method == 'POST':
        result_string = _edit_user_record(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])


@record_app.route('/manual_update_record', methods=['POST'])
def manual_update_record():
    """
    input:
        account : company account's name
        record_object_id : record object id.
        user_object_id : user object id.
    output:
        True,False

    """
    logging.info('Call manual_update_record.')
    if request.method == 'POST':
        result_string = _manual_update_record(request.get_json())
        return result_string
    else:
        return make_result_msg(False, error_msg=error_code_dict[600])
