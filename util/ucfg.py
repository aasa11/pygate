#!/usr/bin
#coding=UTF-8
'''
Created on 2013/06/09

@author: huxiufeng

base config reader

'''

import ConfigParser
import os


class CCfg(object):
    '''
    classdocs
    '''
    

    def __init__(self, infile=''):
        '''
        Constructor
        '''
        if os.path.isfile(infile):
            pass
        else :
            infile = "config.cfg"
        self.config = ConfigParser.ConfigParser()
        self.config.read(infile)
        
    def getItemData(self, section, item):
        data = self.config.get(section, item)
        print "get ", section, " , " ,item, " is ", data
        return data 
    
    
#------------------------------------------------------------------------------
if __name__ == "__main__":
    mycfg = CCfg()
    print mycfg.getItemData("aaa", "1")
        