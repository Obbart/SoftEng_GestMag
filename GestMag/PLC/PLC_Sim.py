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
    def __init__(self):
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

class CRANE(PLC_Sim):
    def __init__(self,s=2):
        self.act_Pos=[0,0]
        self.dest=[0,0]
        self.range=0
        self.speed=s
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
    def calcTime(self,d):
        s=self.getPos()
        return ((s[0]-d[0])**2 +(s[1]-d[1])**2)/self.speed
    
class BUFFER(PLC_Sim):
    def __init__(self,addr):
        self.addr=addr
        self.blockID_loaded=''
        pass
    def setAddr(self,addr):
        self.addr=addr
        pass
    def simNewBlock(self,l):
        blkp={
        "materialID": random.choice(l),
        "blockWidth": random.randrange(100, 200, 50),
        "blockHeight": random.randrange(100, 200, 50),
        "blockLenght": random.randrange(100, 200, 50)}
        blk=BLOCK(prop=blkp,new=True)
        self.loadPiece(blk.blockID)
        return blk
        