# PeopleDetection

Detecting people using OpenCV with a stereo camera (2 webcams) in order to triangulate
real world points and calculate distance from the camera.
Splits each frame into 9 sections and prints count of people detected in each one.

Current version detects faces only because the full body detection was not
reliable enough in order to test it properly, and the bounding boxes were too
large so sometimes the center point of the box wouldnt actualy be a part of the person
and would give incorrect distance.

To test it :
  1. install python3
  2. install OpenCV , numpy, pandas?
  3. connect 2 webcams
  4. print a calibration chessboard (google or opencv), i used one with 9x6 corners
  5. run: python chesscal.py
  6. in distances.py, adjust size of the square to what it is on your chessboard (if its getting the values terribly wrong try adjusting this *10 or /10 , the one i used was 25mm but with 0.025 meters it was getting distances *10 of actual)
  7. run : python distances.py

  This project was done as part of training course at Zircon software
