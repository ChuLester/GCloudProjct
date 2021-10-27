import json

def make_result_msg(status,error_msg = None,result = None):
    out = {}
    out['status'] = status
    out['error_msg'] = error_msg
    out['result'] = result
    return json.dumps(out)