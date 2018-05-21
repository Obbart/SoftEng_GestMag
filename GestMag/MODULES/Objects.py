'''
Created on 26 apr 2018

@author: Emanuele
'''

import uuid, time
from datetime import datetime, timedelta

status_CNC = {"free":0, "busy":1, "waiting_unloading_WIP":2, "broken":3}
type_CNC = {"ver_cut":0, "ori_cut":1, "sagomatore":2}

status_MP = {"ready":0, "not_ready":1}
type_Mat = {"a":0, "b":1} 
status_PLC = {"free":0, "busy":1, "broken":2}
status_CELL = {"free":0, "busy":1} 

prog_CNC = {"franco":0, "pippo":0}
    
class MATERIAL():
    def __init__(self, prop):
        self.materialID = prop['materialID']
        self.lift = prop['lift']
        self.density = prop['density']
        self.color = prop['color']
        self.restTime = prop['restTime']
        self.cutSpeed = prop['cutSpeed']
        pass

class BLOCK():
    def __init__(self, prop, new=False):
        self.width = prop['blockWidth']
        self.height = prop['blockHeight']
        self.length = prop['blockLenght']
        self.materialID = prop['materialID']
        self.material = None
        if not new:
            self.blockID = prop['blockID']
            self.date = prop['blockProductionDate']
        else:
            self.blockID = uuid.uuid4().hex
            self.date = time.asctime()
        self.ready = False
        pass    
    def setDimension(self, width, height, length):
        self.width = width
        self.height = height
        self.length = length
        pass     
    def getData(self):
        return {
        "materialID": self.materialID,
        "blockID": self.blockID,
        "blockWidth": self.width,
        "blockHeight": self.height,
        "blockLenght": self.length,
        "blockProductionDate": self.date
        }  
    def checkReady(self):
        d = self.material.restTime.split(':')
        if (datetime.strptime(self.date, "%c") + timedelta(hours=int(d[0]), minutes=int(d[1]))) < datetime.now():
            self.ready = True
            return self.ready 
    def isReady(self):
        return self.ready


class CELL():
    def __init__(self, prop):
        self.cellID = prop['cellID']
        self.status = prop['cellStatus']
        self.addr = (prop['cellX'], prop['cellY'])
        if prop['blockID'] == '':
            self.blockID = None
        else:
            self.blockID = prop['blockID']
        if prop['wipID'] == '':
            self.wipID = None
        else:
            self.wipID = prop['wipID']
        pass
    def loadPiece(self, np):
        self.blockID = np
        self.status = status_CELL["busy"]
        pass
    def unloadPiece(self):
        self.blockID = None
        self.status = status_CELL["free"]
        pass
    def isEmpty(self):
        if self.blockID is None:
            return True
        else:
            return False

    
class WIP():
    def __init__(self, prop, new=False):
        self.materialID = prop['materialID']
        self.material = None
        self.recipeID = prop['recipeID']
        self.recipeStep = prop['recipeStep']
        if not new:
            self.wipID = prop['wipID']
        else:
            self.wipID = uuid.uuid4().hex
            pass
        pass
    def setStep(self, st):
        self.step_seq = st
        pass
    def setRecipe(self, rec):
        self.recipe = rec
        pass
    def getData(self):
        return {
        "materialID": self.materialID,
        "wipID": self.wipID,
        "recipeID":self.recipeID,
        "recipeStep":self.recipeStep
        }  
        
    
class RECIPE():
    def __init__(self, prop):
        self.recipeID = prop['recipeID']  # nome ricetta
        self.materialID = prop['materialID']  # materiale
        self.material = None
        self.n_ve_cut = prop['nVertCut']  # numero tagli verticali
        self.n_or_cut = prop['nOrCut']  # numero tagli orizzontali
        self.w_ve_cut = prop['spVertCut']  # spessore tagli verticali
        self.w_or_cut = prop['spOrCut']  # spessore tagli orizzontali
        self.sa_prog = prop['progSagom']  # programma sagomatura
        self.sa_time = prop['progTime']
        self.seq = prop["execOrder"].split(',')  # sequenza
        self.lavTimes = [0, 0, 0]
        pass
    def setTimes(self):
        if 'P' in self.seq:
            self.lavTimes[self.seq.index('P')] = self.sa_time
        if 'V' in self.seq:
            self.lavTimes[self.seq.index('V')] = self.n_ve_cut * 200 / self.material.cutSpeed
        if 'O' in self.seq:
            self.lavTimes[self.seq.index('O')] = self.n_or_cut * 200 / self.material.cutSpeed
    def setSequence(self, s):
        self.seq = s
        pass
               
class ORDER(object):
    def __init__(self, prop):  # NB one product type per order
        self.orderID = prop['orderID']
        self.expDate = prop['expDate']
        self.recipeID = prop['recipeID']
        pass
    
    def prodMinus1(self):
        self.n_product -= 1
        pass

