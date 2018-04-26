'''
Created on 12 mar 2018

@author: Emanuele
'''
import random
from MODULES.Objects import *

status_CNC={"free":0,"busy":1,"waiting_unloading_WIP":2,"broken":3}
type_CNC={"ver_cut":0,"ori_cut":1,"sagomatore":2}

status_MP={"ready":0,"not_ready":1}
type_Mat={"a":0,"b":1} 
status_PLC={"free":0,"busy":1,"broken":2}
status_CELL={"free":0,"busy":1} 


class PLC_Sim(object):
   
    def __init__(self, params):
        self.status=status_PLC["free"]
        self.blockID_loaded=""
        pass
    def setStatus(self,s):
        self.status=s
        pass
    def loadPiece(self,blockID):
        self.blockID_loaded=blockID
        self.status=status_PLC["busy"]
        pass
    def unloadPiece(self):
        self.blockID_loaded=""
        self.status=status_PLC["free"]
        pass
    def simNewBlock(self):
        mat='ELAST 65'
        w=random.randrange(10, 20, 1)
        h=random.randrange(10, 20, 1)
        l=random.randrange(10, 20, 1)
        blk=BLOCK(mat,w,h,l)
        self.loadPiece(blk.blockID)
        return blk

class CRANE(PLC_Sim):
    def __init__(self,params):
        self.act_Pos=0
        self.dest=0
        self.range=0
        pass
    
    def setDest(self,d):
        self.dest=d
        pass
    
    def setActPos(self,p):
        self.act_Pos=p
        pass
    def getPos(self):
        return self.act_Pos
    def setRange(self,r):
        self.range=r
        pass
    
class BUFFER(PLC_Sim):
    
    def __init__(self,addr):
        self.addr=addr
        pass
    def setAddr(self,addr):
        self.addr=addr
        pass
        