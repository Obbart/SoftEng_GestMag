'''
Created on 12 mar 2018

@author: Emanuele
'''
import time, json, queue
from MODULES.GestMag_Threads import GestMag_Thread
from CNC.CNC_Sim import CNC_Sim, status_CNC
from MODULES.Objects import BLOCK,WIP

from threading import Timer

class CNC_Com(GestMag_Thread):

    def __init__(self, conf, mqttconf):
        super(CNC_Com, self).__init__(conf, mqttconf)
        self.subList = [mqttconf['main2cnc']]
        self.conf=conf
        self.blockList=[] ##da implementare!
        self.wipList=[]
        
        #internal management of the events
        self.eventQueue = queue.Queue()
        
        # load machine list from configuration file
        self.machineList = []
        for m in conf['machines']:
            self.machineList.append(CNC_Sim(m))
            pass
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.getName():
            if mesg['command'] == 'LOADCNC':
                prop=mesg['prop']
                for m in self.machineList:
                    if m.getName() == prop['name']:  # search the correct machine in the list and load programs
                        m.setRecipe(prop['recipe'],prop['step'])
                        m.loadPiece(prop['blockID'])
                        break
                    pass
                pass
            elif mesg['command'] == 'UNLOADCNC':
                for m in self.machineList:
                    if m.getName() == mesg['name']:
                        m.unloadPiece()
                        break
                pass
            elif mesg['command'] == 'GETCNC':
                for m in self.machineList:
                    if m.getName() == mesg['name']:
                        data=m.getData()
                        self.publish(self.mqttconf['cnc2main'], data)
                pass
            else:
                pass
        pass
    
    #######################################################
    #################### FUNCTIONS ########################
    ####################################################### 
    
    def newWIP (self, b,cnc,ss):           #b=blockID now loaded in the CNC    cnc=in which cnc         
        wipp={
            "materialID":b.material,
            "recipeID":cnc.recipe_lavorato.recipeID,
            "recipeStep":ss+1 }
        wip=WIP(prop=wipp,new=True)
        mesg = {'from':self.getName(),
               'to':'GestMag_MAIN',
               'command':'ADDWIP',
               'prop':wip.getData()
               }
        mesg['prop']['source']=cnc.addr
        self.eventQueue.put(mesg)
        '''cnc.setStatus(status_CNC['waiting_unloading_WIP'])
        self.log.info(mesg)
        self.publish(self.mqttConf['cnc2main'], mesg)'''
        pass
    
    def workCycle(self,m,ss):       #m=cnc that is working   ss=recipe step
        for b in self.blockList:
            if b.blockID==m.blockID_lavorato :
                if m.recipe_lavorato.seq[ss]=='o':          #Modification of the dimensions of the block in input, due to the machining
                    b.height=b.height-(m.nCuts*m.wCut)
                elif m.recipe_lavorato.seq[ss]==('v' or 's'):
                    b.length=b.length-(m.nCuts*m.wCut+m.lSag)
                pass
                if b.height>self.conf['cnc']['minLenght'] and b.length>self.conf['cnc']['minLenght'] :      #check if there is a useful piece of material
                    blkp= {
                                "materialID": b.materialID,
                                "blockWidth": b.width,
                                "blockHeight": b.height,
                                "blockLenght": b.length
                                }
                    blk=BLOCK(prop=blkp,new=True)
                    blk.date=b.date
                    mesg = {'from':self.getName(),
                            'to':'GestMag_MAIN',
                            'command':'ADDBLK',
                            'prop':blk.getData()
                            }
                    mesg['prop']['source']=m.addr
                    self.eventQueue.put(mesg)
                pass
                self.newWIP(b,m,ss)
            pass
        pass
    
    #######################################################
    #################### FUNCTIONS ########################
    ########################END############################ 
    
    #######################################################
    #################### MAIN_LOOP ########################
    #######################################################    
    def run(self):
        self.connectMqtt(self.subList)
        self.client.message_callback_add(self.subList[0], self.on_mainMessage)
        
        self.log.info("Thread STARTED")
        cncBusy=False
        while self.isRunning:
            time.sleep(self.mqttConf["pollPeriod"])
            mesg={'from': self.getName(),
                  'to':'GestMag_MAIN',
                  'command':'',
                  'prop':''}

            for m in self.machineList:      #periodically check if there is machine waiting to be unloaded
                
                if m.getStatus()== status_CNC['busy']:
                    data=m.getData()
                    if data['blockID']==None :
                        for w in wipList:
                            if w.wipID==data['wipID']:
                                ss=w.recipeStep
                                pass
                            pass
                    else:
                        ss=0
                        pass
                    t=Timer(m.lavTimer,self.workCycle(m,ss))
                    t.start()
                    pass
                if m.getStatus() == status_CNC['waiting_unloading_WIP']:  ##not so useful
                    mesg['command']='MACHINEREADY'
                    mesg['prop']='WIP'
                    mesg['name']=m.getName()
                    self.publish(self.mqttConf['cnc2main'], mesg)
                elif m.getStatus() == status_CNC['waiting_unloading_MP']:  ##not so useful
                    mesg['command']='MACHINEREADY'
                    mesg['prop']='MP'
                    mesg['name']=m.getName()
                    self.publish(self.mqttConf['cnc2main'], mesg)
                pass
            
            if not self.eventQueue.empty() and not cncBusy:
                    msg=self.eventQueue.get()
                    if msg['command']=='ADDBLK':
                        for m in self.machineList :
                            if msg['from']==m.getName() and not cncBusy:
                                m.setStatus(status_CNC['waiting_unloading_MP'])
                                self.log.info(msg)
                                self.publish(self.mqttConf['cnc2main'], msg)
                                cncBusy=True
                                pass
                            pass
                    elif msg['command']== 'ADDWIP':
                        for m in self.machineList :
                            if msg['from']==m.getName() and not cncBusy:
                                m.setStatus(status_CNC['waiting_unloading_WIP'])
                                self.log.info(msg)
                                self.publish(self.mqttConf['cnc2main'], msg)
                                cncBusy=True
                                pass
                            pass
                    else:
                        self.eventQueue.put(msg)
                        pass
                    pass
                
                
                
            
                
                    
                    
                            
                            
                        
        self.log.info("Thread STOPPED")
        return
    
    
    
    
    
