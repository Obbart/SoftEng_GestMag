'''
Created on 15 mar 2018

@author: Emanuele
'''
import logging
import threading
import time
import json

from MODULES.MyLog import MyLogger
import paho.mqtt.client as mqtt

# global definition of debug level
deblevel = logging.INFO

class GestMag_Thread(threading.Thread):
    '''
    superclass of every gestmag thread, sets up common features
    mqtt connection with timed poll send to sense thread alive
    logging features
    '''

    def __init__(self, conf, mqttconf):
        super(GestMag_Thread, self).__init__()
        self.daemon = True
        self.isRunning = True
        self.conf = conf
        
        self.mqttConf = mqttconf  # ,connection and poll timer setup
        self.client = mqtt.Client(protocol=mqtt.MQTTv31)
        self.reconnectRetry = 0
        
        self.log = MyLogger(conf['modName'], deblevel).logger()  # logger setup using thread name
        self.setName(self.conf['modName']) 

    
    def on_broadcast(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        msg = json.loads(msg.payload)
        if msg['to'] in 'ALL':
            if msg['command'] in 'POLL':
                self.sendPollResponse()
        pass
    
    def sendPollResponse(self):
        mesg = {'to':'init',
              'from':self.getName(),
              'command':'POLL_RESP',
              'ts':int(time.time())}
        self.publish(self.mqttConf['all2ini'], mesg)
    
    def publish(self, topic, msg):  # kinda overrides publish method to accept dictionaries as input
        self.log.debug('sent: {}'.format(json.dumps(msg)))
        rc = self.client.publish(topic, json.dumps(msg))
        self.client.loop()
        return rc

    def connectMqtt(self, subList):
        try:  # connect to mqtt server and subscribe to passed list and default broadcast from ini
            rc = self.client.connect(host=self.mqttConf['addr'],
                                   keepalive=self.mqttConf['keepalive'])
            self.client.subscribe(self.mqttConf['ini2all'])
            self.client.message_callback_add(self.mqttConf['ini2all'], self.on_broadcast)
            for i in subList:
                self.client.subscribe(i)
                self.log.debug("Subsribed to: {}".format(i))
            self.client.loop_start()
            return True
        except:  # on error for first connection kill thread immediately
            self.log.error("Error Connecting to Mqtt, rc={0}... aborting".format(mqtt.connack_string(rc)))
            self.isRunning = False
            return False
            
    def createInstance(self, l, c):
        # instantiate c using properties from list of dictionaries l
        tmp = []
        for i in l:
            tmp.append(c(prop=i))
        return tmp
    
    def associateMaterial(self, o, m):
        o = list(o)
        m = list(m)
        for oo in o:
            for mm in m:
                if oo.materialID == mm.materialID:
                    oo.material = mm
        return o
              
    def getKey(self, mydict, val):
        return list(mydict.keys())[list(mydict.values()).index(val)]
      
    def kill(self):
        self.isRunning = False
        self.client.disconnect()
        self.client.loop_stop(force=True)
        time.sleep(0.1)
        pass
        
