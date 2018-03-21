'''
Created on 15 mar 2018

@author: Emanuele
'''
import logging
import threading

from MODULES.MyLog import MyLogger
import paho.mqtt.client as mqtt

# global definition of debug level
deblevel=logging.ERROR

class GestMag_Thread(threading.Thread):
    '''
    superclass of every gestmag thread, sets up common features
    mqtt connection with timed poll send to sense thread alive
    logging features
    '''

    def __init__(self,conf,mqttconf):
        super(GestMag_Thread,self).__init__()
        self.isRunning=True
        self.pollAck=False
        
        self.mqttConf=mqttconf  #,connection and poll timer setup
        self.client=mqtt.Client(protocol=mqtt.MQTTv31)
        self.reconnectRetry=0
        
        self.log=MyLogger(conf['modName'],deblevel).logger()  #logger setup using thread name
        self.setName(conf['modName']) 
                
    def sendPoll(self): #automatic alive signal to init every x second
        self.pollAck=False
        rc=self.client.publish(self.mqttConf['all2ini'], str(self.getName()))
        if rc.is_published()==True or True:
            self.reconnectRetry=0   #sense if connected
        else:   #if not connected retry connection, if max retry kill thread
            if self.reconnectRetry <= self.mqttConf['reconRetry']:
                self.log.error("MQTT Connection Lost: {}".format(mqtt.error_string(rc.rc)))
                self.reconnectRetry+=1
                self.client.reconnect()
            else:
                self.kill()
        pass
    
    def on_broadcast(self, client, userdata, msg):
        msg=msg.payload
        if 'KILL' in msg:
            self.kill()
            pass
        pass

    def connectMqtt(self, subList):
        try:    #connect to mqtt server and subscribe to passed list and default broadcast from ini
            rc=self.client.connect(host=self.mqttConf['addr'],
                                   keepalive=self.mqttConf['keepalive'])
            self.client.subscribe(self.mqttConf['ini2all'])
            self.client.message_callback_add(self.mqttConf['ini2all'], self.on_broadcast)
            for i in subList:
                self.client.subscribe(i)
                self.log.debug("Subsribed to: {}".format(i))
            self.client.loop_start()
            return True
        except: #on error for first connection kill thread immediately
            self.log.error("Error Connecting to Mqtt, rc={0}... aborting".format(mqtt.connack_string(rc)))
            self.isRunning=False
            return False
            
    def kill(self):
        self.isRunning=False
        pass
        