'''
Created on 2013/07/08

@author: huxiufeng
'''
import os

#----------------------It is a split line--------------------------------------

def main():
    pass

#----------------------It is a split line--------------------------------------

def main_dir():
    paths = r"F:\Code\ecprj\zsms\src\uss"
    for _, _, files in os.walk(paths):
        for filename in files:
            first , second = os.path.splitext(filename)
            #print first, second
            if str(second).find(".c") >= 0:
                print filename
    
#----------------------It is a split line--------------------------------------

if __name__ == "__main__":
    main_dir()
    print "It's ok"