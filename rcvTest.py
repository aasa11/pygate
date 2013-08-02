#!/usr/bin/
#coding=gbk
'''
Created on 2013/08/01

@summary: mutilthreadsndsocketdata

@author: huxiufeng
'''
import socket
import sys
import time
import binascii
import struct
import hashlib
import datetime
import threading


HOST = '172.17.234.112'
PORT = 44401
BUFSIZE = 60000
DATALEN = 1000
SUCCNUM = 100


SNDCHAR1 = 'A'
SNDCHAR2 = 'Z'


def getdata(ch, lens):
    strs = ''
    for _ in xrange(lens):
        strs += str(ch)
        #time.sleep(0.001)
    return strs

def revsvr():
    addr = (HOST,PORT)
    socklisten = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socklisten.bind(addr)
    socklisten.listen(1)
    
    while True:
        print addr, 'waiting for connection...'
        sock, addr = socklisten.accept()
        print ('...connected from:',addr)
        
        D1 = getdata(SNDCHAR1, DATALEN)
        D2 = getdata(SNDCHAR2, DATALEN)
        
        succ1 = 0 
        succ2 = 0   
        data = ''
        while True:
            try : 
                data += sock.recv(BUFSIZE)
            except Exception, e:
                print 'recv err ', e
                break
            if not data:
                print "no data ..."
                break
            
            if len(data) < DATALEN:
                continue
            oneline = data[0:DATALEN]
            if oneline == D1 :
                succ1 += 1
                if succ1 % SUCCNUM == 0:
                    print "succ1 : ", succ1
            elif oneline == D2 :
                succ2 += 1
                if succ2 % SUCCNUM == 0:
                    print "succ2 : ", succ2
            else:
                print "err oneline" 
                print oneline
                break
            
            data = data[DATALEN:]
            
        sock.close()
        
    socklisten.close()


#----------------------It is a split line--------------------------------------

def main():
    revsvr()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"