'''
Created on 26 mar 2018

@author: Rosso
'''
from sqlite3 import Date
from ctypes.test.test_pickling import name
 

status_CNC={"free":0,"busy":1,"waiting_unloading_WIP":2,"broken":3}
type_CNC={"ver_cut":0,"ori_cut":1,"sagomatore":2}
prog_CNC={"franco":0,"pippo":0}

status_MP={"ready":0,"not_ready":1}
type_Mat={"a":0,"b":1} 

status_PLC={"free":0,"busy":1,"broken":2}

status_CELL={"free":0,"busy":1}                                         #stato cella solo libera o occupata, per sapere stato mat vedi CUDT?



   
class PLC_Sim(object):
   
    def __init__(self, params):
        self.status=status_PLC["free"]
        self.CUDT_loaded=""
        pass
    def setStatus(self,s):
        self.status=s
        pass
    def loadPiece(self,CUDT):
        self.CUDT_loaded=CUDT
        self.status=status_PLC["busy"]
        pass
    def unloadPiece(self):
        self.CUDT_loaded=""
        self.status=status_PLC["free"]
        pass
    
class CRANE(PLC_Sim):
    def __init__(self,params):
        self.act_X=0
        self.act_Y=0
        self.dest=0
        self.range=0
        pass
    
    def setDest(self,d):
        self.dest=d
        pass
    
    def setActPos(self,x,y):
        self.act_X=x
        self.act_Y=y
        pass
    def setRange(self,r):
        self.range=r
        pass
    
class BUFFER(PLC_Sim):
    
    def __init__(self,params):
        self.addr=0
        pass
    def setAddr(self,addr):
        self.addr=addr
        pass

class CNC_Sim(object):
   
    def __init__(self, params):
        self.status=status_CNC["free"]
        self.CUDT_lavorato=""
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
    def loadPiece (self,CUDT_new_piece):
        self.CUDT_lavorato=CUDT_new_piece
        self.status=status_CNC["busy"]
        pass
    
    def unloadPiece (self):
        self.CUDT_lavorato=""
        self.status=status_CNC["free"]
        pass

class BLOCK(object):
    
    def __init__(self,params):
        self.type=""
        self.dim=[0,0,0]  #x,y,z
        self.CUDT=""
        pass
    def setDimension(self,dim):
        self.dim=dim
        pass
    def setType(self,type):
        self.type=type
        pass
    
class MP(BLOCK):
    
    def __init__(self,params):
        self.status=status_MP["not_ready"]
        pass
    def setStatus(self,status):
        self.status=status
        pass
    
class WIP(BLOCK):
    
    def __init__(self,params):
        self.step_seq=0
        self.recipe=""
        pass
    def setStep(self,st):
        self.step_seq=st
        pass
    def setRecipe(self,rec):
        self.recipe=rec
        pass
    
class RECIPE(object):
    def __init__(self,params):
        self.ID_code=""                     #nome ricetta
        self.mat_type=type_Mat["a"]         #materiale
        self.n_ve_cut=0                     #numero tagli verticali
        self.n_or_cut=0                     #numero tagli orizzontali
        self.n_sa_cut=0                     #numero tagli sagomatura
        self.w_ve_cut=0                     #spessore tagli verticali
        self.w_or_cut=0                     #spessore tagli orizzontali
        self.sa_prog=prog_CNC["franco"]     #programma sagomatura
        self.seq=""                         #sequenza
        pass
    def newRecipe(self,i,m,nvc,noc,nsa,wvc,woc,sp,s):
        self.ID_code=i 
        self.mat_type=m 
        self.n_ve_cut=nvc 
        self.n_or_cut=noc 
        self.n_sa_cut=nsa 
        self.w_ve_cut=wvc
        self.w_or_cut=woc 
        self.sa_prog=sp 
        self.seq=s            

class ORDER(object):
    def __init__(self,params):      #NB one product type per order
        self.client=""
        self.exp_date=Date
        self.product=""
        self.n_product=0
        self.ID_code=""
        pass
    def newOrder(self,c,ed,p,np,i):
        self.client=c
        self.exp_date=ed
        self.product=p
        self.n_product=np
        self.ID_code=i
        pass
    def prodMinus1(self):
        self.n_product-=1
        pass
       
class USER(object):
    def __init__(self,params):
        self.username=""
        self.PSW=""
        self.level=0            #definisce il livello, se amministratore, user,tecnico...
        pass
    def newUser(self,u,p):
        self.username=u
        self.PSW=p
        self.level=0            #di default ha il livello minore
        pass
    def setUsername(self,name):
        self.username=name
        pass
    def setPWD(self,p):
        self.PWD=p
        pass
    def setLevel(self,l):
        self.level=l
        pass

class CELL(object):
    def __init__(self,params):
        self.status=status_CELL["free"]
        self.type=[0,0]                     #dimensione, larghezza altezza
        self.addr=0
        self.CUDT_stored=""
        pass
    
    def newCell(self,l,h,a):
        self.status=status_CELL["free"]
        self.type=[l,h]
        self.addr=a
        self.CUDT_stored=""
        pass
    
    def setStatus(self,s):
        self.status=s
        pass
    def loadPiece(self,np):
        self.CUDT_stored=np
        self.status=status_CELL["busy"]
        pass
    def unloadPiece(self):
        self.CUDT_stored=""
        self.status=status_CELL["free"]
        pass

class WH(object): 	             #WHAREHOUSE
    def __init__(self,params):
        self.n_row=0
        self.n_col=0
        self.n_cell=0
        self.n_crane=0
        self.dip_crane=True
        self.in_pos=0
        self.out_pos=0
        pass
    
        
    