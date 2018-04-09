'''
Created on 12 mar 2018

@author: Emanuele
'''
import time
import copy
import json
from MODULES.GestMag_Threads import GestMag_Thread

from PyQt5 import QtSql
import PyQt5

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
        query = QtSql.QSqlQuery(self.db)
        if query.exec(q):
            return query
        else:
            t=query.lastError().text()
            self.dbError(t)
            mesg={'from':self.getName(),
                  'to':'GestMag_GUI',
                  'command':'DBMSG',
                  'msg':str(t)}
            self.publish(self.mqttConf['main2gui'], mesg)
            return False
        pass
        
    def dbError(self, txt):
        self.log.error("SQL DB Error: {}".format(txt))
        pass
    #################### DB_FUNC ######################
    
    #################### MQTT_FUNC ########################
    def on_mainMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        msg=json.loads(msg.payload)
        if msg['to'] == self.name:
            command=msg['command']
            if command=='ADDMAT':
                self.addMaterial(msg['prop'])
                self.updMaterials() #send a updated material list to main 
            elif command=='UPDMAT':
                self.updMaterials() #send a updated material list to main
            elif command=='DELMAT':
                pass
            elif command=='GETMAT':
                matList=self.getMaterial(matID=msg['matID'], prop=msg['prop'])
                mesg={'from':self.getName(),
                      'to':'GestMag_MAIN',
                      'command': 'GETMAT_RESP',
                      'matlist': matList}
                self.publish(self.mqttConf['db2main'], mesg)
                pass
            elif command=='ADDBLK':
                self.addBlock(msg['prop'])
                self.updBlocks() #send an updated block list to main
                pass
            elif command=='UPDBLK':
                self.updBlocks() #send an updated block list to main
            elif command=='GETBLK':
                blkList=self.getBlock(blockID=msg['blkID'])
                mesg={'from':self.getName(),
                      'to':'GestMag_MAIN',
                      'command': 'GETBLK_RESP',
                      'blklist': blkList}
                self.publish(self.mqttConf['db2main'], mesg)
                pass
            elif command=='DELBLK':
                pass
            else:
                self.log.error("Unrecognised Command, ignoring..")
                pass
        pass
    #################### MQTT_FUNC ########################
    
    def addMaterial(self, matProp):
        q='INSERT INTO Material (materialID, density, lift, color, restTime) VALUES (\'{matID}\', \'{density}\', \'{lift}\', \'{color}\', \'{restTime}\')'
        q=q.format(**matProp)
        rc=self.dbQuery(q)
        self.log.debug(rc)
        return rc
    
    def getMaterial(self, matID=None, prop=None): 
        #returns a property from a material id or a list of materials with all properties
        q="SELECT {pr} FROM Material WHERE MaterialID LIKE '{id}'"
        if prop is None:
            prop='*'
        if matID is None:
            matID='%'
        query=self.dbQuery(q.format(pr=prop,id=matID))
        return self.query2dict(query)
    
    def delMaterial(self, matID=None):
        query = QtSql.QSqlQuery()
        q="DELETE FROM Material WHERE MaterialID LIKE '{id}'"
        
        if matID is not None:
            q.format(id=matID)
            return query.exec(q)
        else:
            return False                    
        pass
    
    def addBlock(self,blkProp):
        q='INSERT INTO Blocks (blockID, blockMaterial, blockProductionDate, blockWidth, blockHeight, blockDepth) \
        VALUES (\'{blockID}\', \'{matID}\', \'{date}\', \'{width}\', \'{height}\', \'{length}\')'
        q=q.format(**blkProp)
        self.dbQuery(q)
        pass
    
    def getBlock(self, blockID=None):
        #returns a block or a list of blocks with all properties
        q="SELECT * FROM Blocks WHERE blockID LIKE '{id}'"
        if blockID is None:
            blockID='%'
            pass
        query=self.dbQuery(q.format(id=blockID))
        return self.query2dict(query)
        
        pass
    
    def delBlock(self):
        pass
    
    def addRecipe(self):
        pass
    
    def getRecipe(self):
        pass
    
    def delRecipe(self):
        pass
    
    def updMaterials(self):
        matList=self.getMaterial()
        mesg={'from':self.getName(),
              'to':'GestMag_MAIN',
              'command': 'MATLIST',
              'materials': matList}
        self.publish(self.mqttConf['db2main'], mesg)
        pass
    
    def updBlocks(self):
        blkList=self.getBlock()
        mesg={'from':self.getName(),
              'to':'GestMag_MAIN',
              'command': 'BLKLIST',
              'blocks': blkList}
        self.publish(self.mqttConf['db2main'], mesg)
        pass
    
    def query2dict(self, query): # converts the results of a query into a list of key value dictionary
        record=query.record()
        resp=[]
        m={}
        while query.next():
            for k in range(record.count()):
                if isinstance(query.value(k), PyQt5.QtCore.QTime):
                    m[record.fieldName(k)]=query.value(k).toPyTime()
                else:
                    m[record.fieldName(k)]=query.value(k)
            resp.append(copy.deepcopy(m))
            m.clear()
        self.log.info(str(resp))
        return resp
    

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
            pass
        
        self.db.close()
        self.log.info("Thread STOPPED") 
        pass
        