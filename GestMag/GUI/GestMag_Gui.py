'''
Created on 12 mar 2018

@author: Emanuele
'''
import time, json, uuid
from copy import deepcopy
from GUI.GestMagUI import Ui_GestMag_WINDOW
from MODULES.GestMag_Threads import GestMag_Thread
from PyQt5.QtWidgets import *
import PyQt5.QtWidgets
from PyQt5.QtCore import Qt,pyqtSignal,QDate


class GestMag_GuInterface(QMainWindow):
    signal=pyqtSignal()
    
    def __init__(self, conf, mqttconf):
        # setup user interface
        QMainWindow.__init__(self)
        self.ui=Ui_GestMag_WINDOW()
        self.ui.setupUi(self)
        self.setWindowTitle('GestMag User Interface')
        self.ui.dat_deliveryDate.setDate(QDate.currentDate())
        
        #instantiate common functions
        self.common=GestMag_Thread(conf, mqttconf)
        self.common.connectMqtt([mqttconf['main2gui']])
        self.common.client.message_callback_add(mqttconf['main2gui'], self.on_mainMessage)
        
        # connect button and actions
        self.ui.btn_genID.clicked.connect(lambda: self.on_genID(self.ui.txt_blockID))
        self.ui.btn_genID2.clicked.connect(lambda: self.on_genID(self.ui.txt_orderID))
        self.ui.btn_addBlock.clicked.connect(self.on_addBlock)
        self.ui.btn_delBlock.clicked.connect(self.on_delBlock)
        self.ui.btn_addMaterial.clicked.connect(self.on_addMaterial)
        self.ui.btn_delMaterial.clicked.connect(self.on_delMaterial)
        self.ui.btn_addRecipe.clicked.connect(self.on_addRecipe)
        self.ui.btn_delRecipe.clicked.connect(self.on_delRecipe)
        self.ui.btn_addOrder.clicked.connect(self.on_addOrder)
        self.ui.btn_delOrder.clicked.connect(self.on_delOrder)
        self.ui.btn_createStorage.clicked.connect(self.on_createStorage)
        
        #interface update parameters and functions
        self.blkList=[]
        self.cellList=[]
        self.rcpList=[]
        self.xmax=0
        self.ymax=0
        self.last=''
        self.signal.connect(self.upd)
        
        # load defaults dictionaries
        try:
            fp=open('../INIT/conf/defaults.json','r')
            self.d=json.load(fp)
            fp.close()
        except Exception: 
            self.log.error("unable to open defaults file: {}, aborting")
            exit()
        
        self.mesg=deepcopy(self.d['msg'])
        self.mesg['from']=self.common.getName()
        self.mesg['to']='GestMag_MAIN'
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        self.common.log.debug('received: {}'.format(msg.payload))
        mesg=json.loads(msg.payload)
        if mesg['to'] == self.common.getName():
            if mesg['command'] == 'MATLIST': #after adding a material update combo box with list of all materials
                matList=mesg['materials']
                self.ui.cmb_matID.clear()   #update the whole combo clearing previous content
                self.ui.cmb_matID2.clear()
                self.ui.cmb_matID3.clear()
                matNames=self.dict2list(matList, 'materialID')
                self.ui.cmb_matID.addItems(matNames)
                self.ui.cmb_matID2.addItems(matNames)
                self.ui.cmb_matID3.addItems(matNames)
                pass
            elif mesg['command'] == 'BLKLIST':
                self.blkList=deepcopy(mesg['blocks'])
                self.ui.cmb_blockID.clear()
                blkNames=self.dict2list(self.blkList, 'blockID')
                self.ui.cmb_blockID.addItems(blkNames)
                self.last=mesg['command']
                self.signal.emit()
                pass
            elif mesg['command'] == 'CELLLIST':
                self.cellList=deepcopy(mesg['cells'])
                self.xmax=max(self.cellList, key=lambda f: f['cellX'])['cellX']
                self.ymax=max(self.cellList, key=lambda f: f['cellY'])['cellY']
                self.ui.tbl_storage.setRowCount(self.xmax)
                self.ui.tbl_storage.setColumnCount(self.ymax)
                '''
                tutto cio' che riguarda la visualizzazione dovrebbe essere gestito 
                nella funzione chiamata quando si emette il segnale per evitare problemi
                nel thread chiamante
                '''
                self.last=mesg['command']
                self.signal.emit()
                pass
            elif mesg['command'] == 'RCPLIST':
                self.rcpList=mesg['recipes']
                self.ui.cmb_recipeID.clear()
                self.ui.cmb_recipeID2.clear()
                rcpList=self.dict2list(self.rcpList, 'recipeID')
                self.ui.cmb_recipeID.addItems(rcpList)
                self.ui.cmb_recipeID2.addItems(rcpList)
                self.last=mesg['command']
                pass
            elif mesg['command'] == 'ORDLIST':
                self.ordList=mesg['orders']
                self.ui.cmb_orderID.clear()
                ordList=self.dict2list(self.ordList, 'orderID')
                self.ui.cmb_orderID.addItems(ordList)
                self.last=mesg['command']
                pass
            elif mesg['command'] == 'UPDATE':
                self.signal.emit()
                pass
            elif mesg['command'] == 'DBMSG':
                self.ui.statusbar.showMessage(mesg['msg'])
                pass
            else:
                self.common.log.error('Unrecognized, ignoring...')
                pass
            pass
        pass
    
    
    def on_addMaterial(self):
        mat=deepcopy(self.d['material'])  
        mesg=deepcopy(self.mesg)   
        mat['materialID']=str(self.ui.txt_matID.text()).strip()
        mat['lift']=int(self.ui.txt_lift.text())
        mat['density']=int(self.ui.txt_density.text())
        mat['color']=str(self.ui.txt_color.text()).strip()
        mat['restTime']=str(self.ui.tim_restTime.time().toString("HH:mm"))        
        mesg['command']='ADDMAT'
        mesg['prop']=mat      
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass
    
    def on_delMaterial(self):
        mesg=deepcopy(self.mesg)
        mesg['command']='DELMAT'
        mesg['prop']={
            'matID':self.ui.cmb_matID2.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass 
    
    def on_addBlock(self):
        blk=deepcopy(self.d['block'])
        mesg=deepcopy(self.mesg)
        blk['materialID']=str(self.ui.cmb_matID.currentText())
        blk['blockID']=str(self.ui.txt_blockID.text())
        blk['blockWidth']=int(self.ui.txt_dimX.text())
        blk['blockHeight']=int(self.ui.txt_dimY.text())
        blk['blockLength']=int(self.ui.txt_dimZ.text()) 
        blk['blockProductionDate']=time.strftime('%c')
        mesg['command']='ADDBLK'
        mesg['prop']=blk
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass   
    
    def on_delBlock(self):
        mesg=deepcopy(self.mesg)
        mesg['command']='DELBLK'
        mesg['prop']={
            'blockID':self.ui.cmb_blockID.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass
    
    def on_addRecipe(self):
        rcp=deepcopy(self.d['recipe'])
        mesg=deepcopy(self.mesg)
        rcp['recipeID']=str(self.ui.txt_rcpID.text())
        rcp['materialID']=str(self.ui.cmb_matID2.currentText())
        rcp['nVertCut']=int(self.ui.txt_nCutVert.text())
        rcp['nOrCut']=int(self.ui.txt_nCutOriz.text())
        rcp['spVertCut']=int(self.ui.txt_spCutVert.text())
        rcp['spOrCut']=int(self.ui.txt_spCutOriz.text())
        rcp['progSagom']=str(self.ui.cmb_cncProg.currentText())
        rcp['execOrder']=str(self.ui.txt_execOrder.text())
        mesg['command']='ADDRCP'
        mesg['prop']=rcp
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass
    
    def on_delRecipe(self):
        mesg=deepcopy(self.mesg)
        mesg['command']='DELRCP'
        mesg['prop']={
            'recipeID':self.ui.cmb_recipeID.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass
    
    def on_addOrder(self):
        ordd=deepcopy(self.d['order'])
        mesg=deepcopy(self.mesg)
        ordd['orderID']=str(self.ui.txt_orderID.text())
        ordd['customer']=str(self.ui.txt_customer.text())
        ordd['expDate']=str(self.ui.dat_deliveryDate.date().toString("yyyy MMM dd"))
        ordd['nPieces']=int(self.ui.spn_nPieces.value())
        ordd['recipeID']=str(self.ui.cmb_recipeID2.currentText())
        mesg['command']='ADDORD'
        mesg['prop']=ordd
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass
    
    def on_delOrder(self):
        mesg=deepcopy(self.mesg)
        mesg['command']='DELORD'
        mesg['prop']={
            'orderID':self.ui.cmb_orderID.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass
    
    def on_createStorage(self):
        mesg=deepcopy(self.mesg)
        mesg['command']='ADDCELL'
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
    
    def on_genID(self,t):
        uid=uuid.uuid4().hex
        t.setText(uid)
        return uid
        pass
    
    def getBlockID(self, x,y):    
        for i in self.cellList: 
            if i['cellX']==x and i['cellY']==y: 
                print
                return i['blockID']
    
    def upd(self):
        if self.last=='CELLLIST':
            for x in range(self.xmax):
                for y in range(self.ymax):
                    itm=visitem(self, blockID=self.getBlockID(x,y))
                    self.ui.tbl_storage.setCellWidget(x,y,itm)
                    pass
                pass
            self.ui.tbl_storage.resizeColumnsToContents()
            self.ui.tbl_storage.resizeRowsToContents()
            pass
        elif self.last=='BLKLIST':
            for x in range(self.xmax):
                for y in range(self.ymax):
                    itm=self.ui.tbl_storage.cellWidget(x,y)
                    for bb in self.blkList:
                        if bb['blockID']==itm.blockID:
                            itm.lbl_status.setText(bb['materialID']+'\n'+bb['blockID'])
            self.ui.tbl_storage.resizeColumnsToContents()
            self.ui.tbl_storage.resizeRowsToContents()
            pass
        else:
            self.common.log.error('Unrecognized, ignoring...')
        self.last=''
        pass
    
    def dict2list(self,d,k):
        out=[]
        for i in d:
            out.append(i[k])
        return deepcopy(out)
    
    
class visitem(QWidget):
    def __init__(self,parent, blockID):
        super(visitem, self).__init__(parent)
        self.setParent(parent)
        self.lyt=QVBoxLayout()
        self.lbl_status=QLabel()
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setText('')
        self.btn_show=QPushButton()
        self.btn_show.setText('ShowProp')
        self.lyt.addWidget(self.lbl_status)
        self.lyt.addWidget(self.btn_show)
        self.setLayout(self.lyt)
        self.blockID=blockID
    pass
    
        
        
    