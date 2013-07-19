'''
Created on 2013/07/17

@author: huxiufeng
'''
#coding=gbk

# -*- coding: cp936 -*-
import socket
import time
import struct
import binascii
import sys


def cmpp20svr(host, port): 
#    HOST = '172.17.234.112'
#    PORT = host
    HOST = host
    PORT = int(port)
    BUFSIZE = 1024
    ADDR = (HOST,PORT)
    
    packcmd = struct.Struct('!3I')
    
    packconnectack = struct.Struct('!3I I 16B I')
    packtestack = struct.Struct('!3I B')
    packsubmitack = struct.Struct('!3I I I B')
  
    a = 0
   
    tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSerSock.bind(ADDR)
    tcpSerSock.listen(1)
    
    cmds = (1,4,1)
    data = ''
    while True:
        print 'waiting for connection...'
        tcpclientsock,addr=tcpSerSock.accept()
        print ('...connected from:',addr)
        isok = True
     
        while True:
            try:
                data += tcpclientsock.recv(BUFSIZE)
                if not data:        
                    break       
                #print "get",binascii.hexlify(data)
            except:
                print "err rcv"
                break
            while True:
                if data == '' or len(data) < 12:
                    break
                try:
                    cmds = packcmd.unpack(data[0:12])
                except :
                    print "err unpack: ", data
                    isok = False
                    break
                if len(data) < cmds[0]:
                    break
        
                if cmds[1] == 0x00000004 : #submit
                    a += 1
                    #b += 2
                    #print 'submit rsp'
                    submitack = (21, 0x80000004,cmds[2], a, 0, 0)
                    try :
                        packedvalue = packsubmitack.pack(*submitack)
                    except:
                        print "pack error", str(submitack)
                        continue
                    tcpclientsock.sendall(packedvalue)  
                    #tcpclientsock.sendall('ok')
                    if a%1000 == 0:
                        print 'submit : ', str(a), "time : ", time.ctime(), binascii.hexlify(data)
                elif cmds[1] == 0x00000001:    #connect
                    connectack=(36, 0x80000001, cmds[2],0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
                    tcpclientsock.sendall(packconnectack.pack(*connectack))
                    print 'connect'
                elif cmds[1] == 0x00000008: #test
                    testack = (13, 0x80000008,cmds[2], 0)
                    tcpclientsock.sendall(packtestack.pack(*testack))
                    print 'active test'
                else:
                    print 'unkown cmd : ', binascii.hexlify(data)
                    isok = False
                    break
                    #tcpclientsock.sendall('unkown')
                    #break
                if len(data) == cmds[0]:
                    data = ''
                else :
                    data = data[cmds[0]:]
            if not isok:
                break
     
        tcpclientsock.close()
     
    tcpSerSock.close()


#----------------------It is a split line--------------------------------------

def main():
    if len(sys.argv) <3:
        print " the format is python simsvr host port"
        return 
    
    host = sys.argv[1]
    port = sys.argv[2]
    print host , port
    cmpp20svr(host, int(port))
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"