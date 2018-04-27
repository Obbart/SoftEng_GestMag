'''
Created on 12 mar 2018

@author: Emanuele
'''

status_CNC={"free":0,"busy":1,"waiting_unloading_WIP":2,"broken":3}
type_CNC={"ver_cut":0,"ori_cut":1,"sagomatore":2}
prog_CNC={"franco":0,"pippo":0}

class CNC_Sim(object):
    def __init__(self, params):
        self.status=status_CNC["free"]
        self.blockID_lavorato=""
        self.addr=0
        self.type=type_CNC["ver_cut"]
        self.program=""
        pass
    
    def setStatus(self,s):
        self.status=s
        pass  
    
    def setBusy(self):
        self.status=status_CNC["busy"]
        pass
    
    def setFree(self):
        self.status=status_CNC["free"]
        pass
    
    def setWaiting(self):
        self.status=status_CNC["waiting_unloading_WIP"]
        pass
    
    def setBroken(self):
        self.status=status_CNC["broken"]
        pass
    
    def setType(self,tipo):
        self.type=tipo
        pass
    
    def setProgram(self,p):
        if self.type==type_CNC["sagomatore"]:
            self.program=p
            return
        pass
    def loadPiece (self,blockID_new_piece):
        self.blockID_lavorato=blockID_new_piece
        self.status=status_CNC["busy"]
        pass
    
    def unloadPiece (self):
        self.blockID_lavorato=""
        self.status=status_CNC["free"]
        pass
    