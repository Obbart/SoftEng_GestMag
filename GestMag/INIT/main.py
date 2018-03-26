'''
Created on 28 feb 2018

@author: Emanuele

2018-03-12    Emanuele    First Version, classes setup
2018-03-14    Emanuele    Change Grammar to python3.6, problems in executing
2018-03-15    Emanuele    Solved execution problems, first MySql implementation
2018-03-22    Emanuele    Changes in Poll mechanism, inits sends poll and processes respond with timestamp
                            issues in restarting dead threads, respawn threads result as duplicate of original
                            thread that is still alive
                            UPDATE: thread respawn working correcly, it was only a problem of adding more
                                    than one handler to the logger inside the thread
'''

import json
import logging
import time

from MODULES.MyLog import MyLogger
from MAIN.GestMag_Main import GestMag_Main
from DB.DB_Com import DB_Com
from PLC.PLC_Com import PLC_Com
from CNC.CNC_Com import CNC_Com
import paho.mqtt.client as mqtt

log=MyLogger("GestMag_INIT",logging.INFO).logger()
threadList={}

def launchMain():
    gmag_main=GestMag_Main(c['main'],c['mqtt'])
    log.debug("Starting {}".format(c['main']['modName']))
    gmag_main.start()
    threadList['{}'.format(gmag_main.name)]={'th':gmag_main,'lastSeen':int(time.time()),'cl':GestMag_Main}
    time.sleep(0.1)
    pass

def launchDB():
    gmag_db=DB_Com(c['db'],c['mqtt'])
    log.debug("Starting {}".format(c['db']['modName']))
    gmag_db.start()
    threadList['{}'.format(gmag_db.name)]={'th':gmag_db,'lastSeen':int(time.time()),'cl':DB_Com}
    time.sleep(0.1)
    pass

def launchCNC():
    gmag_cnc=CNC_Com(c['cnc'],c['mqtt'])
    log.debug("Starting {}".format(c['cnc']['modName']))
    gmag_cnc.start()
    threadList['{}'.format(gmag_cnc.name)]={'th':gmag_cnc,'lastSeen':int(time.time()),'cl':CNC_Com}
    time.sleep(0.1)
    pass

def launchPLC():
    gmag_plc=PLC_Com(c['plc'],c['mqtt'])
    log.debug("Starting {}".format(c['plc']['modName']))
    gmag_plc.start()
    threadList['{}'.format(gmag_plc.name)]={'th':gmag_plc,'lastSeen':int(time.time()),'cl':PLC_Com}
    time.sleep(0.1)
    pass

def sendPoll():
    mesg={'from':c_ini['modName'],
          'to': 'ALL',
          'command':'POLL'
        }
    sendBroadcast(mesg)
    
def on_broadcast(client, userdata, msg):
    #convert incoming string to dictionary
    log.debug('received: {}'.format(msg.payload)) 
    msg=json.loads(msg.payload)
    
    if msg['command'] in 'POLL_RESP':
        threadList[msg['from']]['lastSeen']=msg['ts'] #if it is a poll response update last seen for the thread
    pass

def sendBroadcast(msg):
    #convert incoming dictionary to string
    log.debug('sent: {}'.format(json.dumps(msg)))
    client.publish(send_broadcast,json.dumps(msg))
    pass

def checkThreads():
    for t in threadList.keys():     #for every thread launched
        thisThread=threadList[t]    #grab the thread dictionary
        if int(time.time())-thisThread['lastSeen'] < c['mqtt']['pollPeriod']*2 :
            pass    #if was last seen after X seconds ago pass
        else:
            log.error('Thread {} is DEAD, restarting...'.format(t)) #else delete the thread, keep config
            currconf=thisThread['th'].co                            #and restart it
            time.sleep(0.1)
            del thisThread['th']
            thisThread['th']=thisThread['cl'](currconf,c['mqtt'])
            thisThread['th'].start()
            time.sleep(0.1)
            if thisThread['th'].isAlive():      #if after restart threa is not alive kill all and exit
                pass
            else:
                log.critical('Thread {} is DEAD and cannot be restarted, aborting'.format(t))
                isRunning=False
                break
    pass


#######################################################
#################### MAIN_LOOP ########################
#######################################################
try:                            #load configuration file
    fp=open("conf/gesmagconf.json") 
    c=json.load(fp)
    c_ini=c['init']
    log.info("Starting GestMag_INIT ver {0}".format(c['version']))
    fp.close()
except:
    log.error("Error Opening Config File... aborting")
    exit()
                                #init mqtt parameters
HOST=c['mqtt']['addr']
KEEPALIVE=c['mqtt']['keepalive']
recv_broadcast=c['mqtt']['all2ini']
send_broadcast=c['mqtt']['ini2all']

isRunning=True
rc=0
try:                            #connect mqtt broker
    client=mqtt.Client(protocol=mqtt.MQTTv31)
    rc=client.connect(host=HOST,keepalive=KEEPALIVE)
    client.subscribe(recv_broadcast)
    client.message_callback_add(recv_broadcast,on_broadcast)
    client.loop_start()
except:
    log.error("Error Connecting to Mqtt, rc={0}... aborting".format(rc))
    exit()

#launch other modules as separate threads
#possible to automate launch procedure? TODO list

if c_ini['start_main']==True:
    launchMain()
    pass
if c_ini['start_db']==True:
    launchDB()
    pass
if c_ini['start_cnc']==True:
    launchCNC()
    pass
if c_ini['start_plc']==True:
    launchPLC()
if c_ini['start_gui']==True:
    print('INIT_Gui not present yet')
    pass
pass

while isRunning == True: # init cares only to maintain threads alive
    sendPoll()
    time.sleep(c['mqtt']['pollPeriod'])
                
client.disconnect()

#######################################################
#################### MAIN_LOOP ########################
#######################################################

    

