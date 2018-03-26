'''
Created on 12 mar 2018

@author: Emanuele
'''
import time
from MODULES.GestMag_Threads import GestMag_Thread

from PyQt5 import QtSql
from PyQt5.Qt import QSql

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
    
    #################### DB_FUNC ########################
    def dbQuery(self, q):
        try:
            q.exec()
            return q.record()
        except:
            self.dbError(q.lastError().text())
            return False
            pass
        
    def dbError(self, txt):
        self.log.error("SQL DB Error:\n{}".format(txt))
        pass
    #################### DB_FUNC ######################
    
    #################### MQTT_FUNC ########################
    def on_mainMessage(self, client, userdata, msg):
        pass
    #################### MQTT_FUNC ########################
    
    def addMaterial(self, matProp):
        query = QtSql.QSqlQuery()
        query.prepare('INSERT INTO Material (MaterialID, density, lift, color, restTime) \
                        VALUES (:matid, :dens, :lift, :col, :rst)')
        for prop in matProp.keys():
            query.bindValue(prop, matProp[prop])
        return self.dbQuery(query)
    
    def getMaterial(self, matID=None, prop=None): #returns a property from a material id or a list of materials with all properties
        query = QtSql.QSqlQuery()
        query.prepare('SELECT :prop FROM Material \
                        WHERE MaterialID == :id')
        if prop is not None:
            query.bindValue('prop', prop)
        else:
            query.bindValue('prop', '*')
        
        if matID is not None:
            query.bindValue('id', matID)
        else:
            query.bindValue('id', '*')
            
        record=self.dbQuery(query)
        resp=[]
        m={}
        while query.next():
            for k in range(record.count()):
                m[record.fieldName(k)]=query.value(k)
            resp.append(m)
            m.clear()
        return resp
    
    def delMaterial(self):
        pass
    
    def addBlock(self):
        pass
    
    def getBlock(self):
        pass
    
    def delBlock(self):
        pass
    
    def addRecipe(self):
        pass
    
    def getRecipe(self):
        pass
    
    def delRecipe(self):
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
                  
        self.log.info("Thread STARTED")
        
        while self.isRunning:
            time.sleep(self.mqttConf["pollPeriod"])
            self.getMaterial()
            print(self.getMaterial())
            pass
        
        self.db.close()
        self.log.info("Thread STOPPED") 
        pass
        