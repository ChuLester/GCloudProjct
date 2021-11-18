import logging
import pymongo
import gridfs
import json
import time


class Connector:
    def __init__(self, db_connect_config):
        self.client = pymongo.MongoClient(
            db_connect_config['host'], connect=False)
        self.db = self.client[db_connect_config['cloud_face_db']]
        self.fs = None

    def disconnect(self):
        self.client.close()

    def insert_data(self, collection_name, data_dict):
        if self.is_collection_exist(collection_name):
            collection = self.db[collection_name]
            insert_objectID = collection.insert_one(data_dict)
            logging.info('%s collection insert data %s' %
                         (collection_name, str(insert_objectID)))
            return insert_objectID
        else:
            return None

    def query_data(self, collection_name, query_condition={}, visable_cols={}):
        if self.is_collection_exist(collection_name):
            collection = self.db[collection_name]
            result_query_documents = collection.find(
                query_condition, visable_cols)

            logging.info('%s collection query' % (collection_name))
            if result_query_documents.count():
                return result_query_documents
            else:
                return None

    def upload_file(self, collection_name, file):
        if self.is_collection_exist(collection_name):
            if type(data) == str:
                data = data.encode()
            self.fs = gridfs.GridFS(self.db, collection_name)
            insert_objectID = self.fs.put(data)
            logging.info('%s collection upload file, insertID %s' %
                         (collection_name, str(insert_objectID)))

            return insert_objectID
        else:
            return None

    def is_collection_exist(self, collection_name):
        if collection_name in self.db.list_collection_names():
            return True
        else:
            return False

    def create_collection(self, collection_name):
        self.db.create_collection(collection_name)
        logging.info('Create collection : %s' % (collection_name))

    def update_data(self, collection_name, query_dict, update_dict):
        collection = self.db[collection_name]
        collection.update_one(query_dict, {"$set": update_dict})
        logging.info('update %s collection data, from %s to %s' %
                     (collection_name, str(query_dict), str(update_dict)))

    def delete_data(self, collection_name, del_dict):
        collection = self.db[collection_name]
        collection.delete_one(del_dict)
        logging.info('Delete data from %s collection where %s' %
                     (collection_name, del_dict))

    def drop_collection(self, collection_name):
        collection = self.db[collection_name]
        collection.drop()
        logging.info('Drop %s collection' % (collection_name))

    def aggregate(self, collection_name, expression_list):
        collection = self.db[collection_name]
        return collection.aggregate(expression_list)
