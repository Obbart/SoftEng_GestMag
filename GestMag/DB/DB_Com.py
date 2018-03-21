'''
Created on 12 mar 2018

@author: Emanuele
'''
import time
from MODULES.GestMag_Threads import GestMag_Thread

from PyQt5 import QtSql

class DB_Com(GestMag_Thread):

    def __init__(self,conf,mqttconf):
        super(DB_Com,self).__init__(conf,mqttconf)
        self.subList=[mqttconf['main2db']]
        
        self.db = QtSql.QSqlDatabase.addDatabase(conf['dbType'])
        self.db.setHostName(conf['hostname'])
        self.db.setUserName(conf['user'])
        self.db.setPassword(conf['password'])
        self.db.setDatabaseName(conf['database'])
        if conf['port']: 
            self.db.setPort(conf['port'])
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        pass

        
    #######################################################
    #################### MAIN_LOOP ########################
    #######################################################    
    def run(self):
        self.connectMqtt(self.subList) 
        self.client.message_callback_add(self.subList[0], self.on_mainMessage)
        if self.db.open() == True:
            pass
        else:
            self.log.error("Unable to connect to DB: {}".format(self.db.lastError().text()))
            self.isRunning = False
            return                    
        query = QtSql.QSqlQuery(self.db)
                  
        self.log.info("Thread STARTED")
        
        while self.isRunning:
            self.sendPoll()
            time.sleep(self.mqttConf["pollPeriod"])
            pass
        
        self.log.info("Thread STOPPED") 
        pass
        