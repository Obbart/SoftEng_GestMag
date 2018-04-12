'''
Created on 15 mar 2018

@author: Emanuele
'''
import logging
import sys


class MyLogger(object):
    def __init__(self, name, lvl):
        
        self.name=name
        self.level=lvl
         
        self.hld=logging.StreamHandler(sys.stdout)
        self.hld.setLevel(lvl)
        
        self.fmt = logging.Formatter('%(name)s | %(funcName)s \t%(levelname)s\t%(message)s')
        self.hld.setFormatter(self.fmt)
        return

    def logger(self):
        lg=logging.getLogger(self.name)
        lg.setLevel(self.level)
        if len(lg.handlers)<1:
            lg.addHandler(self.hld)
        return lg
    
    