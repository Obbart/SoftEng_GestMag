'''
Created on 12 mar 2018

@author: Emanuele
'''
import time, json
from copy import deepcopy
from MODULES.GestMag_Threads import GestMag_Thread


class GestMag_Main(GestMag_Thread):
    
    def __init__(self, conf, mqttconf):
        super(GestMag_Main,self).__init__(conf, mqttconf)

        self.subList=[mqttconf['db2main'],
                      mqttconf['plc2main'],
                      mqttconf['cnc2main'],
                      mqttconf['gui2main']]
        
        self.matList=[]
        self.blkList=[]
        
    def on_dbMessage(self, client, userdata, msg):
        self.log.debug('received_from_DB: {}'.format(msg.payload))
        mesg=json.loads(msg.payload)
        if mesg['to'] == self.getName():
            if mesg['command'] == 'MATLIST':  #received when a new material is added to the db
                self.matList=deepcopy(mesg['materials'])    #contains a list of materials and properties
                mesg['from']=self.getName()
                mesg['to']='GestMag_GUI'
                self.publish(self.mqttConf['main2gui'], mesg) #forward the list to the gui to update the visualization
            elif mesg['command'] == 'BLKLIST':
                self.blkList=deepcopy(mesg['blocks'])
            pass
        pass
    
    def on_plcMessage(self, client, userdata, msg):
        pass
    
    def on_cncMessage(self, client, userdata, msg):
        pass
    
    def on_guiMessage(self, client, userdata, msg):
        self.log.debug('received_from_GUI: {}'.format(msg.payload))
        mesg=json.loads(msg.payload)
        if mesg['to'] == self.getName(): 
            # do something with the message
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
        time.sleep(self.mqttConf['pollPeriod'])
        #after starting the thread update information reading the db
        self.initialUpdate()
        
        while self.isRunning:
            time.sleep(self.mqttConf['pollPeriod'])
            pass
        
        self.kill()
        self.log.info("Thread STOPPED")
        return
    
    def initialUpdate(self):
        comlist=['UPDMAT','UPDBLK']
        for c in comlist:
            mesg={'from':self.getName(),
              'to':'GestMag_DB',
              'command':c}
            self.publish(self.mqttConf['main2db'], mesg)
            time.sleep(2)
        pass
    
    
    
    
    