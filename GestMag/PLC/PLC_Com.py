'''
Created on 12 mar 2018

@author: Emanuele
'''

import time
import queue
from MODULES.GestMag_Threads import GestMag_Thread
from MODULES.GestMag.MODULES.Classes_UML import PLC_Sim
from multiprocessing.queues import Queue

class PLC_Com(GestMag_Thread):

    def __init__(self,conf,mqttconf):
        super(PLC_Com,self).__init__(conf,mqttconf)
        self.subList=[mqttconf['main2plc']]
        self.simqueue=queue.Queue()
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        pass
    
    #######################################################
    #################### MAIN_LOOP ########################
    #######################################################
    def run(self):
        self.connectMqtt(self.subList)  
        self.client.message_callback_add(self.subList[0], self.on_mainMessage)
         
        self.log.info("Thread STARTED")
        
        while self.isRunning:
            time.sleep(self.mqttConf['pollPeriod'])
            pass
        
        self.log.info("Thread STOPPED") 
        
        pass
    
    