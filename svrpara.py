# !/usr/bin/
# coding=gbk
'''
Created on 2013/08/01

@summary: This class is for the svr para reader

@author: huxiufeng
'''

import ConfigParser
import sys


class svrpara:
    '''this is the config parser class for the svr'''
    def __init__(self, parafile):
        '''get the config file and init the cfg data'''
        self.parafile = parafile
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(self.parafile)
        self.printcfg(self.cfg)
        self.cfgdefine()
        
    def printcfg(self, cfg):
        '''print the configration from the cfg'''
        # cfg = ConfigParser.ConfigParser()
        sections = cfg.sections()
        for sec in sections :
            print "section : ", sec
            print cfg.items(sec)
            
    def cfgdefine(self):
        '''define the paras'''
        # secsions
        self.sec_sys = 'sys'
        self.sec_snd = 'snddata'
        self.sec_connect = 'connect'
    
        # options
        self.op_host = 'host'
        self.op_port = 'port'
        self.op_listen = 'listennum'
        self.op_loop = 'sndloop'
        self.op_sleep = 'sleep'
        self.op_ptnum = 'ptnum'
        self.op_bufsize = 'bufsize'
        self.op_timeout = 'timeout'
        self.op_usr = 'usr'
        self.op_pwd = 'pwd'
        
        self.op_src = 'src'
        self.op_des = 'des'
        self.op_msg = 'msg'
        self.op_coding = 'coding'
        self.op_svcid = 'svcid'
        self.op_needdr = 'needdr'
        
        self.op_sndconnect = 'sendconnect'
        self.op_sndterminate = 'sendterminate'
        self.op_drdelay = 'drdelay'
        self.op_winsize = 'winsize'
        self.op_drloop = 'drloop'
        self.op_activetestloop = 'activetestloop'
        self.op_activetestgap = 'activetestgap'
        
    def getlistennum(self):
        '''get listen numbers from para file'''
        num = self.cfg.getint(self.sec_sys, self.op_listen)
        return num
    
    def getsockaddr(self):
        '''get the host para from the para file'''
        host = self.cfg.get(self.sec_sys, self.op_host)
        port = self.cfg.getint(self.sec_sys, self.op_port)
        addr = (host, port)
        return addr
    
    def getsndconnect(self):
        '''get the value of snd connect'''
        val = self.cfg.getint(self.sec_connect, self.op_sndconnect)
        if val == 1:
            return True
        return False 
    
    def getsndterminate(self):
        '''get the value of snd terminate'''
        val = self.cfg.getint(self.sec_connect, self.op_sndterminate)
        if val == 1:
            return True
        return False
    
    def getsndloop(self):
        val = self.cfg.getint(self.sec_sys, self.op_loop)      
        return val
    
    def getsleeptime(self):
        val = self.cfg.getfloat(self.sec_sys, self.op_sleep)      
        return val
    
    def getptnum(self):
        val = self.cfg.getint(self.sec_sys, self.op_ptnum)      
        return val
    
    def getbufsize(self):
        val = self.cfg.getint(self.sec_sys, self.op_bufsize)      
        return val
    
    def getdefualttimeout(self):
        val = self.cfg.getint(self.sec_sys, self.op_timeout)      
        return val
    
    def getusr(self):
        val = self.cfg.get(self.sec_sys, self.op_usr)      
        return val
    
    def getpwd(self):
        val = self.cfg.get(self.sec_sys, self.op_pwd)      
        return val
    
    def getsrc(self):
        val = self.cfg.get(self.sec_snd, self.op_src)
        return val
    
    def getdes(self):
        val = self.cfg.get(self.sec_snd, self.op_des)
        return val
    
    def getmsg(self):
        val = self.cfg.get(self.sec_snd, self.op_msg)
        return val
    
    def getcoding(self):
        val = self.cfg.getint(self.sec_snd, self.op_coding)
        return val
    
    def getsvcid(self):
        val = self.cfg.get(self.sec_snd, self.op_svcid)
        return val
    
    def getdrdelay(self):
        val = self.cfg.getint(self.sec_connect, self.op_drdelay)
        return val
    
    def getwinsize(self):
        val = self.cfg.getint(self.sec_sys, self.op_winsize)
        return val
    
    def getdr(self):
        val = self.cfg.getint(self.sec_snd, self.op_needdr)
        return val
    
    def getdrloop(self):
        val = self.cfg.getint(self.sec_connect, self.op_drloop)
        if val == 1:
            return True
        return False
    
    def getactivetestloop(self):
        val = self.cfg.getint(self.sec_connect, self.op_activetestloop)
        if val == 1:
            return True
        return False
    
    def getactivetestgap(self):
        val = self.cfg.getint(self.sec_connect, self.op_activetestgap)
        return val
        
        

#----------------------It is a split line--------------------------------------

def main():
    parafile = 'mmpp20.txt'
    if len(sys.argv) > 1:
        parafile = sys.argv[1]
    
    para = svrpara(parafile)
    
    
    print para.getlistennum()
    print para.getsockaddr()
    print para.getsndconnect()
    print para.getsndterminate()
    print para.getsndloop()
    print para.getsleeptime()
    print para.getptnum()
    print para.getbufsize()
    print para.getdefualttimeout()
    print para.getusr()
    print para.getpwd()
    
    print para.getsrc()
    print para.getdes()
    print para.getmsg()
    print para.getcoding()
    print para.getsvcid()
    print para.getdrdelay()
    print para.getwinsize()
    print para.getdr()
    print para.getdrloop()
    print para.getactivetestloop()
    print para.getactivetestgap()
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"
