
"""
Class Name(s):   TP17Storage

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



import pandas as pd



class TP17Storage:
    '''
    Basic database for storing frame information.
    Developed using pandas DataFrame
    '''
    NUM_SECTIONS = 9

    def __init__(self, file = None):
        if file == None:
            self.cols = ['Time']
            for i in range(self.NUM_SECTIONS):
                self.cols.append('Section' + str(i+1) +' count')
                self.cols.append('Section' + str(i+1) + ' movement')
            self.db = pd.DataFrame(columns = self.cols)
        else:
            try:
                self.db = pd.read_csv(file)
                self.cols = list(self.db)
            except:
                print('Database not found.')

    def add(self,frame):
        '''
        Adds a row to the database based on the current frame data

        :param frame: the frame we are looking at

        :returns None
        '''
        row = [frame.time_now]
        for i in range(self.NUM_SECTIONS):
            row.append(frame.sections[i].people_count)
            row.append(frame.movements[i])
        to_add = pd.DataFrame([row],columns=self.cols)
        both = [self.db,to_add]
        self.db = pd.concat(both)
        return None

    def save(self):
        '''
        Saves the database into working directory under name tp17db.csv

        :returns None
        '''
        self.db.to_csv('tp17db.csv', index = False)

        return None
