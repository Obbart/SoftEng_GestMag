'''
Created on 12 mar 2018

@author: Emanuele
'''
from copy import deepcopy
import time, json

from MODULES.GestMag_Threads import GestMag_Thread
from MODULES.Objects import MATERIAL, BLOCK, CELL, ORDER, RECIPE, status_CELL
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
                # self.matList=deepcopy(mesg['materials'])    #contains a list of materials and properties
                self.matList = self.createInstance(deepcopy(mesg['materials']), MATERIAL)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)  # forward the list to the gui to update the visualization
                mesg['to'] = 'GestMag_PLC'
                self.publish(self.mqttConf['main2plc'], mesg)  # forward the material list to plc module for new block simulation
            elif mesg['command'] == 'BLKLIST':
                # self.blkList=deepcopy(mesg['blocks'])
                self.blkList = self.createInstance(deepcopy(mesg['blocks']), BLOCK)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'CELLLIST':
                # self.cellList=deepcopy(mesg['cells'])
                self.cellList = self.createInstance(deepcopy(mesg['cells']), CELL)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'RCPLIST':
                # self.recipeList=deepcopy(mesg['recipes'])
                self.recipeList = self.createInstance(deepcopy(mesg['recipes']), RECIPE)
                mesg['to'] = 'GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'ORDLIST':
                # self.orderListList=deepcopy(mesg['orders'])
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
        plcBusy = False
        x = 1
        y = 1
        
        while self.isRunning:
            if not self.eventQueue.empty() and self.initCompleted:
                lastEvent = self.eventQueue.get(block=False)
                self.log.info(lastEvent)
                if lastEvent['command'] == 'ADDBLK':
                    if not plcBusy:
                        self.log.info('TRYING TO ALLOCATE NEW BLOCK')
                        mesg = {'from':self.getName(),
                                'to':'GestMag_PLC',
                                'command':'MOVE',
                                'prop':{'source':self.bufferPos,
                                      'dest':(x, y),
                                      'blockID':lastEvent['prop']['blockID']}
                                }
                        self.publish(self.mqttConf['main2plc'], mesg)
                        plcBusy = True
                        y += 1
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
                    self.publish(self.mqttConf['main2db'], mesg)
                    mesg['command']='UPDCELL'
                    self.publish(self.mqttConf['main2db'], mesg)
                    time.sleep(0.1)
                    mesg['command']='UPDBLK'
                    self.publish(self.mqttConf['main2db'], mesg)
                    time.sleep(0.1)
                    mesg['command']='UPDATE'
                    self.publish(self.mqttConf['main2gui'], mesg)
                    plcBusy = False
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
    
    def initialUpdate(self):
        # list of commands to perfmorm initial memory update
        comlist = ['UPDCELL', 'UPDMAT', 'UPDBLK', 'UPDRCP', 'UPDORD']
        for c in comlist:
            mesg = {'from':self.getName(),
              'to':'GestMag_DB',
              'command':c}
            self.publish(self.mqttConf['main2db'], mesg)
            self.log.info('Initial Update of: {}'.format(c))
            time.sleep(0.5)
        return True
    
    def createInstance(self, l, c):
        # instantiate c using properties from list of dictionaries l
        tmp = []
        for i in l:
            tmp.append(c(prop=i))
        return tmp
    
    
    
    
    
