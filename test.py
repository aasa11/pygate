# !/usr/bin/
# coding=gbk
'''
Created on 2013/08/01

@summary: 

@author: huxiufeng
'''

class t1:
    def __init__(self):
        self.a = 1
        


#----------------------It is a split line--------------------------------------

def main():
    dic = {}
    t = t1()
    dic[1] = t
    
    m1 = dic[1]
    m1.a = 2

    m2 = dic[1]
    print m2.a
    
    m2.a = 3
    print m1.a
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main()
    print "It's ok"
