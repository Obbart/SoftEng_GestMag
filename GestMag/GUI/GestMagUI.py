# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GestMagUI.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GestMag_GUI(object):
    def setupUi(self, GestMag_GUI):
        GestMag_GUI.setObjectName("GestMag_GUI")
        GestMag_GUI.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(GestMag_GUI)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tab_mainWindow = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_mainWindow.setObjectName("tab_mainWindow")
        self.tab_view = QtWidgets.QWidget()
        self.tab_view.setObjectName("tab_view")
        self.tab_mainWindow.addTab(self.tab_view, "")
        self.tab_control = QtWidgets.QWidget()
        self.tab_control.setObjectName("tab_control")
        self.tab_mainWindow.addTab(self.tab_control, "")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tab_mainWindow.addTab(self.tab, "")
        self.horizontalLayout.addWidget(self.tab_mainWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout.addWidget(self.checkBox)
        self.radioButton = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButton.setObjectName("radioButton")
        self.verticalLayout.addWidget(self.radioButton)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        self.horizontalLayout.addLayout(self.verticalLayout)
        GestMag_GUI.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(GestMag_GUI)
        self.statusbar.setObjectName("statusbar")
        GestMag_GUI.setStatusBar(self.statusbar)

        self.retranslateUi(GestMag_GUI)
        self.tab_mainWindow.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(GestMag_GUI)

    def retranslateUi(self, GestMag_GUI):
        _translate = QtCore.QCoreApplication.translate
        GestMag_GUI.setWindowTitle(_translate("GestMag_GUI", "MainWindow"))
        self.tab_mainWindow.setTabText(self.tab_mainWindow.indexOf(self.tab_view), _translate("GestMag_GUI", "Storage"))
        self.tab_mainWindow.setTabText(self.tab_mainWindow.indexOf(self.tab_control), _translate("GestMag_GUI", "Control"))
        self.tab_mainWindow.setTabText(self.tab_mainWindow.indexOf(self.tab), _translate("GestMag_GUI", "Manual"))
        self.checkBox.setText(_translate("GestMag_GUI", "CheckBox"))
        self.radioButton.setText(_translate("GestMag_GUI", "RadioButton"))
        self.pushButton.setText(_translate("GestMag_GUI", "PushButton"))

