#!/usr/bin/
#coding=gbk
'''
Created on 2013年10月17日

@summary: 

@author: huxiufeng
'''


import sys
import ConfigParser


def change_sleep(file_list, sleepdata):
    for filename in file_list:
        cfg = ConfigParser.ConfigParser()
        cfg.read(filename)
        cfg.set(r'sys',r'sleep', str(sleepdata))
        #cfg.save()
        f = open(filename, 'w')
        cfg.write(f)
        f.close()
        
def change_values(file_list, section_name, option_name, value):
    for filename in file_list:
        cfg = ConfigParser.ConfigParser()
        cfg.read(filename)
        cfg.set(section_name, option_name, value)
        #cfg.save()
        f = open(filename, 'w')
        cfg.write(f)
        f.close()
    
        

#----------------------It is a split line--------------------------------------

def main():
    file_list = [r'mmpp20.txt']
    print sys.argv
    if len(sys.argv) <2:
        return
    
    for i in range(1,len(sys.argv)):
        paras = sys.argv[i].split('##')
        if len(paras) < 3:
            print "error para : ", sys.argv[i]
            continue
        change_values(file_list, paras[0], paras[1], paras[2])
    
    
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"