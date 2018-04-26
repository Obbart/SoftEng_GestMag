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
        self.matID = prop['matID']
        self.lift = prop['lift']
        self.density = prop['density']
        self.color = prop['color']
        self.restTime = time.strptime(prop['restTime'], "HH:mm")
        pass

class BLOCK(MATERIAL):
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
        pass
    
    def setDimension(self, width, height, length):
        self.width = width
        self.height = height
        self.length = length
        pass
    
    def getData (self):
        blk = {"matID": self.matID,
             "blockID": self.blockID,
             "width": self.width,
             "height": self.height,
             "length": self.length,
             "date":self.date}
        return blk
    
    def checkReady(self):
        if time.time() - self.date > self.restTime:
            self.ready = True
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
    
class RECIPE(object):
    def __init__(self, params):
        self.ID_code = ""  # nome ricetta
        self.mat_type = type_Mat["a"]  # materiale
        self.n_ve_cut = 0  # numero tagli verticali
        self.n_or_cut = 0  # numero tagli orizzontali
        self.n_sa_cut = 0  # numero tagli sagomatura
        self.w_ve_cut = 0  # spessore tagli verticali
        self.w_or_cut = 0  # spessore tagli orizzontali
        self.sa_prog = prog_CNC["franco"]  # programma sagomatura
        self.seq = ""  # sequenza
        pass
    def newRecipe(self, i, m, nvc, noc, nsa, wvc, woc, sp, s):
        self.ID_code = i 
        self.mat_type = m 
        self.n_ve_cut = nvc 
        self.n_or_cut = noc 
        self.n_sa_cut = nsa 
        self.w_ve_cut = wvc
        self.w_or_cut = woc 
        self.sa_prog = sp 
        self.seq = s            

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
       
class USER(object):
    def __init__(self, params):
        self.username = ""
        self.PSW = ""
        self.level = 0  # definisce il livello, se amministratore, user,tecnico...
        pass
    def newUser(self, u, p):
        self.username = u
        self.PSW = p
        self.level = 0  # di default ha il livello minore
        pass
    def setUsername(self, name):
        self.username = name
        pass
    def setPWD(self, p):
        self.PWD = p
        pass
    def setLevel(self, l):
        self.level = l
        pass

class CELL(object):
    def __init__(self, a=(0, 0), t=(200, 200)):
        self.status = status_CELL["free"]
        self.type = t  # dimensione, larghezza altezza
        self.addr = a
        self.blockID_stored = ""
        pass
    
    def setStatus(self, s):
        self.status = s
        pass
    def loadPiece(self, np):
        self.blockID_stored = np
        self.status = status_CELL["busy"]
        pass
    def unloadPiece(self):
        self.blockID_stored = ""
        self.status = status_CELL["free"]
        pass

class WH(object):  # WHAREHOUSE
    def __init__(self, params):
        self.n_row = 0
        self.n_col = 0
        self.n_cell = 0
        self.n_crane = 0
        self.dip_crane = True
        self.in_pos = 0
        self.out_pos = 0
        pass
