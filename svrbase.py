# !/usr/bin/
# coding=gbk
'''
Created on 2013/08/01

@summary: ogw server base class, has configration, listen socket , snd rcv loop and etc.

@author: huxiufeng
'''
import sys
import socket
import time
import struct
# import binascii
import threading
import svrpara
from Queue import Queue

class cntpara:
    '''this struct is some para for one socket link'''
    def __init__(self, sockid):
        '''def some base sock count value here'''
        #id
        self.sockid = sockid
        
        #netstat
        self.tcpconnect = False
        self.appconnect = False 
        
        #seqid
        self.seqid = 0
        
        #send count
        self.sndnum = 0
        self.sndsucc = 0
        self.sndfail = 0
        #recv count
        self.rcvnum = 0
        
        #dr count
        self.drnum = 0
        self.drsnd = 0
        
        #send msg format
        self.snddata = None
        self.packsnd = None
        
        #send queue
        self.drque = Queue()
        
#----------------------It is a split line--------------------------------------       

class svrbase:
    '''This is the base class for the gateway socket links and snd \rcv loops'''
    def __init__(self, parafile):
        '''Init def, initialize the config file and print it'''
        self.parafile = parafile
        self.cfg = svrpara.svrpara(self.parafile)
        self.paradefine()
        self.msgid = [0,0]
        
    def emp(self, size, emps=None):
        '''fill empty value to string'''
        lens = size     
        if emps is None:
            emps = ''
        else:
            lens = size-len(emps)
        for _ in xrange(lens):
            emps += '\0'
        return emps
    
    def genmsgid(self):
        if self.msgid[1] < 999999:
            self.msgid[1] += 1
        else :
            self.msgid[0] += 1
            self.msgid[1] = 0
        return self.msgid
        
                
    def paradefine(self):
        '''define some paras which will be used in the obj, and the child class should rewrite it'''
        # stat
        self.statdefine()   
        # pack
        self.packdefine()
      
    def statdefine(self):
        '''initialize some stat variable'''
        self.sockpara = {}  
        self.sockslink = 0
        self.sockid = 0      
    
    def packdefine(self):
        '''initialize the pack data, realize by derived class'''
        self.ID_CONNECT              = 0x00000001
        self.ID_CONNECT_ACK          = 0x80000001
        self.ID_ACTIVETEST           = 0x00000008
        self.ID_ACTIVETEST_ACK       = 0x80000008
        self.ID_DISCONNECT           = 0x00000002
        self.ID_DISCONNECT_ACK       = 0x80000002
        self.ID_SUBMIT               = 0x00000004
        self.ID_SUBMIT_ACK           = 0x80000004
        self.ID_DELIVERY             = 0x00000005
        self.ID_DELIVERY_ACK         = 0x80000005
        self.ID_RECEIPT            = 0x00000025
        self.ID_RECEIPT_ACK        = 0x80000025
        
        #para transfer
        self.packbyte = struct.Struct('!B')
        self.packint = struct.Struct('!I')
        self.packphone = struct.Struct('!21s')
    
    def sndconnect(self, sock, para):
        '''snd connect cmd, realize by derived class'''
        pass
    
    def sndterminate(self, sock , para):
        '''snd terminate cmd, realize by derived class'''
        pass
    
    def sndmsg(self, sock , para):
        '''snd msg, realize by derived class'''
        pass
    
    
    def rcvproc(self, data , sock, para):
        '''rcv proc , realize by derived class'''
        return ''
              
              
    def initsndloop(self, para):
        '''do some init for snd loop, realize by derived class'''
        pass
    
    def initrcvloop(self, para):
        '''do some init for rcv loop, realize by derived class'''
        pass
            
    def sndloop(self, sock, para):
        '''snd data loop'''
        time.sleep(1)
        #para = self.getsockpara(sockid)
        sockid = para.sockid
        issndconnect = self.cfg.getsndconnect()
        issndterminate = self.cfg.getsndterminate()
        # init
        self.initsndloop(para)
        # wait for app connect
        while (para.tcpconnect and not para.appconnect) :        
            if issndconnect :
                self.sndconnect(sock, para)
                time.sleep(1)
            else :
                print "sockid : ", sockid, ", wait connect cmd..."
                time.sleep(1)
        
        # snd data loop
        time.sleep(1)
        loopnum = self.cfg.getsndloop()
        sleeptime = self.cfg.getsleeptime()
        ptnum = self.cfg.getptnum()
        para.sndnum = 0
        now = time.time()
        for _ in xrange(loopnum) :
            self.sndmsg(sock, para)
            para.sndnum += 1
            if para.sndnum % ptnum == 0 :
                new = time.time()
                if new == now :
                    print "sockid : ", sockid, " : snd : ", para.sndnum, ", time : ", time.ctime(), ", tps : XXX"
                else :
                    print "sockid : ", sockid, " : snd : ", para.sndnum, ", time : ", time.ctime(), ", tps : ", float(ptnum) / (new - now)
                    now = new
            time.sleep(sleeptime)
        
        # snd terminate
        if issndterminate:
            waittime = self.cfg.getdefualttimeout()
            wait = 0
            while wait < waittime :
                time.sleep(10)
                wait += 10
            while (para.tcpconnect and para.appconnect):
                self.sndterminate(sock, para)
                time.sleep(1)
        # out of sndloop
    
    
    def rcvloop(self, sock, para):
        '''rcv data loop'''
        #para = self.getsockpara(sockid)
        BUFSIZE = self.cfg.getbufsize()
        # init
        self.initrcvloop(para)
        data = ''
        # rcv loop start
        while para.tcpconnect:
            try:
                data += sock.recv(BUFSIZE)
            except Exception, e:
                print 'recv err ', e
                para.tcpconnect = False
                para.appconnect = False
                break
            if not data:
                print "no data ...  "
                para.tcpconnect = False
                para.appconnect = False
                break
            
            data = self.rcvproc(data, sock, para)
            if data is None:
                self.tcpconnect = False
                self.appconnect = False
                print 'data proc err'
                break 
        # rcv loop out
        
    def drloop(self, sock, para):
        '''This is used to snd dr '''
        drdelay = self.cfg.getdrdelay()
        
        #wait app connect
        while not para.appconnect or not para.tcpconnect :
            time.sleep(1)
        
        while para.appconnect and para.tcpconnect :
            if para.drque.qsize() <= 0:
                time.sleep(0.1)
            snddata = para.drque.get()
            drdata = snddata[1]
            drtime = snddata[0]
            #wait dr time
            while time.time() - drtime < drdelay :
                #print "now is ", time.time, "; snd time is : ", drtime 
                time.sleep(0.01)
            self.snddr(sock, para, drdata)
        return
    
    def snddr(self, sock , para, drdata):
        '''snd dr, realize by the derived class'''
        pass
        
                   
    def initcountval(self, sockid):
        '''init some count values for the one socket link'''
        onepara = cntpara(sockid)
        self.sockpara[sockid] = onepara
        
    def getsockpara(self, sockid):
        '''get sock para, if not exist, create it'''
        if sockid in self.sockpara.keys():
            onepara = self.sockpara[sockid]
            return onepara
        onepara = cntpara(sockid)
        self.sockpara[sockid] = onepara
        return onepara
    
    def removecountval(self, sockid):
        '''remove the count values of the socket link'''
        if sockid in self.sockpara.keys():
            self.sockpara.pop(sockid)
    
    def onesockproc(self, sock, sockid):
        '''proc one connect work'''
        self.initcountval(sockid)
        para = self.getsockpara(sockid)
        para.tcpconnect = True
        self.sockslink += 1
        time.sleep(1)
        print "this is the ", self.sockslink, " socket links, sock id is ", sockid
        
        #snd loop
        print "sockid : ", sockid, " start snd loop"
        sndthread = threading.Thread(target=self.sndloop, args=(sock, para))
        sndthread.start()
        #dr loop
        if self.cfg.getdrloop():
            print "sockid : ", sockid, " start dr loop"
            drthread = threading.Thread(target=self.drloop, args=(sock, para))
            drthread.start()
        #recv loop
        print "sockid : ", sockid, " start rcv loop"
        self.rcvloop(sock, para)
           
        sndthread.join()
        sock.close()
        self.removecountval(sockid)
        self.sockslink -= 1
        print "sockid ", sockid, " terminated, now has ", self.sockslink, " links."
        
    def startsvr(self):
        '''enter main listen loop'''
        sockaddr = self.cfg.getsockaddr()
        socklisten = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socklisten.bind(sockaddr)
        socklisten.listen(self.cfg.getlistennum())
        while True : 
            print sockaddr, 'waiting for connection...'
            sock, addr = socklisten.accept()
            print ('...connected from:', addr)
            self.tcpconnect = True
            # start snd thread
            self.sockid += 1
            sockthread = threading.Thread(target=self.onesockproc, args=(sock, self.sockid))
            sockthread.start()
            
        socklisten.close()
            

    def startclt(self):
        '''connect the server and do snd rcv procs'''
        # connect
        DEFAULTTIMEOUT = self.cfg.getdefualttimeout()
        socket.setdefaulttimeout(DEFAULTTIMEOUT)   
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = self.cfg.getsockaddr()
        sock.connect(server_address)
        sock.setblocking(True)
        # sock proc
        print "connected ", server_address
        self.onesockproc(sock, self.sockid)
        
        # end sock
        sock.close()
        
        


#----------------------It is a split line--------------------------------------

def main():
    # svr
    parafile = 'cmpp20.txt'
    if len(sys.argv) > 1:
        parafile = sys.argv[1]
    
    svr = svrbase(parafile)
    svr.startsvr()
    
    # clt
#    parafile = 'mmpp20.txt'
#    if len(sys.argv) > 1:
#        parafile = sys.argv[1]
#    
#    svr = svrbase(parafile)
#    svr.startclt()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"
