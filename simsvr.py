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
import thread

SEQ = 0
LOOPNUM = 1
srcphone = '18800000000'
desphone = '95516'
msg = 'abcdefghij'
CONNECTED = False


def emp(size,emp=None):
    if emp is None:
        emp =''
    for i in range(size):
        emp += '\0'
    return emp

packdevileryfix = struct.Struct('!21s 10s 3B 21s B B 10s 8s')
packdelivery = struct.Struct('!3I I I 75s')


def deliverthrd(sock, seq):
    fixvalue = (emp(21-len(desphone), desphone),'AAAAAAAAAA',0,0,0,emp(21-len(srcphone), srcphone), 0,10,emp(10-len(msg),msg), emp(8))
    fixpackvalue = packdevileryfix.pack(*fixvalue)
    msglen = 95
    
    while not CONNECTED:
        time.sleep(1)
    idx = 0
    for i in range(LOOPNUM):
        seq += 1
        value = (msglen, 0x00000005, seq, 0, seq, fixpackvalue)
        packvalue = packdelivery.pack(*value)
        idx +=1
        print binascii.hexlify(packvalue)
        sock.sendall(packvalue)
        if idx % 1000 == 0:
            print 'dilivery : ',idx 
        time.sleep(0.001)

def rundelivery(sock):
    global SEQ
    SEQ=1000
    thread.start_new_thread(deliverthrd, (sock, SEQ))


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
     
        rundelivery(tcpclientsock)
        delierynum = 0
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
        
                if cmds[1] == 0x80000005 : #delivery rsp
                    delierynum += 1
                    #print "delierynum", delierynum
                    if delierynum % 1000 == 0:
                        print "delieryack : ", delierynum
                
                elif cmds[1] == 0x00000004 : #submit
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
                    time.sleep(1)
                    global CONNECTED
                    CONNECTED = True
                    
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