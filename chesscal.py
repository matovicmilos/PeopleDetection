import numpy as np
import cv2
import time
import sys
import threading

CALIBRATION_COUNT = 50
CORNERS_W, CORNERS_H = 9, 6
DEVICES = [0, 1]

timer = None

def process_frame(device, img):
    """ Process the captured frame, appending to the img_points array.

        Returns: The corners, if found. Else, None.
    """

    global timer

    # Name of the window to draw things in to
    window = 'img-{}'.format(device)

    # img = cv2.flip(img, -1)  # Camera returns images that are inverted on both axis -- flip 'em.
    img = cv2.GaussianBlur(img, (3, 3), 0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    found, corners = cv2.findChessboardCorners(gray, (CORNERS_W, CORNERS_H), None)

    if found:
        # Refine the corners and add
        refined_corners = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1),
                                           criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 150, 0.0001))

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (CORNERS_H, CORNERS_W), refined_corners, found)
        cv2.imshow(window, img)

        return refined_corners
    else:
        cv2.imshow(window, gray)  # show the gray image if no corners were located
        return None


# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
# Object Points. Used in calibrateCamera. Basically a whole set of dummy values.
# Count up from (0, 0, 0), (1, 0, 0), ... (9, 7, 0)
dummy_points = np.zeros((CORNERS_H * CORNERS_W, 3), np.float32)
for h in range(CORNERS_H):
    for w in range(CORNERS_W):
        index = w + (h * CORNERS_W)
        dummy_points[index][0] = w
        dummy_points[index][1] = h

# Collect data from both cameras at once
img_points = {}
obj_points = []  # the dummy obj_points array, one per img_points element
vidcaps = {}
for device in DEVICES:
    cap = cv2.VideoCapture(device)
    cap.set(5, 15)  # Limit FPS. Need to limit lower if using both cameras at once.
    #cap.set(10, 0.3)  # Brightness
    #cap.set(11, 0.4)  # Contrast
    cap.set(12, 0)  # Saturation to 0 - capture in greyscale.
    vidcaps[device] = cap
    img_points[device] = []  # 2d points in image plane. One per device.

first = True
skip_frames = 0  # A number of frames are skipped after a successful detection to give time to move
while all(len(pts) <= CALIBRATION_COUNT for pts in img_points.values()):
    # Capture frames with no processing so they're as close together as possible
    frames = {}
    for device in DEVICES:
        ok, img = vidcaps[device].read()
        if not ok:
            raise Exception("Error reading from device {}".format(device))

        frames[device] = img

    # Dump frames
    if skip_frames > 0:
        skip_frames -= 1

        for device in DEVICES:
            img = cv2.putText(frames[device], str(skip_frames), (120, 120), cv2.FONT_HERSHEY_DUPLEX, 4, (32, 32, 255), 3)
            cv2.imshow('img-{}'.format(device), frames[device])
        cv2.waitKey(10)

        continue

    # Now process them
    found_points = {}
    for device in DEVICES:
        img = frames[device]

        # Try to identify some corners
        corners = process_frame(device, img)
        if corners is not None:
            found_points[device] = corners

    # Only add them to img_points if both devices got it
    if all(device in found_points for device in DEVICES):
        if not first:
            for device in DEVICES:
                img_points[device].append(found_points[device])
            obj_points.append(dummy_points)
        first = False
        skip_frames = 30
        cv2.waitKey(200)

    cv2.waitKey(10)

# Close the devices
for device in DEVICES:
    vidcaps[device].release()

# Perform solo calibration
solo = {}
for device in DEVICES:
    dev_points = img_points[device]

    # Generate and store the calibrations for the device
    result, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, dev_points, (640, 480), None, None)
    print("Solo calibration result for {}: {}".format(device, result))

    np.savetxt("device_{}_mtx.txt".format(device), mtx)
    np.savetxt("device_{}_dist.txt".format(device), dist)
    np.savetxt("device_{}_rvecs.txt".format(device), rvecs)
    np.savetxt("device_{}_tvecs.txt".format(device), tvecs)

    # Store the matrix and distance values for use in stereo calibration
    solo.setdefault(device, {})["mtx"] = mtx
    solo.setdefault(device, {})["dist"] = dist

    # Calculate and report the error
    total_error = 0
    for i in range(len(obj_points)):
        projected_points, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(dev_points[i], projected_points, cv2.NORM_L2) / len(projected_points)
        total_error += error
    print("Error for device {}: {}".format(device, total_error / len(obj_points)))

# Stereo calibration
result, _, _, _, _, R, T, E, F = cv2.stereoCalibrate(obj_points,
                                                     img_points[DEVICES[0]], img_points[DEVICES[1]],
                                                     solo[DEVICES[0]]["mtx"], solo[DEVICES[0]]["dist"],
                                                     solo[DEVICES[1]]["mtx"], solo[DEVICES[1]]["dist"],
                                                     (640, 480),
                                                     #criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 2000, 0.00001),
                                                     flags=cv2.CALIB_FIX_INTRINSIC)
print("Stereo calibration result: {}".format(result))

# Store the calibration output
np.savetxt("stereo_R.txt", R)
np.savetxt("stereo_T.txt", T)
np.savetxt("stereo_E.txt", E)
np.savetxt("stereo_F.txt", F)

cv2.destroyAllWindows()
