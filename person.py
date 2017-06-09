
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
