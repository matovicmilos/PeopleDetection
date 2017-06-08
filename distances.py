
import cv2
import numpy as np
import queue as q
from threading import Thread
import sys
from threading import Event

from frame import Frame

DEVICES = [0, 1]
ERROR = -1
FPS = 15
DONE = 1


def match_points(left, right):
    """
    Find points that represent the same person on both cameras

    Assumption based, only works if the same object is within +- 40px on both cameras
    this probably needs adjusting for objects that are further away
    """
    matched = []
    for left_point in left:
        for right_point in right:
            if abs(left_point[0] - right_point[0]) < 40 and abs(left_point[1] - right_point[1]) < 40:
                matched.append([left_point,right_point])
    return matched


def get_range(correlations, F, P1, P2):
    """
    Using the set of correlations produced by match_points, identify the distance of detected people in the scene.

    :param correlations: List of correlations, each element a list of one or more pairs of points, to use to
                         calculate distances
    :returns: A list with the distances for each correlated point.
    """

    all_dist = []

    for left_group, right_group in correlations:
        # multiple intersection points are provided, average out the distances
        left_corrected, right_corrected = cv2.correctMatches(F, np.array([[left_group]]).astype(float),
                                                             np.array([[right_group]]).astype(float))
        collection = cv2.triangulatePoints(P1, P2, left_corrected, right_corrected)
        triangulated = np.mean(collection, axis=1).reshape(4, 1)  # Average the results of the triangulation

        # print(left_group)
        # print(left_corrected)
        # print("before mean")
        # print(collection)
        # print(triangulated)

        # homo to normal coords by dividing by last element. squares are 25mm.
        # for some reason, was getting distances *10 of actual so divided the size of the square here by 10
        in_m = (triangulated[0:3] / triangulated[3]) * 0.0025
        x, y, z = (float(n) for n in in_m)

        # z <= 0 means behind the camera -- not actually possible.
        if z > 0:
            # euclidean distance in 3d space with known coords. camera would be (0,0,0)
            distance = (x ** 2 + y ** 2 + z ** 2) ** 0.5  # length of vector to get distance to object

            # reference the distance against the average of the intersection points for each image.
#             left_range[tuple(np.mean(left_group, axis=0))] = (distance, x, y, z)
#             right_range[tuple(np.mean(right_group, axis=0))] = (distance, x, y, z)
            all_dist.append(distance)
            print(distance)
            print("---------------")

    return all_dist


def finished(code):
    captures[0].release()
    captures[1].release()
    sys.exit(code)


def process_frames(cap, device):
    """
    Reads frame from the capture, detects people and displays the processed frame with distances

    :param device: integer indicating device number 0 - left camera, 1 - right camera
    :param cap: OpenCV VideoCapture object
    :return: None
    """
    while 1:
        ret, captured_frame = cap.read()
        # frame read ok
        if ret:
            frame = Frame(captured_frame)
            detection_points = frame.detect_people()
            # if people were found, we first check which thread it is then use corresponding queue to pass the points
            # to the main
            if len(detection_points) > 0:
                # left camera
                if device == DEVICES[0]:
                    left_q.put(detection_points)
                # right camera
                else:
                    right_q.put(detection_points)
            # if no people were found, we need to pass the 0 to main in order to be able to get a response and continue
            # displaying frame without distance
            else:
                if device == DEVICES[0]:
                    left_q.put(0)
                else:
                    right_q.put(0)
            # get message from the main, if matching points were found between the 2 threads, this will contain the
            # distances of people
            dist = main_q.get()
            if dist == DONE:
                cv2.destroyAllWindows()
                left_q.put(DONE)
                right_q.put(DONE)
                return None
            # write the distance if matches were found
            elif dist != 0:
                for j in range(len(dist)):
                    frame.write_distance(detection_points[j], dist[j])
            # draw the rest of the stuff in any case
            frame.draw_boundaries()
            frame.write_time()
            # pick window
            if device == DEVICES[0]:
                frame.show("left")
            else:
                frame.show("right")
            if cv2.waitKey(int(1000 / FPS)) & 0xFF == ord('q'):
                left_q.put(DONE)
                right_q.put(DONE)

        # failed to read frame
        else:
            print("Couldn't read frame.")
            left_q.put(DONE)
            right_q.put(DONE)


# load all the matrices we got from calibration
F = np.loadtxt(open("stereo_F.txt"))
E = np.loadtxt(open("stereo_E.txt"))
R = np.loadtxt(open("stereo_R.txt"))
T = np.loadtxt(open("stereo_T.txt"))
camera_matrix1 = np.loadtxt("device_0_mtx.txt")
camera_matrix2 = np.loadtxt("device_1_mtx.txt")
dist_coef1 = np.loadtxt("device_0_dist.txt")
dist_coef2 = np.loadtxt("device_1_dist.txt")
image_size = (640, 480)

# to get projection matrices P, as they are needed for triangulation
R1, R2, P1, P2, _, _, _ = cv2.stereoRectify(camera_matrix1, dist_coef1, camera_matrix2,dist_coef2, image_size, R, T,
                                            alpha=0)

captures = []
# start capture on both cameras, set the frame rate to 15 and set capture in grayscale
# lowering the frame rate is necessary if it is a cheap "3D" camera - eg. 2 cams on 1 usb port not enough bandwidth
captures.append(cv2.VideoCapture(DEVICES[0]))
captures[0].set(5, FPS)
captures[0].set(12, 0)
captures.append(cv2.VideoCapture(DEVICES[1]))
captures[1].set(5, FPS)
captures[1].set(12, 0)
dropped_frames = 0


left_q = q.Queue()
right_q = q.Queue()
main_q = q.Queue()

if captures[0].isOpened() and captures[1].isOpened():

    for i in range(len(DEVICES)):
        cam_thread = Thread(target=process_frames, args=(captures[i], DEVICES[i]))
        cam_thread.daemon = True
        cam_thread.start()

    while 1:

        points_left = left_q.get()
        points_right = right_q.get()
        if points_left == DONE or points_right == DONE:
            print("Exiting...")
            main_q.put(DONE)
            main_q.put(DONE)
            left_done = left_q.get()
            right_done = right_q.get()
            finished(0)
        elif points_left != 0 and points_right != 0:
            matched = match_points(points_left, points_right)
            if len(matched) > 0:
                distances = get_range(matched, F, P1, P2)
                main_q.put(distances)
                main_q.put(distances)
            else:
                main_q.put(0)
                main_q.put(0)
        else:
            main_q.put(0)
            main_q.put(0)

print("Couldnt start capture. Exiting...")
finished(ERROR)

