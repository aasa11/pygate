# !/usr/bin/
# coding=gbk
'''
Created on 2013/08/01

@summary: 

@author: huxiufeng
'''

from svrbase import *
import struct
import sys
import binascii


class cmpp20Svr(svrbase):
    def __init__(self, parafile):
        svrbase.__init__(self, parafile)
        
    def packdefine(self):
        '''initialize the pack data, realize by derived class'''
        print "cmpp20 pack define init"
        svrbase.packdefine(self)
        self.packcmd = struct.Struct('!3I')
        self.packconnect = struct.Struct('!3I 16s B I')
        self.packconnectack = struct.Struct('!3I B 16s B')
        self.packtestack = struct.Struct('!3I B')
        self.packcommitack = struct.Struct('!3I 2I B')
        self.packterminateack = struct.Struct('!3I')
        self.packdrfix = struct.Struct('!21s 10s B B B 21s B B 2I 7s 10s 10s 21s I 8s')
        self.packdr = struct.Struct('!3I 2I 125s')
        #snd msg data
        self.packsndfix= struct.Struct('!21s 10s 3B 21s 2B')
        
        #para transfer
        self.packbyte = struct.Struct('!B')
        
    
    def sndconnect(self, sock, para):
        '''snd connect cmd, realize by derived class'''
        '''cmpp20 do not snd connect , it just wait connect'''
        pass
    
    def sndterminate(self, sock , para):
        '''snd terminate cmd, realize by derived class'''
        '''cmpp20 do not snd terminate , it just wait terminate'''
        pass
    
    def sndmsg(self, sock , para):
        '''snd msg, realize by derived class'''
        #para = self.getsockpara(sockid)
        sockid = para.sockid
        para.seqid += 1
        msgid = self.genmsgid() 
        value = (20+len(para.snddata), self.ID_DELIVERY, para.seqid, msgid[0], msgid[1], para.snddata)
        packvalue = para.packsnd.pack(*value)
        sock.sendall(packvalue)
        #print "snd value", binascii.hexlify(packvalue)
    
    def sndconnectack(self, sock, cmds, para):
        '''connect ack'''
        #para = self.getsockpara(sockid)
        sockid = para.sockid
        value=(30, self.ID_CONNECT_ACK, cmds[2],0,self.emp(16),0)
        sock.sendall(self.packconnectack.pack(*value))
        print 'sockid : ', sockid, ' connect ack'
        para.appconnect = True
        para.seqid = cmds[2]+1
        time.sleep(1)
        
        
    def sndactivetestack(self, sock, cmds, para):
        '''active test ack'''
        sockid = para.sockid
        value = (13, self.ID_ACTIVETEST_ACK,cmds[2], 0)
        sock.sendall(self.packtestack.pack(*value))
        print 'sockid : ', sockid, 'active test ack'
        
    def procdeliveryack(self, cmds, para, data):
        '''delivery ack'''
        rt = self.packbyte.unpack(data[20])[0]
        if rt == 0: #success
            para.sndsucc += 1
            if para.sndsucc % self.cfg.getptnum() == 0:
                print "sockid : ", para.sockid, ' : snd succ : ', para.sndsucc, " time : ", time.ctime()
        else :  #failure
            para.sndfail += 1
            print "sockid : ", para.sockid, " : snd fail ", para.sndfail, " , rt : ", rt         
        return
    
    def sndsubmitack(self, sock, cmds, para):
        '''submit ack'''
        para.rcvnum += 1
        msgid = self.genmsgid()
        value = (21, self.ID_SUBMIT_ACK, cmds[2], msgid[0], msgid[1], 0)  
        sock.sendall(self.packcommitack.pack(*value))  
        para.seqid = cmds[2]+1
        if para.rcvnum % self.cfg.getptnum() == 0:
            print "sockid : ", para.sockid, ' : get  : ', para.rcvnum , ", time : ", time.ctime()
        return msgid
    
    def sndterminateack(self, sock, cmds , para):
        '''terminate ack'''
        value = (12, self.ID_DISCONNECT_ACK, cmds[2])
        sock.sendall(self.packterminateack(*value))
        print "send terminate ack..."
        para.appconnect = False
        
    
    def snddr(self, sock , para, drdata):
        '''snd dr, realize by the derived class'''
        fixdata = drdata
        para.seqid += 1
        msgid = self.genmsgid()
        value = (20 + 125, self.ID_DELIVERY, para.seqid, msgid[0], msgid[1], fixdata)
        packvalue = self.packdr.pack(*value)
        #print binascii.hexlify(packvalue)
        sock.sendall(packvalue)
        para.drsnd += 1
        if para.drsnd % self.cfg.getptnum() == 0 :
            print "sockid : ", para.sockid, " : snd dr : ", para.drsnd, " : time : ", time.ctime()
        return
    
    def formdrfix(self, msgid, data):
        '''form the fix part of the dr report'''
        '''for tmp proc'''
        #self.packdrfix = struct.Struct('!21s 10s B B B 21s B B 2I 7s 10s 10s 21s I 8s')
        value = (self.emp(21),
                 self.emp(10),
                 0,0,0,
                 self.emp(21),
                 1, 68, 
                 msgid[0], msgid[1],
                 'DELIVRD', 
                 self.emp(10),
                 self.emp(10),
                 self.emp(21),
                 0, self.emp(8))
        packvalue = self.packdrfix.pack(*value)
        return packvalue    
    
    def sndactivetest(self, sock , para):
        '''snd activetest, realize by the derived class'''
        pass
    
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
            if cmds[1] == self.ID_CONNECT :
                self.sndconnectack(sock, cmds, para)
            elif cmds[1] == self.ID_ACTIVETEST :
                self.sndactivetestack(sock, cmds, para)
            elif cmds[1] == self.ID_DELIVERY_ACK :
                self.procdeliveryack(cmds, para, data)
            elif cmds[1] == self.ID_SUBMIT :
                msgid = self.sndsubmitack(sock, cmds, para)
                '''orgnize dr data'''
                if self.cfg.getdrloop():
                    now = time.time()
                    fixdata = self.formdrfix(msgid, data)
                    para.drque.put((now, fixdata))
                    #print fixdata
                    #print para.drque.qsize()
            elif cmds[1] == self.ID_DISCONNECT :
                self.sndterminateack(sock, cmds, para)  
            elif cmds[1] == self.ID_ACTIVETEST_ACK:
                print "get active test ack ..."       
            else:
                print 'unkown cmd : ', binascii.hexlify(data)
                           
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
        des = self.cfg.getdes()
        msg = self.cfg.getmsg()
        coding = self.cfg.getcoding()
        svcid = self.cfg.getsvcid()
        #self.packsndfix= struct.Struct('!21s 10s 3B 21s 2B')
        fixs = (self.emp(21,des), 
                   self.emp(10, svcid),
                   0,0,coding,
                   self.emp(21, src),
                   0, len(msg))
        #print fixs
        packfix = self.packsndfix.pack(*fixs)
        sndmsg = packfix + msg + self.emp(8)
        prsnd = '!3I 2I %ds' % len(sndmsg)
        packsnd = struct.Struct(prsnd)
        para.snddata = sndmsg
        para.packsnd = packsnd
        
    
    def initrcvloop(self, para):
        '''do some init for rcv loop, realize by derived class'''
        pass
        


#----------------------It is a split line--------------------------------------

def main():
    # svr
    parafile = 'cmpp20.txt'
    if len(sys.argv) > 1:
        parafile = sys.argv[1]
    
    svr = cmpp20Svr(parafile)
    svr.startsvr()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"
