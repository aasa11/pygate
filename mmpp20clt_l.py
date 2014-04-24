#!/usr/bin/
#coding=gbk

'''
@summary: 

@author: huxiufeng
'''

import time
import svrbase
import struct
import sys
import binascii
import datetime
import hashlib
from mmpp20clt import mmpp20clt

#----------------------It is a split line--------------------------------------

class mmpp20_clt_l(mmpp20clt):
    def __init__(self, parafile):
        '''init file , call father's init'''
        mmpp20clt.__init__(self, parafile)
        
    def initsndloop(self, para):
        self.total_msg = 1
        para.snddata = []
        para.packsnd = []
        '''do some init for snd loop, realize by derived class'''
        '''init snd data'''
        src = self.cfg.getsrc()
        des = self.cfg.getdes().split(';')
        print "des phones : ", des
        msgori = self.cfg.getmsg()
        coding = self.cfg.getcoding()
        emiclass = self.cfg.getemiclass()
        svcid = self.cfg.getsvcid()
        binascii.hexlify(msgori)
        msgdatas = self.getsnddata(coding, msgori)
        '''only snd the first msg'''
        msgs = msgdatas
        self.total_msg = len(msgs)
        for msg in msgs:
            #self.packsndfix= struct.Struct('!16s 4B 10s 21s 3B 16s 16s 21s B')
            fixs = (self.emp(16),
                    self.cfg.getpktotal(),self.cfg.getpknumber(),self.cfg.getdr(),self.cfg.getpriority(),
                    self.emp(10,svcid),
                    self.emp(21,self.cfg.getpayer()),
                    self.cfg.getprotocolid(),emiclass,coding,
                    (self.emp(16) if self.cfg.getvalidperiod() == '0'  else self.emp(16, self.cfg.getvalidperiod()) ),
                    (self.emp(16) if self.cfg.getscheduletime() == '0'  else self.emp(16, self.cfg.getscheduletime()) ),
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
            para.snddata.append(sndmsg)
            para.packsnd.append(packsnd)

    def sndmsg(self, sock , para):
        '''snd msg, realize by derived class'''
        for idx in range(len(para.snddata)-1, -1, -1):
            para.seqid += 1 
            value = (12+len(para.snddata[idx]), self.ID_SUBMIT, para.seqid, para.snddata[idx])
            packvalue = para.packsnd[idx].pack(*value)
            self.socksend(sock, packvalue)
            #print "sockid : ", para.sockid, "snd value", binascii.hexlify(packvalue)


#----------------------It is a split line--------------------------------------

def main():
    # clt
    parafile = 'mmpp20.txt'
    if len(sys.argv) > 1:
        parafile = sys.argv[1]
    
    clt = mmpp20_clt_l(parafile)
    clt.startclt()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    start_time = time.time()
    
    main()
    
    end_time = time.time()  
    print "It's ok"
    print "start:[",time.ctime(start_time),"]"
    print "end:  [",time.ctime(end_time),"]"
    print "last: [",(end_time-start_time),"s]"