#!/usr/bin/
#coding=gbk
'''
Created on 2013/08/02

@summary: 

@author: huxiufeng
'''
from svrbase import *
import struct
import sys
import binascii
import datetime
import hashlib

class mmpp20clt(svrbase):
    def __init__(self, parafile):
        '''init file , call father's init'''
        svrbase.__init__(self, parafile)
        
    def packdefine(self):
        '''initialize the pack data, realize by derived class'''
        print "mmpp20 pack define init"
        svrbase.packdefine(self)
        self.packcmd = struct.Struct('!3I')
        self.packconnect = struct.Struct('!3I B I 16s B I H')
        self.packterminate = struct.Struct('!3I')
        self.packconnectack = struct.Struct('!3I I 16s B I')
        self.packtestack = struct.Struct('!3I I')
        self.packdeliveryack = struct.Struct('!3I 4I I')
        self.packterminateack = struct.Struct('!3I')
        self.packdrack = struct.Struct('!3I 4I I')
        self.packactivetest = struct.Struct('!3I')
        #snd msg data
        self.packsndfix= struct.Struct('!16s 4B 10s 21s 3B 16s 16s 21s B')
                
        #para version
        self.VERSION = 0x20
        
    def getconvalue(self, seqid, user, password, timestamp, windowsize):
        '''return connect value by given data, need md5 calc'''
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
        
        convalue = (40,self.ID_CONNECT, seqid, self.VERSION, int(user), md5data.digest(), 2, timestamp, windowsize)
        print convalue
        try :
            data = self.packconnect.pack(*convalue)
        except Exception, e:
            print 'pack connect err', e
            return False
        
        return data
        
        
    def sndconnect(self, sock, para):
        '''snd connect cmd, realize by derived class'''
        now = datetime.datetime.now()
        timestamp = now.month*100000000 + now.day*1000000+now.hour*10000+now.minute*100+now.second;
        print 'simestamp', timestamp
        packvalue = self.getconvalue(para.seqid, self.cfg.getusr(), self.cfg.getpwd(), timestamp, self.cfg.getwinsize())
        if packvalue is False:
            para.appconnect = False
            print 'pack connect err'
            return False
        sock.sendall(packvalue)
        print "sockid : ", para.sockid, "connect : ", binascii.hexlify(packvalue)
        para.seqid += 1
        
    
    def sndterminate(self, sock , para):
        '''snd terminate cmd, realize by derived class'''
        '''cmpp20 do not snd terminate , it just wait terminate'''
        value = (12, self.ID_DISCONNECT, para.seqid)
        packdata = self.packterminate.pack(*value)
        sock.sendall(packdata)
        print "sockid : ", para.sockid, "snd terminate : ", binascii.hexlify(packdata)
        
    
    def sndmsg(self, sock , para):
        '''snd msg, realize by derived class'''
        #para = self.getsockpara(sockid)
        para.seqid += 1 
        value = (12+len(para.snddata), self.ID_SUBMIT, para.seqid, para.snddata)
        packvalue = para.packsnd.pack(*value)
        sock.sendall(packvalue)
        #print "sockid : ", para.sockid, "snd value", binascii.hexlify(packvalue)
    
    def sndconnectack(self, sock, cmds, para):
        '''connect ack'''
        '''mmpp20 do not send connect ack, it just send connect'''
        pass
        
        
    def sndactivetestack(self, sock, cmds, para):
        '''active test ack'''
        value = (16, self.ID_ACTIVETEST_ACK,cmds[2], 0)
        sock.sendall(self.packtestack.pack(*value))
        print 'sockid : ', para.sockid, 'active test ack'
        
    def procsubmitack(self, cmds, para, data):
        '''delivery ack'''
        rt = self.packint.unpack(data[28:32])[0]
        if rt == 0: #success
            para.sndsucc += 1
            if para.sndsucc % self.cfg.getptnum() == 0:
                print "sockid : ", para.sockid, ' : snd succ : ', para.sndsucc, " time : ", time.ctime()
        else :  #failure
            para.sndfail += 1
            print "sockid : ", para.sockid, " : snd fail ", para.sndfail, " , rt : ", rt         
        return
    
    def snddeliveryack(self, sock, cmds, para):
        '''submit ack'''
        #print "delivery ack"
        para.rcvnum += 1
        value = (32, self.ID_DELIVERY_ACK, cmds[2], 0, 0, 0, 0, 0)  
        sock.sendall(self.packdeliveryack.pack(*value))  
        para.seqid = cmds[2]+1
        if para.rcvnum % self.cfg.getptnum() == 0:
            print "sockid : ", para.sockid, ' : get : ', para.rcvnum , ", time : ", time.ctime()
    
    def sndterminateack(self, sock, cmds , para):
        '''terminate ack'''
        ''''mmpp20 do not snd terminateack'''
        pass
    
    def procconnectack(self, cmds, para,data):
        '''do connect'''
        data = self.packconnectack.unpack(data[0:37])
        if data[3] == 0:
            print "sock : ", para.sockid, " connected ..., time : ", time.ctime()
            para.appconnect = True
        else :
            print "sock : ", para.sockid, "connect err ..., time : ",time.ctime(),"\ndata : ", binascii.hexlify(data[0:37])
        return
    
    def proctermiateack(self, sock, cmds, para) :
        '''do terminate'''
        para.appconnect = False
        print "sock : ", para.sockid, "disconnect ... , time : ", time.ctime() 
        return
    
    def snddrack(self, sock, cmds,para, data) :
        '''ack the dr '''
        value = (32, self.ID_RECEIPT_ACK, cmds[2], 0,0,0,0,0)
        packvalue = self.packdrack.pack(*value)
        sock.sendall(packvalue)
        para.drnum += 1
        if para.drnum % self.cfg.getptnum() == 0:
            print "sock : ", para.sockid, " : dr get : ", para.drnum, ", time : ", time.ctime()
        return
    
    def sndactivetest(self, sock , para):
        '''snd activetest, realize by the derived class'''
        para.seqid += 1
        value = (12, self.ID_ACTIVETEST, para.seqid)
        packvalue = self.packactivetest.pack(*value)
        sock.sendall(packvalue)
        print "sock : ", para.sockid, " : snd active test, time : ", time.ctime() 
    
    def rcvproc(self, data , sock, para):
        '''rcv proc , realize by derived class'''
        while True:
            if data == '' or len(data) < 12:
                break
            try:
                cmds = self.packcmd.unpack(data[0:12])
            except Exception, e:
                    print "err unpack: ", data, ' err : ', e
                    return None
            if len(data) < cmds[0]:
                    #print 'err data length', cmds[0]
                    return data        
            if cmds[1] == self.ID_CONNECT_ACK :
                self.procconnectack(cmds, para, data)
            elif cmds[1] == self.ID_ACTIVETEST :
                self.sndactivetestack(sock, cmds, para)
            elif cmds[1] == self.ID_SUBMIT_ACK :
                self.procsubmitack(cmds, para, data)
            elif cmds[1] == self.ID_DELIVERY :
                self.snddeliveryack(sock, cmds, para)
            elif cmds[1] == self.ID_DISCONNECT_ACK :
                self.proctermiateack(sock, cmds, para)  
            elif cmds[1] == self.ID_RECEIPT :
                self.snddrack(sock, cmds,para, data)  
            elif cmds[1] == self.ID_ACTIVETEST_ACK:
                print "get active test ack ..."      
            else:
                print 'unkown cmd : ', cmds
                           
            if len(data) == cmds[0]:
                    data = ''
            else :
                data = data[cmds[0]:]                       
        return data
              
              
    def initsndloop(self, para):
        '''do some init for snd loop, realize by derived class'''
        '''init snd data'''
        #para = self.getsockpara(sockid)
        
        src = self.cfg.getsrc()
        des = self.cfg.getdes().split(';')
        print "des phones : ", des
        msg = self.cfg.getmsg()
        coding = self.cfg.getcoding()
        svcid = self.cfg.getsvcid()
        #self.packsndfix= struct.Struct('!16s 4B 10s 21s 3B 16s 16s 21s B')
        fixs = (self.emp(16),
                0,0,self.cfg.getdr(),0,
                self.emp(10,svcid),
                self.emp(21),
                0,0,coding,
                self.emp(16),self.emp(16),
                self.emp(21, src),len(des)
                )
        #print fixs
        packfix = self.packsndfix.pack(*fixs)
        for phone in des :
            phonevalue = (self.emp(21,phone), )
            packfix += self.packphone.pack(*phonevalue)
        
        valuelen = (len(msg), )
        sndmsg = packfix + self.packbyte.pack(*valuelen) + msg + self.emp(28)
        prsnd = '!3I %ds' % len(sndmsg)
        packsnd = struct.Struct(prsnd)
        para.snddata = sndmsg
        para.packsnd = packsnd
        
    
    def initrcvloop(self, para):
        '''do some init for rcv loop, realize by derived class'''
        pass

#----------------------It is a split line--------------------------------------

def main():
    # clt
    parafile = 'mmpp20.txt'
    if len(sys.argv) > 1:
        parafile = sys.argv[1]
    
    clt = mmpp20clt(parafile)
    clt.startclt()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"