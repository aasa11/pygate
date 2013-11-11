#!/usr/bin/
#coding=gbk
'''
Created on 2013年11月7日

@summary: This is the simulator for the sgip.

@author: huxiufeng
'''
import svrbase
import struct
import sys
import binascii
import time
import socket
import threading

from Queue import Queue

#----------------------It is a split line--------------------------------------

class sockStat:
    def __init__(self, sock, msgid, status):
        self.sock = sock
        self.msgid = msgid
        self.status = status

class sgip12Svr(svrbase.svrbase):
    def __init__(self, parafile):
        svrbase.svrbase.__init__(self, parafile)
    
    def packdefine(self):
        '''initialize the pack data, realize by derived class'''
        print "sgip pack define init"
        svrbase.svrbase.packdefine(self)
        self.packcmd = struct.Struct('!5I')
        
        self.packbind = struct.Struct('!B 16s 16s 8s')
        self.packbindrsp = struct.Struct('!B 8s')
        
        self.packsubmitack = struct.Struct('!B 8s')

        self.packdr = struct.Struct('!3I b 21s B B 8s')
        
        self.packdeliveryfix = struct.Struct('!21s 21s B B B I')
        
        #para transfer
        self.packbyte = struct.Struct('!B')
        
        #发送队列
        self.sndlst = []
        
        self.drque = Queue()
        
        self.fixdata = self.getdeliverydata()
               

    def getdeliverydata(self):
        src = self.cfg.getsrc()
        des = self.cfg.getdes()
        prot = self.cfg.getprotocolid()
        emsi = self.cfg.getemiclass()
        msgori = self.cfg.getmsg()
        coding = self.cfg.getcoding()
        svcid = self.cfg.getsvcid()
        msgdatas = self.getsnddata(coding, msgori)
        '''only snd the first msg'''
        msg = msgdatas[0]
        #self.packdeliveryfix = struct.Struct('!21s 21s B B B I')
        fixs = (self.emp(21,src), 
                   self.emp(21,des),
                   prot,emsi,coding,
                   len(msg))
        #print fixs
        packfix = self.packdeliveryfix.pack(*fixs)
        sndmsg = packfix + msg + self.emp(8)
        return sndmsg
                
    def svrproc(self, sock, sockid):
        '''proc one connect work'''
        self.initcountval(sockid)
        para = self.getsockpara(sockid)
        para.tcpconnect = True
        self.sockslink += 1
        time.sleep(1)
        print "this is the ", self.sockslink, " socket links, sock id is ", sockid
        
        #recv loop
        print "sockid : ", sockid, " start rcv loop"
        self.rcvloop(sock,para)
        #close
        sock.close()
        self.removecountval(sockid)
        self.sockslink -= 1
        print "sockid ", sockid, " terminated, now has ", self.sockslink, " links."
        
    def rcvloop(self, sock, para):
        '''rcv data loop'''
        #para = self.getsockpara(sockid)
        BUFSIZE = self.cfg.getbufsize()
        # init
        self.initrcvloop(para)
        data = ''
        # rcv loop start
        sock.settimeout(self.cfg.getunbindtime())
        isneedsndunbind = True
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
            
            #print data
            #data = self.rcvproc(data, sock, para)
            while True:
                if data == '' or len(data) < 20:
                    break
                try:
                    cmds = self.packcmd.unpack(data[0:20])
                    print "cmds :", cmds
                except Exception, e:
                        print "err unpack: ", data, ' err : ', e
                        data = None
                        break
                if len(data) < cmds[0]:
                        #print 'err data length', cmds[0]
                        break        
                if cmds[1] == self.ID_SGIP_BIND :
                    self.sndbindack(sock, cmds, para)
                elif cmds[1] == self.ID_SGIP_DELIVER_RESP :
                    print "wrong thread get delivery ack..."
                elif cmds[1] == self.ID_SGIP_SUBMIT :
                    msgid = self.sndsubmitack(sock, cmds, para)
                    #test
                    print binascii.hexlify(data[0:100])
                    '''orgnize dr data'''
                    if self.cfg.getdrloop():
                        now = time.time()
                        fixdata = self.formdrfix(msgid, data)
                        self.drque.put((now, fixdata))
                        #print fixdata
                        #print para.drque.qsize()
                elif cmds[1] == self.ID_SGIP_UNBIND :
                    self.sndunbindack(sock, cmds, para)
                    isneedsndunbind = False
                    data = None
                    break      
                else:
                    print 'unkown cmd : ', binascii.hexlify(data)
                               
                if len(data) == cmds[0]:
                        data = ''
                else :
                    data = data[cmds[0]:]         
            if data is None:
                self.tcpconnect = False
                self.appconnect = False
                print 'data proc err'
                break
        if isneedsndunbind:
            self.sndunbind(sock, para)
        time.sleep(1)
        
    def sndunbind(self, sock, para):
        sockid = para.sockid
        para.seqid += 1
        value = (20, self.ID_SGIP_UNBIND,para.seqid, 0,0)
        self.socksend(sock, self.packcmd.pack(*value))
        print 'sockid : ', sockid, 'unbind'   
    
    
    def sndbind(self, sock, para): 
        sockid = para.sockid
        para.seqid += 1
        valuecmd = (61, self.ID_SGIP_BIND,para.seqid, 0,0)
        value = (2, self.emp(16, self.cfg.getusr()), self.emp(16, self.cfg.getpwd()), self.emp(8))
        self.socksend(sock, self.packcmd.pack(*valuecmd) + self.packbind.pack(*value))
        print 'sockid : ', sockid, 'bind',  ", time : ", time.ctime()   
    
        
    def sndbindack(self, sock, cmds, para): 
        sockid = para.sockid
        valuecmd = (29, self.ID_SGIP_BIND_RESP,cmds[2], cmds[3],cmds[4])
        value = (0, self.emp(8))
        self.socksend(sock, self.packcmd.pack(*valuecmd) + self.packbindrsp.pack(*value))
        print 'sockid : ', sockid, 'bindack'   
        
    def sndunbindack(self, sock, cmds, para):
        sockid = para.sockid
        valuecmd = (20, self.ID_SGIP_UNBIND_RESP,cmds[2], cmds[3],cmds[4])
        self.socksend(sock, self.packcmd.pack(*valuecmd))
        print 'sockid : ', sockid, 'unbindack' , ", time : ", time.ctime()  
        
    def sndsubmitack(self, sock, cmds, para):
        '''submit ack'''
        para.rcvnum += 1
        #msgid = self.genmsgid_ack()
        valuecmd = (29, self.ID_SGIP_SUBMIT_RESP, cmds[2],cmds[3],cmds[4])
        msgid = (cmds[2], cmds[3],cmds[4])
        value = (0, self.emp(8))  
        self.socksend(sock, self.packcmd.pack(*valuecmd) + self.packbindrsp.pack(*value))
        para.seqid = cmds[2]+1
        if para.rcvnum % self.cfg.getptnum() == 0:
            print "sockid : ", para.sockid, ' : get  : ', para.rcvnum , ", time : ", time.ctime()
        return msgid
        
    def startsvr(self):
        sockthread = threading.Thread(target=self.startsvrImp)
        sockthread.start()  
         
    def startsvrImp(self):
        '''enter main listen loop'''
        sockaddr = self.cfg.getsockaddr()
        socklisten = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print sockaddr
        socklisten.bind(sockaddr)
        socklisten.listen(self.cfg.getlistennum())
        while True : 
            print sockaddr, 'waiting for connection...'
            sock, addr = socklisten.accept()
            print ('...connected from:', addr)
            self.tcpconnect = True
            # start snd thread
            self.sockid += 1
            sockthread = threading.Thread(target=self.svrproc, args=(sock, self.sockid))
            sockthread.start()
            
        socklisten.close()
        
    

    def startclt(self):
        #sockaddr = self.cfg.getsockaddr()
        sockthread = threading.Thread(target=self.cltImp)
        sockthread.start()  
        sockthreaddr = threading.Thread(target=self.drsndImp)
        sockthreaddr.start()       
        
        
    def cltImp(self):
        '''connect the server and do snd rcv procs'''
        sleeptime = self.cfg.getsleeptime()
        cltsockid = 1000
        sndcnt = 0
        totalcnt = 0
        while totalcnt < self.cfg.getsndloop():
            #time.sleep(sleeptime)
            # connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = self.cfg.getremotesockaddr()
            #print server_address
            sock.connect(server_address)
            sock.setblocking(True)
            cltsockid += 1
            if cltsockid >=10000:
                cltsockid = 1
            # sock proc
            print "connected ", server_address
            '''proc one connect work'''
            self.initcountval(cltsockid)
            para = self.getsockpara(cltsockid)
            para.tcpconnect = True
            self.sockslink += 1              
            rt = self.sndcltdata(sock, para) 
            sndcnt += rt  
            totalcnt += rt  
            # end sock
            sock.close()
            self.removecountval(cltsockid)
            self.sockslink -= 1
            print "sockid ", cltsockid, " terminated, now has ", self.sockslink, " links."
            
            if sndcnt >= self.cfg.getptnum():
                print "deliver count: ", totalcnt, ", time : ", time.ctime() 
                sndcnt = 0 
            time.sleep(sleeptime)
        print "deliver deliver is : ", totalcnt,  ", time : ", time.ctime()  
            
    def drsndImp(self):
        cltsockid = 10001
        drdelay = self.cfg.getdrdelay()
        totalcnt = 0
        sndcnt = 0
        while True:
            while self.drque.qsize() > 0:
                snddata = self.drque.get()
                drdata = snddata[1]
                drtime = snddata[0]
                #wait dr time
                while time.time() - drtime < drdelay :
                    #print "now is ", time.time, "; snd time is : ", drtime 
                    time.sleep(0.1)
                    
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_address = self.cfg.getremotesockaddr()
                #print server_address
                sock.connect(server_address)
                sock.setblocking(True)
                cltsockid += 1
                if cltsockid >=100000:
                    cltsockid = 1
                self.initcountval(cltsockid)
                para = self.getsockpara(cltsockid)
                para.tcpconnect = True
                self.sockslink += 1              
                sndcnt += self.snddrdata(sock, para, drdata)     
                # end sock
                sock.close()
                self.removecountval(cltsockid)
                self.sockslink -= 1
                print "sockid ", cltsockid, " terminated, now has ", self.sockslink, " links."
            time.sleep(0.1)
            if sndcnt >= self.cfg.getptnum():
                totalcnt += sndcnt
                sndcnt = 0
                print "dr count: ", totalcnt, ", time : ", time.ctime()  
        print "dr deliver is : ", totalcnt,  ", time : ", time.ctime()  
    
    
    def snddrdata(self, sock, para, drdata):
        self.sndbind(sock, para)
        sock.settimeout(self.cfg.getunbindtime())
        BUFSIZE = 4096
        try:
            data = sock.recv(BUFSIZE)
        except Exception, e:
            print 'recv err ', e
            para.tcpconnect = False
            para.appconnect = False
            return 0
        if data == '' or len(data) < 20:
            print 'recv data err'
            para.tcpconnect = False
            para.appconnect = False
            return 0
        cmds = self.packcmd.unpack(data[0:20])
        print "cmds :", cmds
        rt = self.packbyte.unpack(data[20])[0]
        if cmds[1] <> self.ID_SGIP_BIND_RESP or rt<>0:
            print "bind err: %x "% cmds[1],' , errcode :',rt
            return 0
        self.snddr(sock, para,drdata)
        try:
            data = sock.recv(BUFSIZE)
        except Exception, e:
            print 'recv err ', e
            para.tcpconnect = False
            para.appconnect = False
            return 1
        if data == '' or len(data) < 20:
            print 'recv data err'
            para.tcpconnect = False
            para.appconnect = False
            return 1
        cmds = self.packcmd.unpack(data[0:20])
        print "cmds :", cmds
        rt = self.packbyte.unpack(data[20])[0]
        if cmds[1] <> self.ID_SGIP_REPORT_RESP or rt<>0:
            print "report err: %x"% cmds[1],' , errcode :',rt
        self.sndunbind(sock, para)
        time.sleep(0.1)
        return 1
    
    def formdrfix(self, msgid, data):
        fixdata = []
        fixdata.append(msgid)
        fixdata.append(data[63:63+21])
        return fixdata    
   
    def snddr(self, sock, para, drdata):
        sockid = para.sockid
        para.seqid += 1
        valuecmd = (64, self.ID_SGIP_REPORT,para.seqid, para.seqid,para.seqid)
        value = (drdata[0][0],drdata[0][1],drdata[0][2], 0, self.emp(21,drdata[1]), 0,0,self.emp(8))
        self.socksend(sock, self.packcmd.pack(*valuecmd) + self.packdr.pack(*value))
        print 'sockid : ', sockid, 'report', ", time : ", time.ctime()    
        
        
        
    
    def sndcltdata(self, sock, para):
        self.sndbind(sock, para)
        sock.settimeout(self.cfg.getunbindtime())
        BUFSIZE = 4096
        try:
            data = sock.recv(BUFSIZE)
        except Exception, e:
            print 'recv err ', e
            para.tcpconnect = False
            para.appconnect = False
            return 0
        if data == '' or len(data) < 20:
            print 'recv data err'
            para.tcpconnect = False
            para.appconnect = False
            return 0
        cmds = self.packcmd.unpack(data[0:20])
        print "cmds :", cmds
        rt = self.packbyte.unpack(data[20])[0]
        if cmds[1] <> self.ID_SGIP_BIND_RESP or rt<>0:
            print "bind err: %x "% cmds[1],' , errcode :',rt
            return 0
        self.sndmsg(sock, para)
        try:
            data = sock.recv(BUFSIZE)
        except Exception, e:
            print 'recv err ', e
            para.tcpconnect = False
            para.appconnect = False
            return 1
        if data == '' or len(data) < 20:
            print 'recv data err'
            para.tcpconnect = False
            para.appconnect = False
            return 1
        cmds = self.packcmd.unpack(data[0:20])
        print "cmds :", cmds
        rt = self.packbyte.unpack(data[20])[0]
        if cmds[1] <> self.ID_SGIP_DELIVER_RESP or rt<>0:
            print "snd err: %x "%cmds[1],' , errcode :',rt
        self.sndunbind(sock, para)
        time.sleep(0.1)
        #print "sockid : ", para.sockid," snd one data"
        return 1
    
    def sndmsg(self, sock, para):
        sockid = para.sockid
        para.seqid += 1
          
        valuecmd = (20+len(self.fixdata), self.ID_SGIP_DELIVER,para.seqid, 0,0)
        
        self.socksend(sock, self.packcmd.pack(*valuecmd) + self.fixdata)
        print 'sockid : ', sockid, 'delivery', ", time : ", time.ctime()          
    
                
    def startsvrandclt(self):     
        #启动接收进程
        self.startsvr()
        
        #启动发送进程
        self.startclt()
        

def main():
    parafile = 'sgip12.txt'
    if len(sys.argv) > 1:
        parafile = sys.argv[1]
    
    svr = sgip12Svr(parafile)
    svr.startsvrandclt()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"