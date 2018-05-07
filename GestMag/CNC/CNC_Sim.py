'''
Created on 12 mar 2018

@author: Emanuele
'''
import threading


status_CNC = {"free":0, "busy":1, "waiting_unloading_WIP":2, "broken":3}
type_CNC = {"ver_cut":0, "ori_cut":1, "sagomatore":2}
prog_CNC = {"franco":0, "pippo":0}

class CNC_Sim(object):
    def __init__(self, cncProp):
        self.name = cncProp['name']
        self.addr = cncProp['addr']
        self.type = cncProp['type']
        self.status = status_CNC["free"]
        self.nCuts = 0
        self.wCut = 0
        self.blockID_lavorato = None
        self.program = None
        self.lavTimer = None
        pass
    def getName(self):
        return self.name
    def getStatus(self):
        return self.status
    def getData(self):
        stat = {'name':self.name,
              'status':self.status,
              'addr': self.addr,
              'type':self.type,
              'blockID':self.blockID_lavorato,
              'program':self.program
            }
        return stat
    def setStatus(self, s):
        self.status = s
        pass     
    def setBusy(self):
        self.status = status_CNC["busy"]
        pass    
    def setFree(self):
        self.status = status_CNC["free"]
        pass
    def setWaiting(self):
        self.status = status_CNC["waiting_unloading_WIP"]
        pass    
    def setBroken(self):
        self.status = status_CNC["broken"]
        pass        
    def setProgram(self, job):
        if self.type == type_CNC["sagomatore"]:
            self.program = job['program']
            self.time = job['time']
            pass
        pass
    def setCuts(self, job):
        if not self.type == type_CNC["sagomatore"]:
            self.nCuts = job['n']
            self.wCut = job['w']
            self.time = job['time']
            pass
        pass 
    def loadPiece (self, blockID_new_piece):
        self.blockID_lavorato = blockID_new_piece
        self.status = status_CNC["busy"]
        self.lavTimer = threading.Timer(self.time, self.setWaiting)
        pass    
    def unloadPiece (self):
        self.blockID_lavorato = None
        self.status = status_CNC["free"]
        self.lavTimer = None
        pass
    
