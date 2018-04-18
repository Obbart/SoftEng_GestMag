'''
Created on 12 mar 2018

@author: Emanuele
'''
import time, json, uuid
from copy import deepcopy
from GUI.GestMagUI import Ui_GestMag_WINDOW
from MODULES.GestMag_Threads import GestMag_Thread
from PyQt5.QtWidgets import *
import PyQt5
from PyQt5.QtCore import pyqtSignal
from PyQt5 import Qt


class GestMag_GuInterface(QMainWindow):
    signal=pyqtSignal()
    
    def __init__(self, conf, mqttconf):
        # setup user interface
        QMainWindow.__init__(self)
        self.ui=Ui_GestMag_WINDOW()
        self.ui.setupUi(self)
        self.setWindowTitle('GestMag User Interface')
        
        #instantiate common functions
        self.common=GestMag_Thread(conf, mqttconf)
        self.common.connectMqtt([mqttconf['main2gui']])
        self.common.client.message_callback_add(mqttconf['main2gui'], self.on_mainMessage)
        
        # connect button and actions
        self.ui.btn_genID.clicked.connect(self.on_genID)
        self.ui.btn_addBlock.clicked.connect(self.on_addBlock)
        self.ui.btn_addMaterial.clicked.connect(self.on_addMaterial)
        self.ui.btn_createStorage.clicked.connect(self.on_createStorage)
        
        #interface update parameters and functions
        self.blkList=[]
        self.cellList=[]
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
        
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        self.common.log.debug('received: {}'.format(msg.payload))
        mesg=json.loads(msg.payload)
        if mesg['to'] == self.common.getName():
            if mesg['command'] == 'MATLIST': #after adding a material update combo box with list of all materials
                matList=mesg['materials']
                self.ui.cmb_matID.clear()   #update the whole combo clearing previous content
                matNames=[]
                for m in matList:
                    matNames.append(m['materialID'])
                self.ui.cmb_matID.addItems(matNames)
                pass
            elif mesg['command'] == 'BLKLIST':
                self.blkList=deepcopy(mesg['blocks'])
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
        mesg=deepcopy(self.d['msg'])        
        mat['matID']=str(self.ui.txt_matID.text()).strip()
        mat['lift']=int(self.ui.txt_lift.text())
        mat['density']=int(self.ui.txt_density.text())
        mat['color']=str(self.ui.txt_color.text()).strip()
        mat['restTime']=str(self.ui.tim_restTime.time().toString("HH:mm"))        
        mesg['from']=self.common.name
        mesg['to']='GestMag_DB'
        mesg['command']='ADDMAT'
        mesg['prop']=mat      
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass
     
    def on_addBlock(self):
        blk=deepcopy(self.d['block'])
        mesg=deepcopy(self.d['msg'])
        blk['matID']=str(self.ui.cmb_matID.currentText())
        blk['blockID']=str(self.ui.txt_blockID.text())
        blk['width']=int(self.ui.txt_dimX.text())
        blk['height']=int(self.ui.txt_dimY.text())
        blk['length']=int(self.ui.txt_dimZ.text()) 
        blk['date']=time.strftime('%c')
        mesg['from']=self.common.getName()
        mesg['to']='GestMag_DB'
        mesg['command']='ADDBLK'
        mesg['prop']=blk
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
        pass   
    
    def on_createStorage(self):
        mesg=deepcopy(self.d['msg'])
        mesg['from']=self.common.getName()
        mesg['to']='GestMag_MAIN'
        mesg['command']='ADDCELLS'
        self.common.publish(self.common.mqttConf['gui2main'],mesg)
    
    def on_genID(self):
        uid=uuid.uuid4().hex
        self.ui.txt_blockID.setText(uid)
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
                            itm.lbl_status.setText(bb['blockMaterial']+'\n'+bb['blockID'])
            pass
        else:
            self.common.log.error('Unrecognized, ignoring...')
        self.last=''
        pass
    
    
class visitem(PyQt5.QtWidgets.QWidget):
    def __init__(self,parent, blockID):
        super(visitem, self).__init__(parent)
        self.setParent(parent)
        self.lyt=QVBoxLayout()
        self.lbl_status=QLabel()
        self.lbl_status.setAlignment(PyQt5.QtCore.Qt.AlignCenter)
        self.lbl_status.setText('')
        self.btn_show=QPushButton()
        self.btn_show.setText('ShowProp')
        self.lyt.addWidget(self.lbl_status)
        self.lyt.addWidget(self.btn_show)
        self.setLayout(self.lyt)
        self.blockID=blockID
    pass
    
        
        
    