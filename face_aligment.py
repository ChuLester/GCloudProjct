import cv2
import numpy as np

class FaceAligment:
    def __init__(self):
        self.landmark_location_list = []
        self.landmark_location_list.append(np.array([46,45]))
        self.landmark_location_list.append(np.array([101,45]))
        self.landmark_location_list.append(np.array([0,0]))
        self.landmark_location_list = np.array(self.landmark_location_list)
        
        s60 = np.sin(60 * np.pi / 180)
        c60 = np.cos(60 * np.pi / 180)
        self.landmark_location_list[2][0] = c60 * (self.landmark_location_list[0][0] - self.landmark_location_list[1][0]) - s60 * (self.landmark_location_list[0][1] - self.landmark_location_list[1][1]) + self.landmark_location_list[1][0]
        self.landmark_location_list[2][1] = s60 * (self.landmark_location_list[0][0] - self.landmark_location_list[1][0]) - c60 * (self.landmark_location_list[0][1] - self.landmark_location_list[1][1]) + self.landmark_location_list[1][1]
    
    def aligment(self,face,landmark):
        landmark = np.array(landmark).reshape(-1,2)
        landmark = landmark[:2]
        s60 = np.sin(60 * np.pi / 180)
        c60 = np.cos(60 * np.pi / 180)
        landmark = np.concatenate((landmark,np.array([0,0]).reshape(-1,2)),axis = 0)
        
        landmark[2][0] = c60 * (landmark[0][0] - landmark[1][0]) - s60 * (landmark[0][1] - landmark[1][1]) + landmark[1][0]
        landmark[2][1] = s60 * (landmark[0][0] - landmark[1][0]) - c60 * (landmark[0][1] - landmark[1][1]) + landmark[1][1]
        M = cv2.estimateAffinePartial2D(landmark,self.landmark_location_list)
        
        return cv2.warpAffine(face,M[0],(150,150))