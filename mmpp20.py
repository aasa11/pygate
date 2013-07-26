#!/usr/bin
#coding=gbk
'''
Created on 2013/07/26

@author: huxiufeng
'''
import ConfigParser
import sys
import socket
import time
import struct
import binascii
import threading

'''command ids'''
ID_CONNECT              = 0x00000001
ID_CONNECT_ACK          = 0x80000001
ID_ACTIVETEST           = 0x00000008
ID_ACTIVETEST_ACK       = 0x80000008
ID_DISCONNECT           = 0x00000002
ID_DISCONNECT_ACK       = 0x80000002
ID_SUBMIT               = 0x00000004
ID_SUBMIT_ACK           = 0x80000004
ID_DELIVERY             = 0x00000005
ID_DELIVERY_ACK         = 0x80000005
ID_DELIVERY_REPORT      = 
ID_DELIVERY_REPORT_ACK  = 



#----------------------It is a split line--------------------------------------

def main():
    pass
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"