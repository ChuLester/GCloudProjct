from bson.objectid import ObjectId

def request_to_dict(values,collection_schema,is_include_account = False):
    out_dict = {}
    for key in collection_schema:
        if key in values.keys():
            out_dict[key] = values[key]
    if is_include_account:
        return values['account'] ,out_dict
    else:    
        return out_dict

class Account:
    def __init__(self,data_dict):
        self.data = data_dict    
        self.max_len = 12
        self.min_len = 6

    def registe_check(self,all_account_list):
        checker = True
        error_text = ''

        checker,error_text = self.check_account(all_account_list)
        if not(checker):return [checker,error_text]

        checker,error_text = self.check_password()
        if not(checker):return [checker,error_text]

        return [True,'Account registe successfully']

    def check_account(self,all_account_list):
        if self.data['account'] in all_account_list:
            return [False, 'Account is already registed']
        else:
            return [True, '']

    def check_password(self):
        password = self.data['password']
        if len(password) >= self.max_len or len(password) < self.min_len:
            return [False, 'Password length is invalid']

        return [True, '']

    def check_email(self):
        pass

    def check_third(self):
        pass

class User:
    def __init__(self,data_dict):
        self.data = data_dict
    
    def check(self,all_user_list):
        isValid = True
        error_msg = ''

        isValid, error_msg = self.check_is_not_exist(all_user_list)
        if not(isValid):return [isValid,error_msg]
        
        return [True, 'success']

    def check_is_not_exist(self,all_user_list):
        if all_user_list == None:return [True,'']
        if self.data['name'] in all_user_list:
            return [False, 'user is exist']
        else:
            return [True, '']

    def update_image(self,imageid):
        self.data['cropimageid'] = imageid

class Eigenvalue:
    def __init__(self,data_dict):
        self.data = data_dict

class Clockin:
    def __init__(self,data_dict):
        self.data = data_dict
        self.objectid_construct()
    
    def objectid_construct(self):
        self.data['userid'] = ObjectId(self.data['userid'])
        self.data['recordID'] = ObjectId(self.data['recordID'])

class Record:
    def __init__(self,imageid,eigenvalue):
        self.data = {}
        self.data['cropimageID'] = imageid
        self.data['eigenvalue'] = eigenvalue

def eigenvalue_to_dict(userid,value,imageid):
    out_dict = {}
    out_dict['userid'] = userid
    out_dict['value'] = value
    out_dict['cropimageID'] = imageid
    return out_dict

collection_schema_dict = {}
collection_schema_dict['account'] = ['_id','account','password','mail','workspace','third_party']
collection_schema_dict['user'] = ['_id','name','phone','mail','sex','birthday','manager','face']
collection_schema_dict['eigenvalue'] = ['_id','userid','value','cropimageID']
collection_schema_dict['record'] = ['_id','cropimageID','eigenvalue']
collection_schema_dict['clockin'] = ['_id','userid','date','recordID','status']
collection_schema_dict['image'] = ['_id','file']
collection_schema_dict['login'] = ['account','password']
collection_schema_dict['logout'] = ['account']
collection_schema_dict['identify'] = ['cropimage']
collection_schema_dict['workhour'] = ['starttime','endtime']


