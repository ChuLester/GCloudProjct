import tensorflow as tf
import cv2
import grpc
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
import tensorflow_serving
import numpy as np
from face_aligment import FaceAligment


class InferenceClient:
    def __init__(self,config = None):
        
        channel = grpc.insecure_channel('%s:%s'%(config['host'],config['port']))
        # print(channel)
        self.stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
        self.request = predict_pb2.PredictRequest()
        self.request.model_spec.name = config['model_name']
        self.request.model_spec.signature_name = 'serving_default'
        self.face_aligment = FaceAligment()

    def predict(self,input_image,landmarks):
        print(input_image.shape)
        print(landmarks)
        image = input_image
        image = self.face_aligment.aligment(image,landmarks)
        image = image.transpose((2,0,1))
        with tf.Session() as sess:
            tensor = tf.contrib.util.make_tensor_proto(image.astype(np.float32),shape = (1,3,150,150))
            self.request.inputs['0'].CopyFrom(tensor)
            response = self.stub.Predict(self.request,2.0)
            result = response.outputs['216']
            result = tf.make_ndarray(result)
        
        return result[0].tolist()