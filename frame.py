"""
Class Name(s):   Frame

Purpose:  See class summary
(c) Copyright 2016 Zircon Software Limited.

This software is protected by copyright, the design of any
article recorded in the software is protected by design
right and the information contained in the software is
confidential. This software may not be copied, any design
may not be reproduced and the information contained in the
software may not be used or disclosed except with the
prior written permission of and in a manner permitted by
the proprietors Zircon Software Limited.
"""



import cv2
import numpy as np
from section import Section
from person import Person
from imutils.object_detection import non_max_suppression
from datetime import datetime
from tp17storage import TP17Storage


class Frame:
    '''
    Represents a single frame taken from a video capture.
    fields:
        img_data: ndarray representation of a frame from a video
        movements: list of movements in/out/nochange + count how many for the section
        sections: 9 equal rectangles that frame is split into. defined by top left coordinates
                    width and height. list of Section objects
        people: people detected in the frame, list of Person objects
        hog: OpenCV classifier object used for detection

    constants:
        .........
    '''
    #width and height of the frame, for best visual representation select multiples of 3
    WIDTH = 640
    HEIGHT = 480
    #colour constants BGR mode
    RED = (0,0,255)
    BLUE = (255,0,0)
    GREEN = (0,255,0)
    #width of section lines
    LINE_WIDTH = 1
    #to split height and width by to give us section width/height
    SPLIT_DIV = 3
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    #'steps' used during classification , lower stride = possibly better accuracy but slower
    #choose values between 1 and 16 for best results (higher for larger images)
    STRIDE = (4,4)
    PADDING = (8,8)
    #scale used for classification, has to be > 1, lower scale = better accuracy but slower
    SCALE = 1.03


    def __init__(self,img_data):
        '''
        Creates the frame object resized to width x height pixels.
        Initializes the lists of people and sections and hog detector

        :param img_data: ndarray representation of a image

        advice:
            Load a image file using opencv first , then create a new Frame with that
        '''
        #resize the image to improve performance
        self.img_data = cv2.resize(img_data,(self.WIDTH,self.HEIGHT))
        self.sections = []
        self.people = []
        #self.hog = cv2.HOGDescriptor()
        #use default OpenCV pedestrian detector, to improve - train own detector and replace this
        #self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


        self.movements = []



    def draw_boundaries(self):
        '''
        Splits the frame into 9 equal rectangles, counts persons belonging to each of those
        and displays the number of people in each.

        :returns None

        usage:
            mustn't use before people are detected using detect_people()
        '''
        sec_height = int(self.HEIGHT/self.SPLIT_DIV)
        sec_width = int(self.WIDTH/self.SPLIT_DIV)
        x = 0
        y = 0
        #this will essentialy be 4 iterations with default settings as we are splitting the frame
        #into 9 sections but include edge lines
        while x <= self.WIDTH:
            #draw vertical (y is constant, x changes as a start point)
            self.draw_line(x)
            #draw horizontal (x is constant, y changes as a start point)
            self.draw_line(y,'h')
            #section top left x
            sec_tl = 0
            #we calc the section top left coords by getting the x while the y is constant
            #then y will change in the next outer while and we do the next lot
            while sec_tl < self.WIDTH-2 and len(self.sections) < 9:
                self.sections.append(Section(sec_tl,y,sec_width,sec_height))
                sec_tl += sec_width
            x += sec_width
            y += sec_height

        #count people in each section and write numbers at their top left
        for sec in self.sections:
            sec.count_people(self.people)
            cv2.putText(self.img_data,str(sec.people_count), (sec.x+10,sec.y+15),self.FONT,0.5,self.RED,1,cv2.LINE_AA)

        return None

    def detect_people(self):
        '''
        Detects people in the whole frame and draws green rectangles around them
        Stores people in a list of objects type Person, so we can use them when counting
        people in each section later.

        :returns None
        '''
        # (rects, weights) = self.hog.detectMultiScale(self.img_data, winStride=self.STRIDE,padding=self.PADDING, scale=self.SCALE)
        # # for (x, y, w, h) in rects:
        # #     cv2.rectangle(self.img_data, (x, y), (x + w, y + h), (0, 0, 255), 2)
        # #     self.people.append(Person(x,y,w, h))
        # # apply non-maxima suppression to the bounding boxes using a
        # # fairly large overlap threshold to try to maintain overlapping
        # # boxes that are still people
        # rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
        # people = non_max_suppression(rects, probs=None, overlapThresh=0.65)
        #
        midpoints = []
        # # draw the final bounding boxes
        # for (xA, yA, xB, yB) in people:
        #     cv2.rectangle(self.img_data, (xA, yA), (xB, yB), self.GREEN, 2)
        #     self.people.append(Person(xA,yA,xB - xA, yB - yA))
        #     #point in the middle of the detected rectangle
        #     midpoints.append((int((xB-xA)/2), int((yB - yA)/2)))
        face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

        faces = face_detector.detectMultiScale(self.img_data, scaleFactor = 1.1, minNeighbors = 5, minSize = (30,30), flags = cv2.CASCADE_SCALE_IMAGE)
        for(x,y,w,h) in faces:
            cv2.rectangle(self.img_data, (x,y), (x+w, y+h), self.GREEN, 2)
            self.people.append(Person(x,y,w, h))
            midpoints.append((int(x+w/2), int(y+h/2)))
        return midpoints

    def detect_upper(self):
        midpoints = []

        upperbody_detector = cv2.CascadeClassifier("haarcascade_upperbody.xml")

        bodies = upperbody_detector.detectMultiScale(self.img_data, scaleFactor = 1.05, minNeighbors = 5, minSize = (50,50), flags = cv2.CASCADE_SCALE_IMAGE)
        for(x,y,w,h) in bodies:
            cv2.rectangle(self.img_data, (x,y), (x+w, y+h), self.GREEN, 2)
            self.people.append(Person(x,y,w, h))
            midpoints.append((int(x+w/2), int(y+h/2)))
        return midpoints

    def detect_fullbody(self):
        midpoints = []

        fullbody_detector = cv2.CascadeClassifier("haarcascade_fullbody.xml")

        bodies = fullbody_detector.detectMultiScale(self.img_data, scaleFactor = 1.03, minNeighbors = 3, minSize = (50,50), flags = cv2.CASCADE_SCALE_IMAGE)
        for(x,y,w,h) in bodies:
            cv2.rectangle(self.img_data, (x,y), (x+w, y+h), self.GREEN, 2)
            self.people.append(Person(x,y,w, h))
            midpoints.append((int(x+w/2), int(y+h/2)))
        return midpoints

    def draw_line(self,start, orientation = 'v'):
        '''
        Draws a straight 1px blue line over the image

        :param start: starting point (pixel value) for the line
        :param orientation: v (vertical) or h (horizontal) , just so we know where to use hight/width

        :returns None
        '''
        # cv2.line takes image,start point, end point, colour, line width
        if orientation == 'v':
            cv2.line(self.img_data,(start,0),(start,self.HEIGHT),self.BLUE,self.LINE_WIDTH)
        else:
            cv2.line(self.img_data,(0,start),(self.WIDTH,start),self.BLUE,self.LINE_WIDTH)
        return None

    def write_time(self):
        '''
        Writes system time at the bottom right corner of the frame

        :returns None

        usage:
            frame.write_time() - at any time after initializing the frame
        '''
        self.time_now = str(datetime.now())
        loc = (self.WIDTH - 4*len(self.time_now),self.HEIGHT - 10)

        cv2.putText(self.img_data,self.time_now,loc,self.FONT,0.24,self.RED,1,cv2.LINE_AA)
        return None

    def update_movements(self, prev_counts):
        '''
        Updates the list of movements in/out of sections based on list of previous person counts
        and current person counts for each section.
        Needs to be called after people are detected, sections are initialized and people are counted.

        :param prev_counts: List of previous person counts for each section

        :returns prev_counts: updated counts for each section
        '''
        for i in range(len(self.sections)):
            cur = self.sections[i].people_count
            prev = prev_counts[i]
            #find out how many people went in/out of the section
            if cur > prev:
                self.movements.append(str(cur-prev) + ' IN')
            elif cur < prev:
                self.movements.append(str(prev-cur)+ ' OUT')
            else:
                self.movements.append('NO CHANGE')
            prev_counts[i] = self.sections[i].people_count

        return prev_counts

    def write_distance(self, point, dist):
        cv2.putText(self.img_data,"{0:.2f}".format(dist) + " m",point,self.FONT,0.4,(self.BLUE),1,cv2.LINE_AA)
        return None

    def show(self,winname):
        '''
        Displays the frame.

        Can be called at any time after initializing, but to get full view of people/sections
        call this function last.
        '''
        window = cv2.namedWindow(winname)
        cv2.imshow(winname,self.img_data)
        #cv2.waitKey(100)
        #cv2.destroyAllWindows()
        return None
