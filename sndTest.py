#!/usr/bin/
#coding=gbk

'''
Created on 2013/08/01

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


LOOPNUM = 1000000
CHARLEN = 10000
HOST = '172.17.254.180'
PORT = 44401

SNDCHAR1 = 'A'
SNDCHAR2 = 'Z'
SNDCHAR3 = 'a'
SNDCHAR4 = 'z'
SUCCNUM = 100

def getdata(ch, lens):
    strs = ''
    for _ in xrange(lens):
        strs += str(ch)
        #time.sleep(0.001)
    return strs

def sndThd(sock, data):
    for i in xrange(LOOPNUM):
        sock.sendall(data)
        #time.sleep(0.0001)
        if i %SUCCNUM == 0 :
            print "snd : ", i

def sockclient():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (HOST, PORT)
    sock.connect(server_address)
    sock.setblocking(True)


    snddata1 = getdata(SNDCHAR1, CHARLEN)
    snddata2 = getdata(SNDCHAR2,CHARLEN)
    snddata3 = getdata(SNDCHAR3,CHARLEN)
    snddata4 = getdata(SNDCHAR4,CHARLEN)

    sndthread1 = threading.Thread(target=sndThd, args=(sock,snddata1))
    sndthread2 = threading.Thread(target=sndThd, args=(sock,snddata2))
    sndthread3 = threading.Thread(target=sndThd, args=(sock,snddata3))
    sndthread4 = threading.Thread(target=sndThd, args=(sock,snddata4))
    sndthread1.start()
    sndthread2.start()
    sndthread3.start()
    sndthread4.start()
    
    sndthread1.join()
    sndthread2.join()
    sndthread3.join()
    sndthread4.join()
    
    sock.close()



#----------------------It is a split line--------------------------------------

def main():
    sockclient()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"