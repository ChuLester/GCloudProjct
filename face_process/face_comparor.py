import numpy as np

def cosine_distance(v1,v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    v1 = v1.reshape(-1,256)
    v2 = v2.reshape(-1,256)
    n1 = v1.shape[0]
    n2 = v2.shape[0]
    norm1 = np.linalg.norm(v1,axis = 1).reshape(n1,1)
    norm2 = np.linalg.norm(v2,axis = 1).reshape(n2,1)
    similiry = v1.dot(v2.T) / norm1.dot(norm2.T)
    return 1 - similiry

class Face_Comparor:
    def __init__(self,eigenvalue_object_list):
        self.eigenvalue_data_list = []
        self.user_data_list = []
        self.build_to_list(eigenvalue_object_list)

    def build_to_list(self,eigenvalue_object_list):
        if eigenvalue_object_list == None:return
        for obj in eigenvalue_object_list:
            self.eigenvalue_data_list.append(obj['value'])
            self.user_data_list.append(obj['userid'])
        
        self.eigenvalue_data_list = np.array(self.eigenvalue_data_list).reshape(-1,256)
        # print(len(self.eigenvalue_data_list))
        
    def identify(self,searched_embedding):
        """
        args:
            searched_embedding: It's embeeding which be searched user face.
        
        return:
            userid : the most simility userid.
            distance: the most shortest cosine distance value.
        """
        searched_embedding = np.array(searched_embedding)
        cosine_distance_pairwise_matrix = cosine_distance(searched_embedding,self.eigenvalue_data_list).reshape(-1)
        min_idx = np.argmin(cosine_distance_pairwise_matrix)

        return self.user_data_list[min_idx],cosine_distance_pairwise_matrix[min_idx]
