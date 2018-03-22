'''
Created on 12 mar 2018

@author: Emanuele
'''
import time
from MODULES.GestMag_Threads import GestMag_Thread


class GestMag_Main(GestMag_Thread):
    
    def __init__(self, conf, mqttconf):
        super(GestMag_Main,self).__init__(conf, mqttconf)

        self.subList=[mqttconf['db2main'],
                      mqttconf['plc2main'],
                      mqttconf['cnc2main'],
                      mqttconf['gui2main']]
        
    def on_dbMessage(self, client, userdata, msg):
        pass
    
    def on_plcMessage(self, client, userdata, msg):
        pass
    
    def on_cncMessage(self, client, userdata, msg):
        pass
    
    def on_guiMessage(self, client, userdata, msg):
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
        i=0
        
        while self.isRunning and i < 3:
            time.sleep(self.mqttConf['pollPeriod'])
            i+=1
            pass
        
        self.kill()
        self.log.info("Thread STOPPED")
        return
    
    
    
    
    