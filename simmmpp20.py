'''
Created on 2013/07/18

@author: huxiufeng
'''
#!/usr/bin/
#coding=gbk


import socket
import sys
import time
import binascii
import struct
import hashlib
import datetime
import thread


ISSND = False

BUFFSIZE = 1024
LOOPNUM = 0
DEFAULTTIMEOUT = 600000
SEQID = 0
DATACODING = 15
desphone = '18812345678'
#connect pack
packconnect = struct.Struct('!3I B I 16s B I H')
#connect ack pack
packconnectack = struct.Struct('!3I I 16s B I')
#send pack
packsendfix = struct.Struct('!4I I 10s 21s B B B 32s 21s B 21s B 10s 24s 4B')
packsend = struct.Struct('!3I 168s')
#dilivery ack
packdiliveryack = struct.Struct('!3I 5I')



def emp(size,emp=None):
    if emp is None:
        emp =''
    for i in range(size):
        emp += '\0'
    return emp

datasendfix = (0,0,0,0,0,'ABCDEFGHIJ', emp(21),0,0,0,emp(32),emp(21),1,emp(10, desphone),10,'ABCDEFGHIJ',emp(24), 1,1,1,1)
packvaluesendfix = packsendfix.pack(*datasendfix)
print packvaluesendfix
#send ack pack
packsndack = struct.Struct('!3I 4I I')
#dr ack pack
packdrack = struct.Struct('!3I 4I I')
#active ack pack
packtestack = struct.Struct('!3I I')
#cmd pack
packcmd = struct.Struct('!3I')




def getconvalue(seqid, user, password, timestamp):
    userlen = len(str(user))
    pwdlen = len(password)
    
    strpack = '!'+str(userlen)+'s 9B '+str(pwdlen)+'s 10s'
    print 'strpack is ', strpack
    packmd5 = struct.Struct(strpack)
    
    
    strtimestamp = "%010d" % timestamp
    value = (str(user), 0,0,0,0,0,0,0,0,0, str(password), strtimestamp)
    print value
    try :
        packedvalue = packmd5.pack(*value)
        print len(packedvalue)
        
    except:
        print 'pack md5 err'
        return False
    
    md5data = hashlib.md5()
    md5data.update(packedvalue)
    #print md5data
    #print md5data.digest()
    
    convalue = (40,0x00000001, seqid, 0x20, int(user), md5data.digest(), 2, timestamp, 16)
    print convalue
    try :
        data = packconnect.pack(*convalue)
    except Exception, e:
        print 'pack connect err', e
        return False
    
    return data


def sendmsg(sock, datacoding):
    global SEQID
    global ISSND
    ISSND = True
    
    #sndvalue = 
    for i in range(LOOPNUM):
        SEQID +=1
        valuesend = (180,0x00000004,SEQID,packvaluesendfix)
        packvalue = packsend.pack(*valuesend)
        sock.sendall(packvalue)
        #print binascii.hexlify(packvalue)
        #time.sleep(0.0001)
        if SEQID % 1000 == 0:
            print "snd: ", SEQID, ' time: ',time.ctime()
        
    ISSND = False

def simMmpp20(host, port , user, password):
    print "host: ", host
    print "port: ", port
    print "user: ", user
    print "pswd: ", password
    
    socket.setdefaulttimeout(DEFAULTTIMEOUT)
    #connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    sock.connect(server_address)
    sock.setblocking(True)
    #seqid
    connected = False
    global SEQID
    #send connect
    while True:
        SEQID += 1
        if connected:
            break
        
        now = datetime.datetime.now()
        timestamp = now.month*100000000 + now.day*1000000+now.hour*10000+now.minute*100+now.second;
        print 'simestamp', timestamp
        packvalue = getconvalue(SEQID, user, password, timestamp)
        if packvalue is False:
            sock.close() 
            print 'pack err return'
            return 
        print "connect value: ", binascii.hexlify(packvalue)
        sock.sendall(packvalue)
        connectack = sock.recv(BUFFSIZE)
        if not connectack or len(connectack) < 37:
            print "connect err"
            time.sleep(10)
            continue
        
        data = packconnectack.unpack(connectack)
        if data[1] == 0x80000001 and data[3] == 0:
            connected = True
            print 'connected'
        else:
            print 'cmd: ', data[1], ' err no : ', str(data[3])
            print data
            time.sleep(10)
            
    time.sleep(1)
             
    if connected:
        thread.start_new_thread(sendmsg, (sock, DATACODING))
    data = ''  
    isok = True 
    sndsucc = 0
    sndfail = 0
    drsucc = 0 
    diliverynum = 0
    while True:
        try : 
            recvdata = sock.recv(BUFFSIZE)
            if not recvdata:  
                #print "no data", time.ctime()  
                break
            data += recvdata
        except Exception, e:
            print "err rcv", e
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
            
            if cmds[1] == 0x00000005:    #diliery
                diliverynum +=1
                if diliverynum % 1000 == 0:
                    print "diliverynum : ", diliverynum
                #print "diliverynum : ", diliverynum    
                value = (32, 0x80000005, cmds[2], 0,0,0,0,0)
                
                packvalue = packdiliveryack.pack(*value)
                sock.sendall(packvalue)         
            elif cmds[1] == 0x80000004 : #submit ack
                value = packsndack.unpack(data[0:32])
                #print binascii.hexlify(data)
                #print value
                success = value[7]
                if success <> 0:
                    sndfail +=1
                    print "sndfail", sndfail
                else:
                    sndsucc += 1
                    #print "sndsucc", sndsucc
                    
#                if (sndsucc+1)%100 == 0 :
#                    print "sndsucc : ", sndsucc, 'time: ',time.ctime()
            
            elif cmds[1] == 0x00000008: #test
                testack = (16, 0x80000008,cmds[2], 0)
                packdata = packtestack.pack(*testack)
                sock.sendall(packdata)
                print 'active test', binascii.hexlify(packdata)
            elif cmds[1] == 0x00000025: #dr
                drack = (32, 0x80000025,cmds[2],0,0,0,0,0)
                sock.sendall(packdrack.pack(*drack))
                drsucc +=1
            else:
                print 'unkown cmd : ', binascii.hexlify(data)
                isok = False
                break  
            if len(data) == cmds[0]:
                data = ''
            else :
                data = data[cmds[0]:]
        if not isok:
            print 'no isok'
            break
        
    while ISSND:
        time.sleep(1)
    sock.close() 

    print sndsucc
    print sndfail
    print drsucc
    
#----------------------It is a split line--------------------------------------

def main():
    if len(sys.argv) < 5:
        print "the format is python simmmpp20.py host port user password"
        return
    host = sys.argv[1]
    port = int(sys.argv[2])
    user = int(sys.argv[3])
    password = sys.argv[4]
    
    simMmpp20(host, port, user, password)
    
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"