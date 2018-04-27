'''
Created on 12 mar 2018

@author: Emanuele
'''
from copy import deepcopy
import time, json

from MODULES.GestMag_Threads import GestMag_Thread
from MODULES.Objects import MATERIAL, BLOCK, CELL, ORDER, RECIPE


class GestMag_Main(GestMag_Thread):
    
    def __init__(self, conf, mqttconf):
        super(GestMag_Main,self).__init__(conf, mqttconf)

        self.subList=[mqttconf['db2main'],
                      mqttconf['plc2main'],
                      mqttconf['cnc2main'],
                      mqttconf['gui2main']]
        
        self.matList=[]
        self.blkList=[]
        self.cellList=[]
        self.recipeList=[]
        self.orderList=[]
        
    def on_dbMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg=json.loads(msg.payload)
        if mesg['to'] == self.getName():
            mesg['from']=self.getName()
            if mesg['command'] == 'MATLIST':  #received when a new material is added to the db
                self.matList=deepcopy(mesg['materials'])    #contains a list of materials and properties
                self.matList=self.createInstance(deepcopy(mesg['materials']), MATERIAL)
                mesg['to']='GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg) #forward the list to the gui to update the visualization
            elif mesg['command'] == 'BLKLIST':
                self.blkList=deepcopy(mesg['blocks'])
                mesg['to']='GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'CELLLIST':
                self.cellList=deepcopy(mesg['cells'])
                mesg['to']='GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'RCPLIST':
                self.recipeList=deepcopy(mesg['recipes'])
                mesg['to']='GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            elif mesg['command'] == 'ORDLIST':
                self.orderListList=deepcopy(mesg['orders'])
                mesg['to']='GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg)
            pass
        pass
    
    def on_plcMessage(self, client, userdata, msg):
        pass
    
    def on_cncMessage(self, client, userdata, msg):
        pass
    
    def on_guiMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg=json.loads(msg.payload)
        if mesg['to'] == self.getName(): 
            mesg['from']=self.getName()
            # do something with the message
            if mesg['command'] == 'ADDCELL':
                mesg['to']='GestMag_DB'
                mesg['prop']={'x':self.conf['mag']['x'],
                              'y':self.conf['mag']['y']}
                self.publish(self.mqttConf['main2db'], mesg)
                pass    
            elif mesg['command'] in ['ADDMAT','DELMAT']:
                mesg['to']='GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
                pass
            elif mesg['command'] in ['ADDBLK','DELBLK']:
                mesg['to']='GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
                pass
            elif mesg['command'] in ['ADDRCP','DELRCP']:
                mesg['to']='GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
            elif mesg['command'] in ['ADDORD','DELORD']:
                mesg['to']='GestMag_DB'
                self.publish(self.mqttConf['main2db'], mesg)
            else:
                pass
        elif mesg['to'] == 'GestMag_DB': #publish the message directly to the destination
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
        #after starting the thread update information reading the db
        time.sleep(2)
        self.initialUpdate()
        
        while self.isRunning:
            time.sleep(self.mqttConf['pollPeriod'])
            pass
        
        self.kill()
        self.log.info("Thread STOPPED")
        return
    
    def initialUpdate(self):
        comlist=['UPDCELL','UPDMAT','UPDBLK','UPDRCP','UPDORD']
        for c in comlist:
            mesg={'from':self.getName(),
              'to':'GestMag_DB',
              'command':c}
            self.publish(self.mqttConf['main2db'], mesg)
            self.log.info('Initial Update of: {}'.format(c))
            time.sleep(0.5)
        pass
    
    def createInstance(self, l, c):
        tmp=[]
        for i in l:
            tmp.append(c(prop=i))
        return tmp
    
    
    
    
    