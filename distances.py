
# coding: utf-8

# In[7]:

import cv2
import numpy as np
import os
from frame import Frame


# In[8]:

def match_points(left,right):
    '''
    Find points that represent the same person on both cameras

    Assumption based, only works if the same object is within +- 10px on both cameras
    this probably needs adjusting for objects that are further away
    '''
    matched = []
    for left_point in left:
        for right_point in right:
            if abs(left_point[0] - right_point[0]) < 40 and abs(left_point[1] - right_point[1]) < 40:
                matched.append([left_point,right_point])
    return matched
                
        
        


# In[9]:

def get_range(correlations, F, P1, P2):
    """
    Using the set of correlations produced by correlate_lines, identify the range of the lines in the scene.

    :param correlations: List of correlations, each element a list of one or more pairs of points, to use to
                         calculate distances
    :returns: A dict, keyed by correlation, with the distances for each correlated point.
    """

    # The results are indexed against the points in both left and right images for ease of display
    #left_range, right_range = {}, {}
    all_dist = []

    for left_group, right_group in correlations:
        # multiple intersection points are provided, average out the distances
        #left_corrected, right_corrected = cv2.correctMatches(F,np.reshape(np.array([left_group]),(1,len([left_group]),2)) , 
        #                                                     np.reshape(np.array([right_group]),(1,len([right_group]),2)))
        left_corrected, right_corrected = cv2.correctMatches(F, np.array([[left_group]]).astype(float),
                                                             np.array([[right_group]]).astype(float))
        collection = cv2.triangulatePoints(P1, P2, left_corrected, right_corrected)
        triangulated = np.mean(collection, axis=1).reshape(4, 1)  # Average the results of the triangulation
        
        print(left_group)
        print(left_corrected)
        print("before mean")
        print(collection)
        
        #triangulated = collection[:, 0]
        
        print(triangulated)
        
        
        
        # homo to normal coords by dividing by last element. squares are 25mm.
        in_mm = (triangulated[0:3] / triangulated[3]) * 0.0025
        x, y, z = (float(n) for n in in_mm)

        # z <= 0 means behind the camera -- not actually possible.
        if z > 0:
            #euclidean distance in 3d space with known coords. camera would be (0,0,0)
            distance = (x ** 2 + y ** 2 + z ** 2) ** 0.5  # length of vector to get distance to object

            # reference the distance against the average of the intersection points for each image.
#             left_range[tuple(np.mean(left_group, axis=0))] = (distance, x, y, z)
#             right_range[tuple(np.mean(right_group, axis=0))] = (distance, x, y, z)
            all_dist.append(distance)
            print(distance)
            print("---------------")

    return all_dist


# In[10]:

F = np.loadtxt(open("stereo_F.txt"))
E = np.loadtxt(open("stereo_E.txt"))
R = np.loadtxt(open("stereo_R.txt"))
T = np.loadtxt(open("stereo_T.txt"))


# In[11]:

camera_matrix1 = np.loadtxt("device_0_mtx.txt")
camera_matrix2 = np.loadtxt("device_1_mtx.txt")
dist_coef1 = np.loadtxt("device_0_dist.txt")
dist_coef2 = np.loadtxt("device_1_dist.txt")
image_size = (640,480)

R1 = np.ndarray((3,3),dtype = float)
R2 = np.ndarray((3,3),dtype = float)
P1 = np.ndarray((3,4),dtype = float)
P2 = np.ndarray((3,4),dtype = float)

R1,R2,P1,P2,_,_,_ = cv2.stereoRectify(camera_matrix1,dist_coef1, camera_matrix2,dist_coef2, image_size, R, T,alpha = 0)


# In[12]:

left = cv2.VideoCapture(0)
left.set(5, 15)
left.set(12, 0)
right = cv2.VideoCapture(1)
right.set(5, 15)
right.set(12, 0)

if left.isOpened() and right.isOpened():
    while 1:
        ret1, lcap_frame = left.read()
        ret2, rcap_frame = right.read()
        if ret1 and ret2:
            lframe = Frame(lcap_frame)
            rframe = Frame(rcap_frame)
            points_left = lframe.detect_people()
            points_right = rframe.detect_people()
            lframe.draw_boundaries()
            rframe.draw_boundaries()
            lframe.write_time()
            rframe.write_time()
            matched = match_points(points_left,points_right)
            if len(matched) > 0:
                print(matched)
                distances = get_range(matched,F,P1,P2)
                for i in range(len(distances)):
                    lframe.write_distance(matched[i][0], distances[i])
                    rframe.write_distance(matched[i][1], distances[i])
            lframe.show('left')
            rframe.show('right')
        if cv2.waitKey(50) & 0xFF == ord('q'):
            print('Exiting...')
            break
cv2.destroyAllWindows()
left.release()
right.release()


# In[ ]:




# In[ ]:



