'''
Created on 12 mar 2018

@author: Emanuele
'''
import sys
import time

from PyQt5 import QtCore, QtGui

import paho.mqtt.client as mqtt


class GestMag_Gui(QtGui.QWindow):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        
        
if __name__ == '__main__':
    app = QtGui.QWindow(sys.argv)
    window = GestMag_Gui()
    window.show()
    sys.exit(app.exec_())
    pass