#!/usr/bin
#coding=gbk
'''
Created on 2013/07/25

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

'''wrap container define'''
st_cmdhead = struct.Struct('!3I')
st_ack_connect = struct.Struct('!3I B 16s B')
#st_ack_disconnect = struct.Struct('!')
st_ack_activetest = struct.Struct('!3I B')
st_ack_submit = struct.Struct('!3I 2I B')
st_ack_delivery = struct.Struct('!3I 2I B')

#delivery
st_delivery_head = struct.Struct('!3I 2I')
st_delivery_fix = struct.Struct('!21s 10s 3B 21s 2B')



#parafile define
sec_sys = 'sys'
sec_snd = 'snddata'

op_host = 'host'
op_port = 'port'
op_loop = 'sndloop'
op_sleep = 'sleep'

op_src = 'src'
op_des = 'des'
op_msg = 'msg'
op_coding = 'coding'
op_svcid = 'svcid'

#tcp rcv buffer
BUFSIZE = 1024

class cmpp20:
    def __init__(self, parafile):
        self.parafile = parafile
        print 'parafile' , self.parafile
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.parafile)
        syspara = self.config.items(sec_sys)
        snddata = self.config.items(sec_snd)
        #print self.config.sections()
        print syspara
        print snddata
        
    def emp(self, size, emps=None):
        lens = size     
        if emps is None:
            emps = ''
        else:
            lens = size-len(emps)
        for i in xrange(lens):
            emps += '\0'
        return emps
    
    def trcoding(self, msg, codeformat):
        #TODO
        return msg
    
    def sndloop(self, sock):
        if (not self.isconnected) or (not self.islogin) :
            time.sleep(1)
        #get data
        sndloop = self.config.getint(sec_sys, op_loop)
        sndsleep = self.config.getfloat(sec_sys, op_sleep)
        src = self.config.get(sec_snd, op_src)
        des = self.config.get(sec_snd, op_des)
        msg = self.config.get(sec_snd, op_msg)
        codeformat = self.config.getint(sec_snd, op_coding)
        svcid = self.config.get(sec_snd, op_svcid)
        
        msg = self.trcoding(msg, codeformat)
        #st_delivery_fix = struct.Struct('! 21s 10s b b b 21s b b')
        fixdata = (self.emp(21,des), 
                   self.emp(10, svcid),
                   0,0,codeformat,
                   self.emp(21, src),
                   0, len(msg))
        packfix = st_delivery_fix.pack(*fixdata)
        packall = packfix + msg + self.emp(8)
        #print binascii.hexlify(packall)
        
        str_delivery = '!3I 2I %ds' % len(packall)
        st_delivery = struct.Struct(str_delivery)
        
        sndnum = 0
        
        time.sleep(1)
        now  = time.time()
        
        for i in xrange(sndloop):
            value = (20+len(packall), ID_DELIVERY, self.seqid, 0, self.seqid, packall)
            packhead = st_delivery.pack(*value)
#            print binascii.hexlify(packhead)
            
            sock.sendall(packhead)
            self.seqid += 1
            sndnum += 1
            if sndnum % 1000 == 0:
                new = time.time()
                print 'snd: ', sndnum, ', now: ', time.ctime(), ', tps:', 1000/(new-now)
                now = new
            time.sleep(sndsleep)
  
    def start(self):
        #socket bind
        host = self.config.get(sec_sys, op_host)
        port = self.config.getint(sec_sys,op_port)
        addr = (host,port)
        #print addr 
        
        socklisten = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socklisten.bind(addr)
        socklisten.listen(1)
        
        self.isconnected = False
        self.islogin = False
        self.seqid = 1
        #listem
        while True:
            print addr, 'waiting for connection...'
            sock, addr = socklisten.accept()
            print ('...connected from:',addr)
            self.isconnected = True
            
            self.submitnum = 0
            self.delisucc = 0
            self.deliack = 0
            #start send loop
            sndthread = threading.Thread(target=self.sndloop, args=(sock,))
            sndthread.start()
            
            #rev
            data = ''
            while True:
                try : 
                    data += sock.recv(BUFSIZE)
                except Exception, e:
                    print 'recv err ', e
                    self.isconnected = False
                    self.islogin = False
                    break
                if not data:
                    self.isconnected = False
                    self.islogin = False
                    break
                
                data = self.procrecv(data, sock)
                if data is None:
                    self.isconnected = False
                    self.islogin = False
                    print 'data proc err'
                    break    
                
        
            sndthread.join()
            sock.close()
        socklisten.close()
            
    def sndconnectack(self, sock, cmds):
        value=(30, ID_CONNECT_ACK, cmds[2],0,self.emp(16),0)
        sock.sendall(st_ack_connect.pack(*value))
        print 'connect'
        time.sleep(1)
        self.seqid = cmds[2]+1
        self.islogin = True
        
    def sndactivetestack(self, sock, cmds):
        value = (13, ID_ACTIVETEST_ACK,cmds[2], 0)
        sock.sendall(st_ack_activetest.pack(*value))
        print 'active test'
    
    def procdeliveryack(self, cmds):
        self.deliack += 1
        #print "delierynum", delierynum
        if self.deliack % 1000 == 0:
            print "delieryack : ", self.deliack, ", time : ", time.ctime()
            
    def sndsubmitack(self, sock, cmds):
        self.submitnum += 1
        value = (21, ID_SUBMIT_ACK, cmds[2], self.submitnum, 0, 0)  
        sock.sendall(st_ack_submit.pack(*value))  
        #tcpclientsock.sendall('ok')
        self.seqid = cmds[2]+1
        if self.submitnum %1000 == 0:
            print 'submit : ', self.submitnum, ", time : ", time.ctime()
    
    def procrecv(self, data, sock):
        while True:
            if data == '' or len(data) < 12:
                break
            try:
                cmds = st_cmdhead.unpack(data[0:12])
            except Exception, e:
                    print "err unpack: ", data, ' err : ', e
                    return None
            if len(data) < cmds[0]:
                    print 'err data length', cmds[0]
                    return None        
            if cmds[1] == ID_CONNECT :
                self.sndconnectack(sock, cmds)
            elif cmds[1] == ID_ACTIVETEST :
                self.sndactivetestack(sock, cmds)
            elif cmds[1] == ID_DELIVERY_ACK :
                self.procdeliveryack(cmds)
            elif cmds[1] == ID_SUBMIT :
                self.sndsubmitack(sock, cmds)
                
            else:
                print 'unkown cmd : ', binascii.hexlify(data)
                           
            if len(data) == cmds[0]:
                    data = ''
            else :
                data = data[cmds[0]:]
                         
        return data
            

#----------------------It is a split line--------------------------------------

def main():
    parafile = 'cmpp20.txt'
    if len(sys.argv)>1:
        parafile = sys.argv[1]
    
    svr = cmpp20(parafile)
    svr.start()
    
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"