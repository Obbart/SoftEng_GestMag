'''
Created on 12 mar 2018

@author: Emanuele
'''
from copy import deepcopy
import time, json

from MODULES.GestMag_Threads import GestMag_Thread
from CNC.CNC_Sim import status_CNC, type_CNC
from MODULES.Objects import MATERIAL, BLOCK, CELL, ORDER, RECIPE, WIP, status_CELL
from math import sqrt
import queue


class GestMag_Main(GestMag_Thread):
    
    def __init__(self, conf, mqttconf):
        super(GestMag_Main, self).__init__(conf, mqttconf)

        self.subList = [mqttconf['db2main'],
                      mqttconf['plc2main'],
                      mqttconf['cnc2main'],
                      mqttconf['gui2main']]
        
        # local copy of database to manage allocation of blocks in the storage
        self.matList = []
        self.blkList = []
        self.wipList = []
        self.cellList = []
        self.recipeList = []
        self.orderList = []
        
        # event queue to be processed on main loop in order to leave the callback function free for next events
        self.initCompleted = False
        self.eventQueue = queue.Queue()
        
        # load machine list from configuration file
        self.machineList = conf['cnc']['machines']
        
        # load buffer properties from configuration file
        self.bufferPos = (conf['plc']['buffer']['addr'], 0)
        self.bufferBlockID = ''
        # crane useful data
        self.cranePos = 0
        self.craneBlockID = ''
        
    def on_dbMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.getName():
            mesg['from'] = self.getName()
            if mesg['command'] == 'MATLIST':  # received when a new material is added to the db
                                                # contains a list of materials and properties
                self.matList = self.createInstance(deepcopy(mesg['materials']), MATERIAL)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)  # forward the list to the gui to update the visualization
                mesg['to'] = 'GestMag_PLC'
                self.publish(self.mqttConf['main2plc'], mesg)  # forward the material list to plc module for new block simulation
            elif mesg['command'] == 'BLKLIST':
                self.blkList = self.createInstance(deepcopy(mesg['blocks']), BLOCK)
                self.blkList = self.associateMaterial(self.blkList, self.matList)
                # gira il messaggio anche ai moduli:
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
                mesg['to'] = 'GestMag_CNC'
                self.publish(self.mqttConf['main2cnc'], mesg)
            elif mesg['command'] == 'WIPLIST':
                self.wipList = self.createInstance(deepcopy(mesg['wips']), WIP)
                self.wipList = self.associateMaterial(self.wipList, self.matList)
                #gira il messaggio anche ai moduli:
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
                mesg['to'] = 'GestMag_CNC'
                self.publish(self.mqttConf['main2cnc'], mesg)
            elif mesg['command'] == 'CELLLIST':
                self.cellList = self.createInstance(deepcopy(mesg['cells']), CELL)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'RCPLIST':
                self.recipeList = self.createInstance(deepcopy(mesg['recipes']), RECIPE)
                self.recipeList = self.associateMaterial(self.recipeList, self.matList)
                for s in self.recipeList:
                    s.setTimes()
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'ORDLIST':
                self.orderList = self.createInstance(deepcopy(mesg['orders']), ORDER)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            pass
        pass
    '''
    events from cnc, plc and some from gui require some time and logic to be completed so actions are put in a queue 
    that is red from main and necessary action are taken into the appropriate order
    '''
    
    def on_plcMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['command'] == 'ADDBLK': 
            self.eventQueue.put(mesg)  
            mesg['to'] = 'GestMag_DB'
            self.publish(self.mqttConf['main2db'], mesg)
            pass
        elif mesg['command'] in ['MOVE_WAIT', 'MOVE_OK']:
            self.eventQueue.put(mesg)
        pass
    
    def on_cncMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.getName():
            #mesg['to'] = 'GestMag_CNC'
            if mesg['command'] == 'ADDWIP':
                self.eventQueue.put(mesg)
            elif mesg['command'] == 'ADDBLK':
                self.eventQueue.put(mesg)
            elif mesg['command']=='GETCNC_RESP':
                self.machineList=deepcopy(mesg['machines'])
            pass
        pass
    
    def on_guiMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.getName(): 
            mesg['from'] = self.getName()
            # do something with the message
            if mesg['command'] == 'ADDCELL':
                mesg['to'] = 'GestMag_DB'
                mesg['prop'] = {'x':self.conf['mag']['x'],
                              'y':self.conf['mag']['y']}
                self.publish(self.mqttConf['main2db'], mesg)
                pass    
            elif mesg['command'] in ['ADDMAT', 'DELMAT']:
                mesg['to'] = 'GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
                pass
            elif mesg['command'] in ['ADDBLK', 'DELBLK']:
                mesg['to'] = 'GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
                self.eventQueue.put(mesg)
                pass
            elif mesg['command'] in ['ADDRCP', 'DELRCP']:
                mesg['to'] = 'GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
            elif mesg['command'] in ['ADDORD', 'DELORD']:
                mesg['to'] = 'GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
            else:
                pass
        elif mesg['to'] == 'GestMag_DB':  # publish the message directly to the destination
            self.publish(self.mqttConf['main2db'], mesg)
            pass
        elif mesg['to'] == 'GestMag_CNC':
            self.publish(self.mqttConf['main2cnc'], mesg)
            pass 
        elif mesg['to'] == 'GestMag_PLC':
            if mesg['command'] == 'MOVE':
                msg = {'form':self.getName(),
                     'to':'GestMag_DB',
                     'command':'EMPCELL',
                     'prop':{'cellX':mesg['prop']['source'][0],
                             'cellY':mesg['prop']['source'][1]}}
                self.publish(self.mqttConf['main2db'], msg)
                time.sleep(0.05)
                self.publish(self.mqttConf['main2plc'], mesg)
            pass 
        pass
    
    
    
    
    #######################################################
    #################### MAIN_LOOP ########################
    #######################################################    
    def run(self):
        self.connectMqtt(self.subList) 
        self.client.message_callback_add(self.subList[0], self.on_dbMessage) 
        self.client.message_callback_add(self.subList[1], self.on_plcMessage)
        self.client.message_callback_add(self.subList[2], self.on_cncMessage)
        self.client.message_callback_add(self.subList[3], self.on_guiMessage)
        
        self.log.info("Thread STARTED")
        # after starting the thread update information reading the db
        time.sleep(2)
        self.initCompleted = self.initialUpdate()
        time.sleep(2)
        
        plcBusy = False
        BUFFER_OUT=0
                
        while self.isRunning:
            if not self.eventQueue.empty() and self.initCompleted:
                lastEvent = self.eventQueue.get(block=False)
                self.log.info(lastEvent)
                if lastEvent['command'] == 'ADDBLK':  # new block from Buffer IN or CNC
                    if not plcBusy:
                        self.log.info('TRYING TO ALLOCATE NEW BLOCK')
                        v = 0
                        o = 0
                        s = 0
                        for r in [rr for rr in self.recipeList if rr.materialID == lastEvent['prop']['materialID'] ]:  # check which is the most common first step of recipes using the block's material
                            if r.seq[0] == 'V':
                                v += 1
                            elif r.seq[0] == 'O':
                                o += 1
                            elif r.seq[0] == 'S':
                                s += 1    
                                pass
                            pass
                        cncRequired = max(v, o, s)  # plurality voting
                        if cncRequired == v:
                            cncRequired = type_CNC['V']
                        elif cncRequired == o:
                            cncRequired = type_CNC['O']
                        elif cncRequired == s:
                            cncRequired = type_CNC['S']
                            pass
                        
                        cncDest = self.choseDestination(cncRequired)  # find the right destination
                        
                        mesg = {'from':self.getName(),  # creation of the message to send to the PLC
                                'to':'GestMag_PLC',
                                'command':'MOVE',
                                'prop':{'source':lastEvent['prop']['source'],
                                      'dest':(cncDest['xmin'], cncDest['ymin']),
                                      'blockID':lastEvent['prop']['blockID']}
                                }
                        
                        self.publish(self.mqttConf['main2plc'], mesg)
                        plcBusy = True
                        pass
                    else:
                        self.eventQueue.put(lastEvent)
                        pass
                elif  lastEvent['command'] == 'ADDWIP':
                    if plcBusy == False:
                        if self.getSeqLengthFromRecipe(lastEvent['prop']['recipeID'])==lastEvent['prop']['stepRecipe'] :
                            mesg = {'from':self.getName(),  # creation of the message to send to the PLC
                                        'to':'GestMag_PLC',
                                        'command':'MOVE',
                                        'prop':{'source':lastEvent['prop']['source'],
                                              'dest':(BUFFER_OUT, 0),
                                              'blockID':lastEvent['prop']['blockID']}
                                        }
                                
                            self.publish(self.mqttConf['main2plc'], mesg)
                            plcBusy = True
                        # trovare il cnc per il prox step 
                        cncReq = self.getTypeCNCFromRecipe(lastEvent['prop']['recipeID'], lastEvent['prop']['stepRecipe'])  # prima controllo se non ho CNC disponibili
                        for m in [mm for mm in self.machineList if mm.type == cncReq and mm.isReady()]:
                            if plcBusy == False:
                                mesg = {'from':self.getName(),  # creation of the message to send to the PLC
                                        'to':'GestMag_PLC',
                                        'command':'MOVE',
                                        'prop':{'source':lastEvent['prop']['source'],
                                              'dest':(m['addr'], 0),
                                              'blockID':lastEvent['prop']['blockID']}
                                        }
                                
                                self.publish(self.mqttConf['main2plc'], mesg)
                                plcBusy = True
                                pass
                            pass
                        if plcBusy == False: 
                            cncDest = self.choseDestination(cncReq)
                            mesg = {'from':self.getName(),  # creation of the message to send to the PLC
                                    'to':'GestMag_PLC',
                                    'command':'MOVE',
                                    'prop':{'source':lastEvent['prop']['source'],
                                          'dest':(cncDest['xmin'], cncDest['ymin']),
                                          'blockID':lastEvent['prop']['blockID']}
                                    }
                                
                            self.publish(self.mqttConf['main2plc'], mesg)
                            plcBusy = True
                            pass
                    else:
                        self.eventQueue.put(lastEvent)
                        pass
                elif lastEvent['command'] == 'MOVE_OK':
                    mesg = {'from':self.getName(),
                          'to':'GestMag_DB',
                          'command':'SETCELL',
                          'prop':{'blockID':lastEvent['prop']['blockID'],
                                  'cellStatus':status_CELL['busy'],
                                  'cellX':lastEvent['prop']['dest'][0],
                                  'cellY':lastEvent['prop']['dest'][1]}
                            }
                    
                    # aggiorna interfaccia
                    self.publish(self.mqttConf['main2db'], mesg)
                    mesg['command'] = 'UPDCELL'
                    self.publish(self.mqttConf['main2db'], mesg)
                    time.sleep(0.1)
                    mesg['command'] = 'UPDBLK'
                    self.publish(self.mqttConf['main2db'], mesg)
                    time.sleep(0.1)
                    mesg['to'] = 'GestMag_GUI'
                    mesg['command'] = 'UPDVIS'
                    self.publish(self.mqttConf['main2gui'], mesg)
                    plcBusy = False
                else:
                    pass
            time.sleep(0.5)
            pass
        
            for m in [mm for mm in self.machineList if mm['status']==status_CNC['free']]:  # cycle used to check if there is a free CNC 
                if plcBusy == False :
                    for w in self.wipList:  # check first if m is needed by any WIP
                        if m.type == self.getTypeCNCFromRecipe(w.recipeID, w.recipeStep):
                            mesg = {'from':self.getName(),  # creation of the message to send to the PLC
                                    'to':'GestMag_PLC',
                                    'command':'MOVE',               ##trovare un modo per dire a CNC che arriva un blocco o wip
                                    'prop':{'source':m,
                                          'dest':(m['addr'], 0),
                                          'blockID':'',
                                          'wipID':w.wipID}  # wipID different from blockID?
                                    }
   
                            self.publish(self.mqttConf['main2plc'], mesg)
                            plcBusy = True
                            pass
                        pass
                    
                    otrtc = []  # OrdersThatRequireThisCnc
                    Dmin = sqrt((self.conf['mag']['x'] + 10) ** 2 + (self.conf['mag']['y'] + 10) ** 2)
                    bestBlock = ''
                    
                    if plcBusy == False and len(self.orderList)>0:                                                      
                        for o in self.orderList:
                            if m['type'] == self.getTypeCNCFromRecipe(o.recipeID, 0):
                                for b in [bb for bb in self.blkList if bb.ready and bb.materialID == self.getMatIDFromRecipe(o.recipeID)]:
                                    if self.checkDimension(o.recipeID, b.blockID):
                                        Dist = self.distance((m.addr, 0), self.findPos(b.blockID))
                                        if Dist < Dmin :
                                            Dmin = Dist
                                            bestBlock = b.blockID
                                            pass
                                    # misurare la distanza da m e trovare il blocco pi� vicino, con le dimensioni giuste
                                    pass
                                orderData = {'order':o,
                                             'expDate': time.strptime(o.expDate,"%s"),
                                             'Block':bestBlock}
                                otrtc.append(orderData)
                                pass
                            pass
                        if len(otrtc) > 0: 
                            earliestOrder=min(otrtc,key=lambda f: f['expDate'])
                            mesg = {'from':self.getName(),  # creation of the message to send to the PLC
                                    'to':'GestMag_PLC',
                                    'command':'MOVE',
                                    'prop':{'source':self.findPos(earliestOrder['block']),
                                          'dest':(m['addr'], 0),
                                          'blockID':earliestOrder['block'],
                                          'wipID':''}                      
                                    }
                            self.publish(self.mqttConf['main2plc'], mesg)
                            plcBusy = True
                            pass
                        pass
                    
                    pass
                
                pass
            
            time.sleep(0.5)
            pass
        
        self.kill()
        self.log.info("Thread STOPPED")
        return
    
    #######################################################
    #################### MAIN_LOOP ########################
    #######################################################
    
    #######################################################
    #################### FUNCTIONS ########################
    #######################################################
    
    def initialUpdate(self):
        # list of commands to perfmorm initial memory update
        comlist = ['UPDCELL', 'UPDMAT', 'UPDBLK', 'UPDWIP', 'UPDRCP', 'UPDORD']
        for c in comlist:
            mesg = {'from':self.getName(),
              'to':'GestMag_DB',
              'command':c}
            self.publish(self.mqttConf['main2db'], mesg)
            self.log.info('Initial Update of: {}'.format(c))
            time.sleep(0.5)
            
        mesg['to']='GestMag_CNC'
        mesg['command']='GETCNC'
        self.publish(self.mqttConf['main2cnc'], mesg)
        
        mesg['to'] = 'GestMag_GUI'
        mesg['command'] = 'UPDMAC'
        mesg['machines'] = self.machineList
        self.publish(self.mqttConf['main2gui'], mesg)
        time.sleep(0.25)
        mesg['command'] = 'UPDVIS'
        self.publish(self.mqttConf['main2gui'], mesg)
        
        self.log.info('Initial Update of: Visualization')
        return True
    
    def getCell(self, x, y):    
        for c in self.cellList: 
            if c.addr[0] == x and c.addr[1] == y: 
                return c
    
    def choseDestination(self, cncReq):  # determination of the cell which the block will be sent to
        cncData = {'name':'', 'dist':0, 'xmin':0, 'ymin':0}      
        cncAvail = []
        for c in self.machineList:
            if c['type'] == cncReq :
                xmin = self.conf['mag']['x'] + 10
                ymin = self.conf['mag']['y'] + 10
                Dmin = sqrt(xmin ^ 2 + ymin ^ 2)
                Xc = c['addr']
                for x in range (0, self.conf['mag']['x']):
                    for y in range(0, self.conf['mag']['y']):
                        if self.getCell(x, y).isEmpty():  # #come ricavare se cell � libera o no
                            D = self.distance((Xc, 0), (x, y))
                            if D < Dmin :
                                xmin = x
                                ymin = y
                                Dmin = D
                                pass
                            pass
                    pass
                pass
                cncData = {'name':c['name'],
                         'dist':Dmin,
                         'xmin':xmin,
                         'ymin':ymin}
                cncAvail.append(cncData)
            pass
        cnc = min(cncAvail, key=lambda f: f['dist'])
        return cnc
  
    def getTypeCNCFromRecipe(self, r, step): 
        ''' r=recipeID  step=recipe step'''        
        for x in self.recipeList:
            if x.recipeID == r :
                if x.seq[step] == 'v':
                    return type_CNC["v"]
                elif x.seq[step] == 'o':
                    return type_CNC["o"]
                elif x.seq[step] == 's':
                    return type_CNC["s"]


    def getMatIDFromRecipe(self, r):
        '''r=recipeID'''
        for x in self.recipeList:
            if x.recipeID == r:
                return x.materialID
            pass
        pass
    def getSeqLengthFromRecipe(self,r):
        for x in self.recipeList:
            if x.recipeID == r:
                return len(x.seq)
            pass
        pass
      
    def distance(self, a, b):  # distance having x and y of two positions
        return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
    
    def findPos(self, b): 
        '''b=blockID'''  # find the position of block b, either if in cell or crane/buffer
        if self.bufferBlockID == b:
            return (self.bufferPos, 0)
        if self.craneBlockID == b:
            return self.cranePos
        for c in [cc for cc in self.cellList if not cc.isEmpty()]:
            if c.blockID == b:
                return c.addr
            pass
        pass
            
    def checkDimension (self, r, b):  # avendo ricetta e blocco controllo se blocco � abbastanza grande
        '''r=recipeID b=blockID'''
        for y in self.blkList:
            if y.blockID == b:
                block = y
                pass
            pass
        for x in self.recipeList:
            if x.recipeID == r:
                if x.seq[0] == 'v':
                    return block.length >= x.n_ve_cut * x.w_ve_cut
                elif x.seq[0] == 's':
                    return block.length >= x.lSag
                elif x.seq[0] == 'o':
                    return block.height >= x.n_or_cut * x.w_or_cut
                    pass
                pass
            pass
        pass
    #######################################################
    #################### FUNCTIONS ########################
    #######################  END  #########################
    