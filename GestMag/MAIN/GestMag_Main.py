'''
Created on 12 mar 2018

@author: Emanuele
'''
from copy import deepcopy
import time, json, math

from MODULES.GestMag_Threads import GestMag_Thread
from MODULES.Objects import MATERIAL, BLOCK, CELL, ORDER, RECIPE, WIP, status_CELL, type_CNC
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
        
    def on_dbMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.getName():
            mesg['from'] = self.getName()
            if mesg['command'] == 'MATLIST':  # received when a new material is added to the db
                                                #contains a list of materials and properties
                self.matList = self.createInstance(deepcopy(mesg['materials']), MATERIAL)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)  # forward the list to the gui to update the visualization
                mesg['to'] = 'GestMag_PLC'
                self.publish(self.mqttConf['main2plc'], mesg)  # forward the material list to plc module for new block simulation
            elif mesg['command'] == 'BLKLIST':
                self.blkList = self.createInstance(deepcopy(mesg['blocks']), BLOCK)
                self.blkList = self.associateMaterial(self.blkList, self.matList)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'WIPLIST':
                self.wipList = self.createInstance(deepcopy(mesg['wips']), WIP)
                self.wipList = self.associateMaterial(self.wipList, self.matList)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
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
            mesg['to'] = 'GestMag_CNC'
            if mesg['command'] == 'MACHINEREADY':
                self.eventQueue.put(mesg)
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
        elif mesg['to'] == 'GestMaa_CNC':
            self.publish(self.mqttConf['main2cnc'], mesg)
            pass 
        elif mesg['to'] == 'GestMaa_PLC':
            self.publish(self.mqttConf['main2cnc'], mesg)
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
                
        while self.isRunning:
            if not self.eventQueue.empty() and self.initCompleted:
                lastEvent = self.eventQueue.get(block=False)
                self.log.info(lastEvent)
                if lastEvent['command'] == 'ADDBLK':                    #new block from Buffer IN
                    if lastEvent['prop']['materialID'] in [rm.materialID for rm in self.recipeList]:
                        self.log.info('TRYING TO ALLOCATE NEW BLOCK')
                        v=0
                        o=0
                        s=0
                        for r in self.recipeList:                       #check which is the most common first step of recipes using the block's material
                            if r.materialID==lastEvent['prop']['materialID'] :
                                if r.seq[0]=='V':
                                    v+=1
                                elif r.seq[0]=='O':
                                    o+=1
                                elif r.seq[0]=='P':
                                    s+=1    
                                pass
                            
                            pass
                        cncRequired=max(v,o,s)                                      #plurality voting
                        self.log.info('cncRequired: {}'.format(self.getKey(type_CNC,cncRequired)))
                        if cncRequired==v:
                            cncRequired=type_CNC["ver_cut"]
                        elif cncRequired==o:
                            cncRequired=type_CNC["ori_cut"]
                        elif cncRequired==s:
                            cncRequired=type_CNC["sagomatore"]
                            pass
                        
                        cncDest=self.choseDestination(cncRequired)                  #find the right destination
                        
                        mesg = {'from':self.getName(),                              #creation of the message to send to the PLC
                                'to':'GestMag_PLC',
                                'command':'MOVE',
                                'prop':{'source':self.bufferPos,
                                      'dest':(cncDest['xmin'], cncDest['ymin']),
                                      'blockID':lastEvent['prop']['blockID']}
                                }
                        
                        self.publish(self.mqttConf['main2plc'], mesg)
                        pass
                    else:
                        #self.eventQueue.put(lastEvent)
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
                    self.publish(self.mqttConf['main2db'], mesg)
                    mesg['command']='UPDCELL'
                    self.publish(self.mqttConf['main2db'], mesg)
                    time.sleep(0.1)
                    mesg['command']='UPDBLK'
                    self.publish(self.mqttConf['main2db'], mesg)
                    time.sleep(0.1)
                    mesg['to']='GestMag_GUI'
                    mesg['command']='UPDVIS'
                    self.publish(self.mqttConf['main2gui'], mesg)
                else:
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
            
        mesg['to']='GestMag_GUI'
        mesg['command']='UPDVIS'
        self.publish(self.mqttConf['main2gui'], mesg)
        mesg['command']='UPDMAC'
        mesg['machines']=self.machineList
        self.publish(self.mqttConf['main2gui'], mesg)
        
        self.log.info('Initial Update of: Visualization')
        return True
    
    def getCell(self, x,y):    
        for c in self.cellList: 
            if c.addr[0]==x and c.addr[1]==y: 
                return c
    
    def choseDestination(self,cncReq):                      #determination of the cell which the block will be sent to
        cncData={'name':'','dist':0,'xmin':0,'ymin':0}      
        cncAvail=[]
        for c in self.machineList:
            xmin=self.conf['mag']['x']+10
            ymin=self.conf['mag']['y']+10
            Dmin=math.sqrt(xmin**2+ymin**2)
            self.log.debug('Initial Dmin:{}'.format(Dmin))
            if c['type']==cncReq :
                self.log.info('Analysing cnc: {} - addr:{}'.format(c['name'],c['addr']))
                Xc=c['addr']
                for x in range (self.conf['mag']['x']):
                    for y in range(1,self.conf['mag']['y']):
                        D=math.sqrt((Xc-x)**2+y**2)
                        self.log.debug('Cell: {},{} - Empty: {} - Dist: {}'.format(x,y,self.getCell(x,y).isEmpty(),D))
                        if self.getCell(x,y).isEmpty():                                 ##come ricavare se cell Ë libera o no
                            if D<Dmin :
                                self.log.debug('Found Dmin={} for cnc: {}'.format(Dmin,c['name']))
                                xmin=x
                                ymin=y
                                Dmin=D
                                pass
                            pass
                    pass
                pass
                cncData={'name':c['name'],
                         'dist':Dmin,
                         'xmin':xmin,
                         'ymin':ymin}
                self.log.info('Data for cnc: {}'.format(cncData))
                cncAvail.append(deepcopy(cncData))
            pass
        self.log.info('Available cnc: {} _ dist:{}'.format([c['name'] for c in cncAvail], [c['dist'] for c in cncAvail ]))
        cnc=min(cncAvail,key=lambda f: f['dist'])
        return cnc
    
    
    #######################################################
    #################### FUNCTIONS ########################
    #######################  END  #########################
    
    
    
    
    
    
