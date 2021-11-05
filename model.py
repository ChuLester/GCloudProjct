from config import MongoConfig,InferenceConfig,RecognizeConfig
from face_comparor import Face_Comparor
from mongo_connector import Connector
from inference_client import InferenceClient

global DB_CONNECTOR,INFERENCE_CLIENT,FACE_COMPAROR_DICT

DB_CONNECTOR = Connector(MongoConfig)
INFERENCE_CLIENT = InferenceClient(InferenceConfig)
FACE_COMPAROR_DICT = {}