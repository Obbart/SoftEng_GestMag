'''
Created on 12 mar 2018

@author: Emanuele
'''
import time, json, uuid
from parse import parse
from copy import deepcopy
from GUI.GestMagUI import Ui_GestMag_WINDOW
from MODULES.GestMag_Threads import GestMag_Thread
from MODULES.Objects import CELL, BLOCK, MATERIAL, WIP
from CNC.CNC_Sim import type_CNC,status_CNC
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from random import randrange


class GestMag_GuInterface(QMainWindow):
    signal = pyqtSignal()
    
    def __init__(self, conf, mqttconf):
        # setup user interface
        QMainWindow.__init__(self)
        self.ui = Ui_GestMag_WINDOW()
        self.ui.setupUi(self)
        self.setWindowTitle('GestMag User Interface')
        self.ui.dat_deliveryDate.setDate(QDate.currentDate())
        
        # instantiate common functions
        self.common = GestMag_Thread(conf, mqttconf)
        self.common.connectMqtt([mqttconf['main2gui'],
                                 mqttconf['plc2gui']])
        self.common.client.message_callback_add(mqttconf['main2gui'], self.on_mainMessage)
        self.common.client.message_callback_add(mqttconf['plc2gui'], self.on_plcMessage)
        
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
        self.ui.btn_cncLoad.clicked.connect(lambda: self.on_cncLoadUnload(True))
        self.ui.btn_cncUnload.clicked.connect(lambda: self.on_cncLoadUnload(False))
        self.ui.btn_move.clicked.connect(self.on_storageMove)
        #initialize other interface elements
        
        # interface update parameters and functions
        self.matList = []
        self.blkList = []
        self.wipList = []
        self.cellList = []
        self.rcpList = []
        self.machineList = []
        self.xmax = 0
        self.ymax = 0
        self.last = ''
        self.signal.connect(self.upd)
        self.initCompleted = False
        
        
        # load defaults dictionaries
        try:
            fp = open('../INIT/conf/defaults.json', 'r')
            self.d = json.load(fp)
            fp.close()
        except Exception: 
            self.log.error("unable to open defaults file: {}, aborting")
            exit()
        
        self.mesg = deepcopy(self.d['msg'])
        self.mesg['from'] = self.common.getName()
        self.mesg['to'] = 'GestMag_MAIN'
        pass
    
    def on_plcMessage(self, client, userdata, msg):
        self.common.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.common.getName():
            if mesg['command'] == 'PLCSTAT':
                buffin=mesg['stat']['bufferin']
#                 buffout=mesg['stat']['bufferout']
                crane=mesg['stat']['crane']
                
                self.ui.lbl_binBid.setText(buffin['blockID'])
                self.ui.lbl_binDate.setText(buffin['date'])
                self.ui.lbl_binMat.setText(buffin['material'])
                self.ui.lbl_binStat.setText(buffin['status'])
                
