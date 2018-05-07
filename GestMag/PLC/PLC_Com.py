'''
Created on 12 mar 2018

@author: Emanuele
'''

from copy import deepcopy
import queue, time, json, queue

from MODULES.GestMag_Threads import GestMag_Thread
from PLC.PLC_Sim import BUFFER, CRANE


class PLC_Com(GestMag_Thread):

    def __init__(self, conf, mqttconf):
        super(PLC_Com, self).__init__(conf, mqttconf)
        self.subList = [mqttconf['main2plc']]
        self.buffer = BUFFER(addr=conf['buffer']['addr'])
        
        self.bufferqueue = queue.Queue(maxsize=1)
        self.crane = CRANE(s=1)  # velocita' in celle al secondo
        self.matList = []
        self.progList = []
        
        self.eventQueue = queue.Queue()
        pass
    
    def on_mainMessage(self, client, userdata, msg):
        self.log.debug('received: {}'.format(msg.payload))
        mesg = json.loads(msg.payload)
        if   mesg['command'] == 'MATLIST':
            self.matList = self.dict2list(deepcopy(mesg['materials']), 'materialID')
            pass
        elif mesg['command'] == 'RCPLIST': 
            self.progList = self.dict2list(deepcopy(mesg['recipes']), 'prg')
            self.log.info('\n'.join(self.progList))
            pass
        elif mesg['command'] == 'MOVE':
            self.eventQueue.put(mesg)
            mesgr = {'from':self.getName(),
                  'to':'GestMag_MAIN',
                  'command':'MOVE_WAIT'
                }
            self.publish(self.mqttConf['plc2main'], mesgr)
            pass
        elif mesg['command'] == 'GETSTATUS':
            mesg = {'from':self.getName(),
                  'to':'GestMag_MAIN',
                  'command':'GETCRANE_RESP',
                  'prop': {'cranepos':self.crane.act_Pos,
                           'blockID':self.buffer.blockID_loaded,
                           'status':self.crane.status
                           }
                }
            self.publish(self.mqttConf['plc2main'], mesg)
            pass
        
    def newBlock (self, b):
        mesg = {'from':self.getName(),
               'to':'GestMag_MAIN',
               'command':'ADDBLK',
               'prop':''
               }
        mesg['prop'] = b.getData()
        self.log.info(mesg)
        self.publish(self.mqttConf['plc2main'], mesg)
        pass
    
    def moveBlock(self, prop):
        s = prop['source']
        d = prop['dest']
        self.crane.setDest(s);
        time.sleep(self.crane.calcTime(s))
        self.crane.setActPos(s)
        time.sleep(1)
        self.crane.loadPiece(self.buffer.blockID_loaded)
        time.sleep(1)
        self.buffer.unloadPiece()
        time.sleep(1)
        self.crane.setDest(d)
        time.sleep(self.crane.calcTime(d))
        self.crane.setActPos(d)
        time.sleep(1)
        return True
    
    #######################################################
    #################### MAIN_LOOP ########################
    #######################################################
    def run(self):
        self.connectMqtt(self.subList)  
        self.client.message_callback_add(self.subList[0], self.on_mainMessage)
         
        self.log.info("Thread STARTED")
        last = time.time()
        genTimeout = 30
        lastEvent = ''
        
        while self.isRunning:
            if not self.eventQueue.qsize() == 0:
                lastEvent = self.eventQueue.get(block=False)
                self.log.info(lastEvent)
                if lastEvent['command'] == 'MOVE':
                    self.moveBlock(lastEvent['prop'])
                    lastEvent['from'] = self.getName()
                    lastEvent['to'] = 'GestMag_MAIN'
                    lastEvent['command'] = 'MOVE_OK'
                    self.publish(self.mqttConf['plc2main'], lastEvent)
                    pass
                else:
                    pass
                pass
                    
            if time.time() - last > genTimeout:
                last = time.time()
                self.bufferqueue.put(self.buffer.simNewBlock(self.matList))
                pass
            
            if self.bufferqueue.full() :
                self.newBlock(self.bufferqueue.get())
                pass
                
            time.sleep(0.5)
        
        self.log.info("Thread STOPPED") 
        pass
    
    def dict2list(self, d, k):
        out = []
        for i in d:
            out.append(i[k])
        self.log.info(str(out))
        return deepcopy(out)
    
    
