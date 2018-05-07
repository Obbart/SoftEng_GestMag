'''
Created on 12 mar 2018

@author: Emanuele
'''
import time, json
from MODULES.GestMag_Threads import GestMag_Thread
from CNC.CNC_Sim import CNC_Sim, type_CNC, status_CNC

class CNC_Com(GestMag_Thread):

    def __init__(self, conf, mqttconf):
        super(CNC_Com, self).__init__(conf, mqttconf)
        self.subList = [mqttconf['main2cnc']]
        
        # load machine list from configuration file
        self.machineList = []
        for m in conf['machines']:
            self.machineList.append(CNC_Sim(m))
            pass
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if mesg['to'] == self.getName():
            if mesg['command'] == 'LOADCNC':
                prop=mesg['prop']
                for m in self.machineList:
                    if m.getName() == prop['name']:  # search the correct machine in the list and load programs
                        if prop['type']==type_CNC['sagomatore']:
                            m.setProgram(prop['job'])
                            pass
                        else: 
                            m.setCuts(prop['job'])
                            pass
                        pass
                        m.loadPiece(prop['blockID'])
                        break
                    pass
                pass
            elif mesg['command'] == 'UNLOADCNC':
                for m in self.machineList:
                    if m.getName() == mesg['name']:
                        m.unloadPiece()
                        break
                pass
            elif mesg['command'] == 'GETCNC':
                for m in self.machineList:
                    if m.getName() == mesg['name']:
                        data=m.getData()
                        self.publish(self.mqttconf['cnc2main'], data)
                pass
            else:
                pass
        pass
    
    #######################################################
    #################### MAIN_LOOP ########################
    #######################################################    
    def run(self):
        self.connectMqtt(self.subList)
        self.client.message_callback_add(self.subList[0], self.on_mainMessage)
        
        self.log.info("Thread STARTED")
        
        while self.isRunning:
            time.sleep(self.mqttConf["pollPeriod"])
            mesg={'from': self.getName(),
                  'to':'GestMag_MAIN',
                  'command':''}
            for m in self.machineList:      #periodically check if there is machine waiting to be unloaded
                if m.getStatus() == status_CNC['waiting_unloading_WIP']:
                    mesg['command']='MACHINEREADY'
                    mesg['name']=m.getName()
                    self.publish(self.mqttConf['cnc2main'], mesg)
                pass
        self.log.info("Thread STOPPED")
        return
    
    
    
    
    