#                 self.ui.lbl_boutBid.setText(buffout['blockID'])
#                 self.ui.lbl_boutMat.setText(buffout['material'])
#                 self.ui.lbl_boutStat.setText(buffout['status'])
                
                self.ui.lbl_craneBid.setText(crane['blockID'])
                self.ui.lbl_craneStat.setText(crane['status'])
                self.ui.lbl_craneSrc.setText(str(crane['source']))
                self.ui.lbl_craneDest.setText(str(crane['dest']))
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        self.common.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.common.getName():
            self.last = mesg['command']
            if mesg['command'] == 'MATLIST':  # after adding a material update combo box with list of all materials
                self.matList = mesg['materials']
                self.ui.cmb_matID.clear()  # update the whole combo clearing previous content
                self.ui.cmb_matID2.clear()
                self.ui.cmb_matID3.clear()
                matNames = self.dict2list(self.matList, 'materialID')
                self.ui.cmb_matID.addItems(matNames)
                self.ui.cmb_matID2.addItems(matNames)
                self.ui.cmb_matID3.addItems(matNames)
                self.matList = self.common.createInstance(deepcopy(self.matList), MATERIAL)
                pass
            elif mesg['command'] == 'BLKLIST':
                self.blkList = mesg['blocks']
                self.ui.cmb_blockID.clear()
                blkNames = self.dict2list(self.blkList, 'blockID')
                self.ui.cmb_blockID.addItems(blkNames)
                self.blkList = self.common.createInstance(deepcopy(self.blkList), BLOCK)
                self.blkList = self.common.associateMaterial(self.blkList, self.matList)
                self.common.log.info('Blocks Updated')
                self.signal.emit()
                pass
            elif mesg['command'] == 'WIPLIST':
                self.wipList = mesg['wips']
                self.wipList = self.common.createInstance(deepcopy(self.wipList), WIP)
                self.wipList = self.common.associateMaterial(self.wipList, self.matList)
                self.common.log.info('Wips Updated')
            elif mesg['command'] == 'CELLLIST':
                self.cellList = mesg['cells']
                self.xmax = max(self.cellList, key=lambda f: f['cellX'])['cellX']+1
                self.ymax = max(self.cellList, key=lambda f: f['cellY'])['cellY']+1
                self.ui.tbl_storage.setRowCount(self.ymax)
                self.ui.tbl_storage.setColumnCount(self.xmax)
                self.ui.spn_destX.setMaximum(self.xmax)
                self.ui.spn_destY.setMaximum(self.ymax)
                self.ui.spn_srcX.setMaximum(self.xmax)
                self.ui.spn_srcY.setMaximum(self.ymax)
                self.cellList = self.common.createInstance(deepcopy(self.cellList), CELL)
                self.common.log.info('Cells Updated - x:{},y:{}'.format(self.xmax, self.ymax))
                self.signal.emit()
                pass
            elif mesg['command'] == 'RCPLIST':
                self.rcpList = mesg['recipes']
                self.ui.cmb_recipeID.clear()
                self.ui.cmb_recipeID2.clear()
                rcpList = self.dict2list(self.rcpList, 'recipeID')
                self.ui.cmb_recipeID.addItems(rcpList)
                self.ui.cmb_recipeID2.addItems(rcpList)
                pass
            elif mesg['command'] == 'ORDLIST':
                self.ordList = mesg['orders']
                self.ui.cmb_orderID.clear()
                ordList = self.dict2list(self.ordList, 'orderID')
                self.ui.cmb_orderID.addItems(ordList)
                pass
            elif mesg['command'] == 'UPDMAC':
                self.machineList = mesg['machines']
                self.signal.emit()
                pass
            elif mesg['command'] == 'UPDVIS':
                self.common.log.info('Updating Visualization')
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
        mat = deepcopy(self.d['material'])  
        mesg = deepcopy(self.mesg)   
        mat['materialID'] = str(self.ui.txt_matID.text()).strip()
        mat['lift'] = int(self.ui.txt_lift.text())
        mat['density'] = int(self.ui.txt_density.text())
        mat['color'] = str(self.ui.txt_color.text()).strip()
        mat['restTime'] = str(self.ui.tim_restTime.time().toString("HH:mm")) 
        mat['cutSpeed'] = randrange(200, 500, 100)       
        mesg['command'] = 'ADDMAT'
        mesg['prop'] = mat      
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass
    
    def on_delMaterial(self):
        mesg = deepcopy(self.mesg)
        mesg['command'] = 'DELMAT'
        mesg['prop'] = {
            'matID':self.ui.cmb_matID2.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass 
    
    def on_addBlock(self):
        blk = deepcopy(self.d['block'])
        mesg = deepcopy(self.mesg)
        blk['materialID'] = str(self.ui.cmb_matID.currentText())
        blk['blockID'] = str(self.ui.txt_blockID.text())
        blk['blockWidth'] = int(self.ui.txt_dimX.text())
        blk['blockHeight'] = int(self.ui.txt_dimY.text())
        blk['blockLength'] = int(self.ui.txt_dimZ.text()) 
        blk['blockProductionDate'] = time.strftime('%c')
        mesg['command'] = 'ADDBLK'
        mesg['prop'] = blk
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass   
    
    def on_delBlock(self):
        mesg = deepcopy(self.mesg)
        mesg['command'] = 'DELBLK'
        mesg['prop'] = {
            'blockID':self.ui.cmb_blockID.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass
    
    def on_addRecipe(self):
        rcp = deepcopy(self.d['recipe'])
        mesg = deepcopy(self.mesg)
        rcp['recipeID'] = str(self.ui.txt_rcpID.text())
        rcp['materialID'] = str(self.ui.cmb_matID2.currentText())
        rcp['nVertCut'] = int(self.ui.txt_nCutVert.text())
        rcp['nOrCut'] = int(self.ui.txt_nCutOriz.text())
        rcp['spVertCut'] = int(self.ui.txt_spCutVert.text())
        rcp['spOrCut'] = int(self.ui.txt_spCutOriz.text())
        rcp['progSagom'] = str(self.ui.cmb_cncProg.currentText())
        if rcp['progSagom'] is not '-':
            rcp['progTime'] = randrange(10, 30, 5)
        else:
            rcp['progTime'] = 0
        rcp['execOrder'] = str(self.ui.txt_execOrder.text()).upper()
        mesg['command'] = 'ADDRCP'
        mesg['prop'] = rcp
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass
    
    def on_delRecipe(self):
        mesg = deepcopy(self.mesg)
        mesg['command'] = 'DELRCP'
        mesg['prop'] = {
            'recipeID':self.ui.cmb_recipeID.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass
    
    def on_addOrder(self):
        ordd = deepcopy(self.d['order'])
        mesg = deepcopy(self.mesg)
        ordd['orderID'] = str(self.ui.txt_orderID.text())
        ordd['customer'] = str(self.ui.txt_customer.text())
        #ordd['expDate'] = str(self.ui.dat_deliveryDate.date().toString("yyyy MMM dd"))
        ordd['expDate'] = str(time.asctime(time.gmtime(self.ui.dat_deliveryDate.dateTime().toSecsSinceEpoch())))
        ordd['recipeID'] = str(self.ui.cmb_recipeID2.currentText())
        mesg['command'] = 'ADDORD'
        mesg['prop'] = ordd
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass
    
    def on_delOrder(self):
        mesg = deepcopy(self.mesg)
        mesg['command'] = 'DELORD'
        mesg['prop'] = {
            'orderID':self.ui.cmb_orderID.currentText()}
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass
    
    def on_createStorage(self):
        mesg = deepcopy(self.mesg)
        mesg['command'] = 'ADDCELL'
        self.common.publish(self.common.mqttConf['gui2main'], mesg)
    
    def on_genID(self, t):
        uid = uuid.uuid4().hex
        t.setText(uid)
        return uid
        pass
    
    def on_cncLoadUnload(self, cnc, load):
        pass
    
    def on_storageMove(self):
        mesg=deepcopy(self.mesg)
        mesg['command']='MOVE'
        mesg['from']=self.common.getName()
        mesg['to']='GestMag_PLC'
        if self.ui.rad_move.isChecked():
            if self.ui.cmb_blockID3.currentText() == '-':
                src=(int(self.ui.spn_srcX.value(),int(self.ui.spn_srcY.value())))
            else:
                #src=(tuple(self.ui.cmb_blockID3.currentText().split('-')[1].split(',').strip('()')))
                src=(tuple(parse("({:d},{:d})",self.ui.cmb_blockID3.currentText().split('-')[1].strip())))
            dst=(int(self.ui.spn_destX.value()),int(self.ui.spn_destY.value()))
        elif self.ui.rad_load.isChecked():
            src=(self.common.conf['plc']['buffer']['addr'],0)
            dst=(int(self.ui.spn_destX.value(),int(self.ui.spn_destY.value())))
        elif self.ui.rad_unload.isChecked():
            src=(int(self.ui.spn_srcX.value(),int(self.ui.spn_srcY.value())))
            dst=(self.common.conf['plc']['buffer']['addr'],0)
        else:
            pass
        if self.getCell(src[0], src[1]).blockID is not None and self.getCell(dst[0], dst[1]).isEmpty():
            mesg['prop']={'source':src,
                          'dest':dst,
                          'blockID':self.getCell(src[0], src[1]).blockID}
            self.common.log.info(mesg)
            self.common.publish(self.common.mqttConf['gui2main'], mesg)
        pass
    
    def getCell(self, x, y):    
        for c in self.cellList: 
            if c.addr[0] == x and c.addr[1] == y: 
                return c
    
    def upd(self):
        if self.last == 'CELLLIST' and not self.initCompleted:
            self.common.log.info('Creating {} cells'.format(self.xmax * self.ymax))
            for x in range(self.xmax):
                for y in range(self.ymax):
                    itm = visitem(self, _cell=self.getCell(x, y))
                    self.ui.tbl_storage.setCellWidget(y, x, itm)
                    pass
                pass
            self.ui.tbl_storage.resizeColumnsToContents()
            self.ui.tbl_storage.resizeRowsToContents()
            self.initCompleted = True
            pass
        elif self.last == 'UPDVIS':
            self.common.log.info('Block & Wip Update')
            self.ui.cmb_blockID2.clear()
            self.ui.cmb_blockID3.clear()
            for x in range(self.xmax):
                for y in range(1,self.ymax):
                    # le celle della visualizzazione hanno x e y invertite!
                    itm = self.ui.tbl_storage.cellWidget(y, x)
                    itm.setCell(self.getCell(x, y))
                    found=False
                    for bb in self.blkList:
                        if bb.blockID == itm.cell.blockID:
                            itm.setBlock(bb)
                            self.ui.cmb_blockID2.addItem('{} - {}'.format(bb.materialID,(x,y)))
                            self.ui.cmb_blockID3.addItem('{} - {}'.format(bb.materialID,(x,y)))
                            found=True
                    for ww in self.wipList:
                        if ww.wipID == itm.cell.blockID:
                            itm.setWip(ww)
                            found=True
                    if not found:
                        itm.emptyCell()
        elif self.last == 'UPDMAC':
            self.common.log.info('Machines Update')
            for x in range(self.xmax):
                itm = self.ui.tbl_storage.cellWidget(0, x)
                for mm in self.machineList:
                    if mm['addr'][0] == x:
                        itm.setMachine(mm)
                        pass
                    pass
                pass
            pass   
        else:
            pass
        self.last = ''
        
        self.ui.tbl_storage.resizeColumnsToContents()
        self.ui.tbl_storage.resizeRowsToContents()
        pass
    
    def dict2list(self, d, k):
        out = []
        for i in d:
            out.append(i[k])
        return deepcopy(out)
    
    
class visitem(QWidget):
    def __init__(self, parent, _cell):
        super(visitem, self).__init__(parent)
        self.setParent(parent)
        self.lyt = QVBoxLayout()
        self.lbl_block = QLabel()
        self.lbl_block.setAlignment(Qt.AlignCenter)
        self.lbl_block.setText('-')
        self.lbl_stat = QLabel()
        self.lbl_stat.setAlignment(Qt.AlignCenter)
        self.lbl_stat.setText('-')
        self.lyt.addWidget(self.lbl_block)
        self.lyt.addWidget(self.lbl_stat)
        self.setLayout(self.lyt)
        self.cell = _cell
        
    def setCell(self, c):
        self.cell = c
        pass
    
    def emptyCell(self):
        self.lbl_block.setText('-')
        self.lbl_stat.setText('-')
        self.setColor(Qt.transparent)
    
    def setMachine(self, m):
        self.lbl_block.setText(m['name'])
        self.lbl_stat.setText(self.getKey(status_CNC, m['status']))
        if m['status'] == status_CNC['free']:
            self.setColor(Qt.green)
            pass
        elif m['status'] == status_CNC['busy']:
            self.setColor(Qt.cyan)
            pass
        else:
            self.setColor(Qt.yellow)
            pass
        pass
        
    def setBlock(self, b):
        self.lbl_block.setText(b.material.materialID + '\n' + b.date)
        if b.checkReady():
            self.lbl_stat.setText('READY')
            self.setColor(Qt.green)
        else:
            self.lbl_stat.setText('WAIT')
            self.setColor(Qt.yellow)
            
    def setWip(self, w):
        self.lbl_block.setText(w.material.matID + '\n' + w.recipeID)
        self.lbl_stat.setText('CurrentStep: {}'.format(w.recipeStep))
        self.setColor(Qt.cyan)
            
    def setColor(self, c):
        p = self.lbl_stat.palette()
        self.lbl_stat.setAutoFillBackground(True)
        p.setColor(self.lbl_stat.backgroundRole(), c)
        self.lbl_stat.setPalette(p)
        
    def getKey(self, mydict, val):
        return list(mydict.keys())[list(mydict.values()).index(val)]
        
        
    
