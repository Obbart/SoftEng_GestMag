'''
Created on 12 mar 2018

@author: Emanuele

ogni richiesta riceve come parametro solo il materiale perche' 
l'intera ottimizzazione di allocazione viene effettuata in base solamente al tipo di materiale
vengono quindi considerati ti inferiore importanza gli altri parametri
'''

import copy
import json
import time
import uuid
import re

from PyQt5 import QtSql
import PyQt5

from MODULES.GestMag_Threads import GestMag_Thread


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
        self.log.info(re.sub(' +', ' ', q))
        query = QtSql.QSqlQuery(self.db)
        mesg={'from':self.getName(),
                  'to':'GestMag_GUI',
                  'command':'DBMSG'}
        if query.exec(q):
            return query
        else:
            t=query.lastError().text()
            mesg['msg']=t
            self.dbError(t)
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
            if   command=='ADDMAT':
                self.addMaterial(msg['prop'])
                self.updMaterials() #send a updated material list to main 
            elif command=='UPDMAT':
                self.updMaterials() #send a updated material list to main
            elif command=='GETMAT':
                matList=self.getMaterial(matID=msg['matID'], prop=msg['prop'])
                mesg={'from':self.getName(),
                      'to':'GestMag_MAIN',
                      'command': 'GETMAT_RESP',
                      'matlist': matList}
                self.publish(self.mqttConf['db2main'], mesg)
                pass
            elif command=='SETMAT':
                pass
            elif command=='DELMAT':
                self.delMaterial(msg['prop'])
                self.updMaterials()
                pass
            elif command=='ADDBLK':
                self.addBlock(msg['prop'])
                self.updBlocks() #send an updated block list to main
                pass
            elif command=='UPDBLK':
                self.updBlocks() #send an updated block list to main
            elif command=='GETBLK':
                blkList=self.getBlock(matID=msg['matID'])
                mesg={'from':self.getName(),
                      'to':'GestMag_MAIN',
                      'command': 'GETBLK_RESP',
                      'blklist': blkList}
                self.publish(self.mqttConf['db2main'], mesg)
                pass
            elif command=='SETBLK':
                pass
            elif command=='DELBLK':
                self.delBlock(msg['prop'])
                self.updBlocks()
                pass
            elif command=='ADDRCP':
                self.addRecipe(msg['prop'])
                self.updRecipes()
                pass
            elif command=='UPDRCP':
                self.updRecipes()
                pass
            elif command=='GETRCP':
                rcpList=self.getRecipe(matID=msg['matID'])
                mesg={'from':self.getName(),
                      'to':'GestMag_MAIN',
                      'command': 'GETRCP_RESP',
                      'rcplist': rcpList}
                self.publish(self.mqttConf['db2main'], mesg)
                pass
            elif command=='SETRCP':
                pass
            elif command=='DELRCP':
                self.delRecipe(msg['prop'])
                self.updRecipes()
                pass
            elif command=='ADDCELL':
                self.addCell(msg['prop'])
                self.updCells()
                pass
            elif command=='UPDCELL':
                self.updCells()
                pass
            elif command=='GETCELL':
                pass
            elif command=='SETCELL':
                self.setCell(msg['prop'])
                pass
            elif command=='ADDORD':
                self.addOrder(msg['prop'])
                self.updOrder()
                pass
            elif command=='UPDORD':
                self.updOrder()
                pass
            elif command=='GETORD':
                ordList=self.getOrd(ordID=msg['ordID'])
                mesg={'from':self.getName(),
                      'to':'GestMag_MAIN',
                      'command': 'GETORD_RESP',
                      'ordList': ordList}
                self.publish(self.mqttConf['db2main'], mesg)
                pass
                pass
            elif command=='SETORD':
                pass
            elif command=='DELORD':
                self.delOrder(msg['prop'])
                self.updOrder()
                pass
            else:
                self.log.error("Unrecognised Command, ignoring..")
                pass
        pass
    #################### MQTT_FUNC ########################
    
    ##### MATERIALS #####
    def addMaterial(self, matProp):
        q='INSERT INTO Materials (materialID, density, lift, color, restTime)\
            VALUES (\'{matID}\', \'{density}\', \'{lift}\', \'{color}\', \'{restTime}\')'
        q=q.format(**matProp)
        rc=self.dbQuery(q)
        self.log.debug(rc)
        return rc
    def updMaterials(self):
        matList=self.getMaterial()
        mesg={'from':self.getName(),
              'to':'GestMag_MAIN',
              'command': 'MATLIST',
              'materials': matList}
        self.publish(self.mqttConf['db2main'], mesg)
        pass
    def getMaterial(self, matID=None, prop=None): 
        #returns a property from a material id or a list of materials with all properties
        q="SELECT {pr} FROM Materials WHERE materialID LIKE '{id}'\
            ORDER BY MaterialID ASC"
        if prop is None:
            prop='*'
        if matID is None:
            matID='%'
        query=self.dbQuery(q.format(pr=prop,id=matID))
        if query is not False:
            return self.query2dict(query)
        else:
            return {}
        pass
    
    #TODO rifare la funzione!!!! 
    def setMaterial(self, matID=None, prop=None):
        pass
    def delMaterial(self, matID=None):
        q='DELETE FROM Materials \
            WHERE materialID = \'{matID}\' '
        q=q.format(**matID)
        self.dbQuery(q)
        pass
    
    ##### BLOCKS #####
    def addBlock(self,blkProp):
        q='INSERT INTO Blocks (blockID, materialID, blockProductionDate, blockWidth, blockHeight, blockDepth) \
            VALUES (\'{blockID}\', \'{matID}\', \'{date}\', \'{width}\', \'{height}\', \'{length}\')'
        q=q.format(**blkProp)
        self.dbQuery(q)
        pass
    def updBlocks(self):
        blkList=self.getBlock()
        mesg={'from':self.getName(),
              'to':'GestMag_MAIN',
              'command': 'BLKLIST',
              'blocks': blkList}
        self.publish(self.mqttConf['db2main'], mesg)
        pass
    def getBlock(self, matID=None):
        #returns a block or a list of blocks with all properties
        q="SELECT * FROM Blocks WHERE materialID LIKE '{id}'\
            ORDER BY materialID ASC"
        if matID is None:
            matID='%'
            pass
        query=self.dbQuery(q.format(id=matID))
        if query is not False:
            return self.query2dict(query)
        pass
    def setBlock(self, blockID, prop):
        pass
    def delBlock(self, blockID=None):
        q='DELETE FROM Blocks \
            WHERE blockID = \'{blockID}\' '
        q=q.format(**blockID)
        self.dbQuery(q)
        pass
    
    ##### RECIPES #####
    def addRecipe(self, rcpProp):
        q='INSERT INTO Recipes(recipeID, materialID, nVertCut, spVertCut, nOrCut, spOrCut, progSagom)\
            VALUES (\'{rcpID}\', \'{matID}\', \'{ncv}\', \'{scv}\',\'{nco}\', \'{sco}\',\'{prg}\')'
        q=q.format(**rcpProp)
        self.dbQuery(q)
        pass
    def updRecipes(self):
        rcpList=self.getRecipe()
        mesg={'from':self.getName(),
              'to':'GestMag_MAIN',
              'command': 'RCPLIST',
              'recipes': rcpList}
        self.publish(self.mqttConf['db2main'], mesg)
        pass
    def getRecipe(self, matID=None):
        q='SELECT * FROM Recipes WHERE materialID LIKE \'{id}\' '
        if matID is None:
            matID='%'
            pass
        query=self.dbQuery(q.format(id=matID))
        if query is not False:
            return self.query2dict(query)
        pass
    def setRecipe(self):
        pass
    def delRecipe(self,recID=None):
        q='DELETE FROM Recipes \
            WHERE recipeID = \'{recipeID}\' '
        q=q.format(**recID)
        self.dbQuery(q)
        pass
    
    ##### CELLS #####
    def addCell(self,cellProp):
        q='SELECT COUNT(cellID) FROM Cells'
        query=self.dbQuery(q)
        if query is not False:
            resp=self.query2dict(query) #check if dimensions are changed
            if resp[0]['COUNT(cellID)'] is not cellProp['x']*cellProp['y']:
                self.log.info('Recreating CELL Database')
                q='DELETE FROM Cells'
                query=self.dbQuery(q) #if are changed, delete all cells, for simplicity
                if query is not False:
                    for x in range(cellProp['x']): #recreate cells with new uuids
                        for y in range(cellProp['y']):
                            q='INSERT INTO Cells (cellID, cellX, cellY)\
                            VALUES (\'{cellID}\', \'{xx}\', \'{yy}\')'
                            q=q.format(cellID=uuid.uuid4().hex,xx=x,yy=y)
                            rc=self.dbQuery(q)
                            self.log.debug(rc.lastError().text())
                            pass
                        pass
                    pass
                pass
            pass
        pass
    def updCells(self):
        cellList=self.getCell()
        mesg={'from':self.getName(),
              'to':'GestMag_MAIN',
              'command': 'CELLLIST',
              'cells': cellList}
        self.publish(self.mqttConf['db2main'], mesg)
        pass
    def getCell(self):
        q="SELECT * FROM Cells\
            ORDER BY cellY,cellX ASC"
        query=self.dbQuery(q)
        if query is not False:
            return self.query2dict(query)
        pass
    def setCell(self,cellProp):
        q='UPDATE Cells \
            SET blockID={blockID}, cellStatus={cellStatus} \
            WHERE cellX={cellX} AND cellY={cellY}'
        q=q.format(**cellProp)
        self.dbQuery(q)
        pass
    def delCell(self):
        q='DELETE FROM Cells'
        self.dbQuery(q)
        pass
    
    ##### ORDERS #####
    def addOrder(self, ordProp):
        q='INSERT INTO Orders (orderID, customer, expDate, nPieces, recipeID)\
            VALUES (\'{orderID}\', \'{customer}\', \'{expDate}\', \'{nPieces}\',\'{recipeID}\')'
        q=q.format(**ordProp)
        self.dbQuery(q)
        pass
    def updOrder(self):
        ordList=self.getOrder()
        mesg={'from':self.getName(),
              'to':'GestMag_MAIN',
              'command': 'ORDLIST',
              'orders': ordList}
        self.publish(self.mqttConf['db2main'], mesg)
        pass
    def getOrder(self, ordID=None):
        q='SELECT * FROM Orders WHERE orderID LIKE \'{id}\''
        if ordID is None:
            ordID='%'
            pass
        query=self.dbQuery(q.format(id=ordID))
        if query is not False:
            return self.query2dict(query)
        pass
    def setOrder(self):
        pass
    def delOrder(self,ordID=None):
        q='DELETE FROM Orders \
            WHERE orderID LIKE \'{orderID}\' '
        q=q.format(**ordID)
        self.dbQuery(q)
        pass
    
    ##### MISCELLANEOUS #####
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
        