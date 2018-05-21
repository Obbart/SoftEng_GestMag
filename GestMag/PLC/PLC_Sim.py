'''
Created on 12 mar 2018

@author: Emanuele
'''
import random
from MODULES.Objects import BLOCK


status_CNC={"free":0,"busy":1,"waiting_unloading_WIP":2,"broken":3}
type_CNC={"ver_cut":0,"ori_cut":1,"sagomatore":2}

status_MP={"ready":0,"not_ready":1}
type_Mat={"a":0,"b":1} 
status_PLC={"free":0,"busy":1,"loading":2,"unloading":4,"moving":5,"broken":6}
status_CELL={"free":0,"busy":1} 


def getKey(mydict, val):
    return list(mydict.keys())[list(mydict.values()).index(val)]

class PLC_Sim(object):
    def __init__(self):
        self.status=status_PLC["free"]
        self.blockID_loaded=None
        self.block=None
        pass
    def setFree(self):
        self.blockID_loaded=None
        self.block=None
        self.status=status_PLC["free"]
        pass
    def loadPiece(self,blockID):
        self.blockID_loaded=blockID
        self.status=status_PLC["loading"]
        pass
    def unloadPiece(self):
        self.blockID_loaded=None
        self.status=status_PLC["unloading"]
        pass

class CRANE(PLC_Sim):
    def __init__(self,s=2):
        super(CRANE, self).__init__()
        self.act_Pos=[0,0]
        self.dest=[0,0]
        self.range=0
        self.speed=s
        pass
    def setDest(self,d):
        self.status=status_PLC['moving']
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
    def getStat(self):
        return {'status':getKey(status_PLC, self.status),
                'source':self.act_Pos,
                'dest':self.dest,
                'blockID':self.blockID_loaded}
    
class BUFFER(PLC_Sim):
    def __init__(self,addr):
        super(BUFFER, self).__init__()
        self.addr=addr
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
        self.block=blk
        return blk
    def getStat(self):
        if self.block:
            b=self.block.materialID
            d=self.block.date
        else:
            b=''
            d=''
        return {'status':getKey(status_PLC, self.status),
                'material':b,
                'date':d,
                'blockID':self.blockID_loaded}
    
    