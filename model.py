from config import MongoConfig,InferenceConfig,RecognizeConfig
from core.db.mongo_connector import Connector
from core.face_process.inference_client import InferenceClient


global DB_CONNECTOR,INFERENCE_CLIENT,FACE_COMPAROR_DICT

DB_CONNECTOR = Connector(MongoConfig)
INFERENCE_CLIENT = InferenceClient(InferenceConfig)
FACE_COMPAROR_DICT = {}