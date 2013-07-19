# !/usr/bin
# coding=UTF-8
'''
Created on 2013/06/09

@author: huxiufeng

base tcp server, have listen accept funcs.

'''
from socket import *
from util import *



class CSvr(object):
    '''
    classdocs
    '''
    def __init__(self, infile):
        '''
        Constructor
        '''
        self.cfg = ucfg.CCfg(infile)
        self.host = ''
        self.port = self.cfg.getItemData("LOCAL", "port")
        self.bufsize = self.cfg.getItemData("LOCAL", "bufsize")
        
    def start(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        
        while True:
            print 'waiting for connection...'
            socks, addr = self.socket.accept()
            print '...connected from:', addr
            self.transdoing(socks, addr)
            
        self.socket.close()

    def transdoing(self, socks, addr):
        "implementation by derived class"
        pass


