import logging
from flask import Flask, request, Blueprint
from utils import make_result_msg
from record.model import _cal_working_hours, _get_user_record
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
        return make_result_msg(False, error_msg=error_code_dict[600])
