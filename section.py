
class Section:
    '''
    Represents a section of the Frame (image).
    '''

    def __init__(self,x,y,width,height):
        '''
        Constructs the section with coordinates of top left point, width and height

        :param x: top left x coordinate - pixels
        :param y: top left y coordinate - pixels
        :param height: height of the section - pixels
        :param width: width of the section - pixels
        '''
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.people_count = 0

    def count_people(self,person_list):
        '''
        Counts the detected people that fit into this section.

        :param person_list: List of objects of type Person, representing the persons detected in the
                            whole frame
        :returns None
        '''
        for person in person_list:
            #area of the person, we want only to count if its more than 50% in this section
            #problem. what if its split between 4 sections and neither has 50% ? pick largest, have to change implementation
            #p_area = person.width * person.height
            #TODO intersects and overlaps, hardest part
            #then count based on area
            #basic implementation - if the top left corner fits in
            if person.x > self.x and person.y > self.y and person.x <= (self.x + self.width) and person.y <= (self.y + self.height):
                self.people_count += 1

        return None
