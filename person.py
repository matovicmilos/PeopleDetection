
"""
Class Name(s):   Person

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



class Person:
    '''
    Represents a person detected by opencv detection mechanism

    fields:
        x: x coordinate of the top left point of the bounding box surrounding the person
        y: y coordinate of the top left point
        height: height of the bounding box
        width: width of the bounding box
    '''
    def __init__(self,x,y,width,height):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
