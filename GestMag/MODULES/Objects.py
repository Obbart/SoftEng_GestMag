'''
Created on 26 apr 2018

@author: Emanuele
'''

import uuid, time

status_CNC = {"free":0, "busy":1, "waiting_unloading_WIP":2, "broken":3}
type_CNC = {"ver_cut":0, "ori_cut":1, "sagomatore":2}

status_MP = {"ready":0, "not_ready":1}
type_Mat = {"a":0, "b":1} 
status_PLC = {"free":0, "busy":1, "broken":2}
status_CELL = {"free":0, "busy":1} 

prog_CNC = {"franco":0, "pippo":0}
    
class MATERIAL():
    def __init__(self, prop):
        self.matID = prop['materialID']
        self.lift = prop['lift']
        self.density = prop['density']
        self.color = prop['color']
        self.restTime = time.strptime(prop['restTime'], "%H:%M")
        pass

class BLOCK():
    def __init__(self, prop, new=False):
        self.width = prop['width']
        self.height = prop['height']
        self.length = prop['length']
        if not new:
            self.blockID = prop['blockID']
            self.date = time.mktime(time.strptime(prop['date'], '%c'))
        else:
            self.blockID = uuid.uuid4().hex
            self.date = time.time()
        self.ready = False
        self.material=None
        pass    
    def setDimension(self, width, height, length):
        self.width = width
        self.height = height
        self.length = length
        pass   
    def setMaterial(self, mat):
        self.material=mat
        pass   
    def getMaterial(self):
        return self.material  
    def checkReady(self):
        if time.time() - self.date > self.material.restTime:
            self.ready = True
        pass


class CELL():
    def __init__(self,prop):
        self.cellID = prop['cellID']
        self.status = prop['cellStatus']
        self.blockID = prop['blockID']
        self.addr = (prop['cellX'],prop['cellY'])
        pass
    def setStatus(self, s):
        self.status = s
        pass
    def loadPiece(self, np):
        self.blockID = np
        self.status = status_CELL["busy"]
        pass
    def unloadPiece(self):
        self.blockID = None
        self.status = status_CELL["free"]
        pass

    
class WIP(BLOCK):
    
    def __init__(self, params):
        self.step_seq = 0
        self.recipe = ""
        pass
    def setStep(self, st):
        self.step_seq = st
        pass
    def setRecipe(self, rec):
        self.recipe = rec
        pass
    
class RECIPE():
    def __init__(self, prop):
        self.recipeID = prop['recipeID']  # nome ricetta
        self.matID = prop['matID']  # materiale
        self.n_ve_cut = prop['ncv']  # numero tagli verticali
        self.n_or_cut = prop['nco']  # numero tagli orizzontali
        self.w_ve_cut = prop['scv']  # spessore tagli verticali
        self.w_or_cut = prop['sc0']  # spessore tagli orizzontali
        self.sa_prog = prop['prg']  # programma sagomatura
        self.seq = "DEFAULT"  # sequenza
        pass
    def setSequence(self,s):
        self.seq=s
        pass
               

class ORDER(object):
    def __init__(self, params):  # NB one product type per order
        self.client = ""
        self.exp_date = time.strftime("%c")
        self.product = ""
        self.n_product = 0
        self.ID_code = ""
        pass
    def newOrder(self, c, ed, p, np, i):
        self.client = c
        self.exp_date = ed
        self.product = p
        self.n_product = np
        self.ID_code = i
        pass
    def prodMinus1(self):
        self.n_product -= 1
        pass

