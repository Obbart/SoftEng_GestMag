'''
Created on 28 feb 2018

@author: Emanuele

2018-03-12    Emanuele    First Version, classes setup
2018-03-14    Emanuele    Change Grammar to python3.6, problems in executing
2018-03-15    Emanuele    Solved execution problems, first MySql implementation
2018-03-21    Davide      Git Join :)
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


def launchMain():
    gmag_main=GestMag_Main(c['main'],c['mqtt'])
    log.debug("Starting {}".format(c['main']['modName']))
    gmag_main.start()
    threadList.append(gmag_main)
    time.sleep(0.1)
    pass

def launchDB():
    gmag_db=DB_Com(c['db'],c['mqtt'])
    log.debug("Starting {}".format(c['db']['modName']))
    gmag_db.start()
    threadList.append(gmag_db)
    time.sleep(0.1)
    pass

def launchCNC():
    gmag_cnc=CNC_Com(c['cnc'],c['mqtt'])
    log.debug("Starting {}".format(c['cnc']['modName']))
    gmag_cnc.start()
    threadList.append(gmag_cnc)
    time.sleep(0.1)
    pass

def launchPLC():
    gmag_plc=PLC_Com(c['plc'],c['mqtt'])
    log.debug("Starting {}".format(c['plc']['modName']))
    gmag_plc.start()
    threadList.append(gmag_plc)
    time.sleep(0.1)
    pass


def on_broadcast(client, userdata, msg):
    log.debug(str(msg.payload))
    pass

def send_broadcst(msg):
    
    pass


#######################################################
#################### MAIN_LOOP ########################
#######################################################
log=MyLogger("GestMag_INIT",logging.DEBUG).logger()
threadList=[]

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

isRunning=True
rc=0
try:                            #connect mqtt broker
    client=mqtt.Client(protocol=mqtt.MQTTv31)
    rc=client.connect(host=HOST,keepalive=KEEPALIVE)
    client.subscribe(recv_broadcast)
    client.message_callback_add(recv_broadcast,on_broadcast)
except:
    log.error("Error Connecting to Mqtt, rc={0}... aborting".format(rc))
    exit()

#launch other modules as separate threads
# possible to automate launch procedure? TODO list

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

while isRunning == True: 
    client.loop()
    time.sleep(1)

client.disconnect()

#######################################################
#################### MAIN_LOOP ########################
#######################################################

    

